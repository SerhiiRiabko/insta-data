"""
Product-name translation service (Phase 4.6).

Products are scraped in Montenegrin/Serbian (Latin script, mixed with brand
names). This service resolves a display name per UI locale:

- `name_i18n` on a product doc, if already translated/cached there, wins.
- Otherwise, try `grocery_dictionary.translate_via_dictionary()` — a free,
  deterministic, word-by-word translator covering the actual grocery
  vocabulary in this dataset. It translates only the generic/descriptive
  words it recognises and leaves everything else (brand names, model
  numbers, percentages) untouched, so it needs no API key and never
  mistranslates a brand.
- Otherwise, if `settings.groq_api_key` is set, translate on demand via the
  Groq chat-completions API (OpenAI-compatible) and let the caller persist
  the result into `name_i18n` for next time.
- Otherwise, fall back to the original scraped name untouched — this is a
  deliberate, documented fallback (see PHASE_4_PLAN.md Phase 4.6), not an
  error: nothing here should ever block a product-listing response.

Brand/manufacturer names are kept untranslated in all locales per explicit
product requirement — the dictionary translator does this by only touching
recognised generic words; `extract_brand()` additionally splits a
known/likely brand token off the front of the name so the AI-fallback
prompt can instruct the model to leave it alone too.
"""

import logging
import re
from typing import Optional

import httpx

from app.core.config import settings
from app.services.grocery_dictionary import translate_via_dictionary

logger = logging.getLogger(__name__)

SUPPORTED_LOCALES = ["ukr", "rus", "mne", "srb", "bos", "eng"]

LOCALE_NAMES = {
    "ukr": "Ukrainian",
    "rus": "Russian",
    "mne": "Montenegrin",
    "srb": "Serbian",
    "bos": "Bosnian",
    "eng": "English",
}

# Known brand tokens (Latin + Cyrillic spellings) - extends the matching set
# already used for product grouping in product_matcher.py::BRAND_PATTERNS.
KNOWN_BRANDS = {
    "kiš": "Kiš", "kis": "Kiš",
    "danone": "Danone",
    "aroma": "Aroma",
    "zdravo": "Zdravo",
    "podgorica": "Podgorica",
    "voli": "Voli",
    "hdl": "HDL",
    "idea": "IDEA",
}

# mne/srb/bos are close enough to the scraped source language that, absent a
# real AI translation, showing the source name is more accurate than a wrong
# machine translation would be - only ukr/rus/eng actually need translating.
LOCALES_NEEDING_TRANSLATION = {"ukr", "rus", "eng"}


def extract_brand(name: str) -> tuple[Optional[str], str]:
    """Splits a leading/trailing known brand token off `name`.

    Returns (brand_or_None, rest_of_name). `rest_of_name` is `name` unchanged
    if no known brand is found - callers should translate the whole string
    in that case.
    """
    tokens = name.split()
    for i, tok in enumerate(tokens):
        key = re.sub(r"[^\wа-яїєіґ]", "", tok, flags=re.IGNORECASE).lower()
        if key in KNOWN_BRANDS:
            brand = KNOWN_BRANDS[key]
            rest = " ".join(tokens[:i] + tokens[i + 1 :]).strip()
            return brand, rest or name
    return None, name


async def translate_name(name: str, target_locale: str) -> Optional[str]:
    """Translates one product name into `target_locale`.

    Tries the free, deterministic grocery-word dictionary first; only calls
    the Groq AI fallback if the dictionary didn't recognise a single word in
    `name` and an API key is configured. Returns None (never raises) if
    neither produced anything - callers must treat None as "no translation
    available yet, use the source name".
    """
    if target_locale not in LOCALES_NEEDING_TRANSLATION:
        return None

    dictionary_result = translate_via_dictionary(name, target_locale)
    if dictionary_result:
        return dictionary_result

    return await _translate_name_ai(name, target_locale)


async def _translate_name_ai(name: str, target_locale: str) -> Optional[str]:
    """AI fallback via Groq - only reached when the dictionary couldn't
    translate a single word of `name`. Returns None if no API key is
    configured or the request fails."""
    if not settings.groq_api_key:
        return None

    brand, rest = extract_brand(name)
    brand_instruction = (
        f' Keep the brand name "{brand}" exactly as written, do not translate it.'
        if brand
        else ""
    )
    target_lang_name = LOCALE_NAMES[target_locale]

    prompt = (
        f"Translate this grocery product name from Montenegrin to {target_lang_name}. "
        f"Reply with ONLY the translated product name, no explanation, no quotes."
        f"{brand_instruction}\n\nProduct name: {name}"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 60,
                },
            )
            response.raise_for_status()
            data = response.json()
            translated = data["choices"][0]["message"]["content"].strip().strip('"')
            return translated or None
    except Exception as e:
        logger.warning(f"translate_name failed for '{name}' -> {target_locale}: {e}")
        return None


async def translate_to_all_locales(name: str) -> dict:
    """Translates `name` into every locale that needs it. Best-effort - any
    locale that fails to translate is simply omitted from the result dict."""
    result = {}
    for locale in LOCALES_NEEDING_TRANSLATION:
        translated = await translate_name(name, locale)
        if translated:
            result[locale] = translated
    return result


def resolve_display_name(doc: dict, locale: str) -> str:
    """Resolves the name to show for `doc` in `locale`: cached translation if
    present, else the original source name. Never returns None/empty."""
    name_i18n = doc.get("name_i18n") or {}
    return name_i18n.get(locale) or doc.get("name", "")
