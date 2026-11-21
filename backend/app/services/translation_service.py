"""
Product-name translation service (Phase 4.6, multi-country since 2026-11).

Montenegro's products are scraped in Montenegrin/Serbian (Latin script,
mixed with brand names), Ukraine's in Ukrainian - see
SOURCE_LOCALE_BY_COUNTRY / TRANSLATION_TARGETS. Whole catalogs are
translated in batches by translate_batch() (Groq, then Claude Haiku for the
rest), driven by app/services/translation_jobs.py. Per-name resolution:

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

import json
import logging
import re
from typing import Optional

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.services.grocery_dictionary import translate_via_dictionary

logger = logging.getLogger(__name__)

SUPPORTED_LOCALES = ["ukr", "rus", "mne", "srb", "bos", "eng"]

# Each country's catalog is scraped in one language: cijene.me (ME) names are
# Montenegrin/Serbian Latin, the UA stores' names are Ukrainian.
SOURCE_LOCALE_BY_COUNTRY = {"ME": "mne", "UA": "ukr"}

# Locales that get a stored `name_i18n` translation, per country. srb/bos
# are never translated separately: for ME they read the (already
# Serbian-like) source name, for UA they reuse the "mne" Latin translation -
# see LOCALE_FALLBACK.
TRANSLATION_TARGETS = {"ME": ["ukr", "rus", "eng"], "UA": ["rus", "eng", "mne"]}
LOCALE_FALLBACK = {"srb": "mne", "bos": "mne"}

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
                    # gpt-oss reasons before answering; its reasoning counts
                    # toward max_tokens, so a title-sized cap returns nothing.
                    "max_tokens": 1500,
                },
            )
            response.raise_for_status()
            data = response.json()
            translated = data["choices"][0]["message"]["content"].strip().strip('"')
            return translated or None
    except Exception as e:
        logger.warning(f"translate_name failed for '{name}' -> {target_locale}: {e}")
        return None


async def translate_to_all_locales(name: str, country: str = "ME") -> dict:
    """Translates `name` into every locale that needs it. Best-effort - any
    locale that fails to translate is simply omitted from the result dict."""
    if country != "ME":
        source = SOURCE_LOCALE_BY_COUNTRY[country]
        result = {}
        for locale in TRANSLATION_TARGETS[country]:
            translated = (await translate_batch([name], source, locale)).get(name)
            if translated:
                result[locale] = translated
        return result

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
    fallback = LOCALE_FALLBACK.get(locale)
    return name_i18n.get(locale) or (fallback and name_i18n.get(fallback)) or doc.get("name", "")


# ---------------------------------------------------------------------------
# Batch AI translation: Groq first, Claude Haiku for whatever Groq didn't
# return (rate limit, error, malformed or incomplete JSON).
# ---------------------------------------------------------------------------

BATCH_SYSTEM_PROMPT = (
    "You translate grocery and household product names for a price-comparison "
    "website, from {source} to {target}. Rules: never translate brand, "
    "manufacturer or product-line names - keep them as written{script_rule} "
    "Keep numbers and percentages as they are. Translate the generic product "
    "words and descriptors; keep it a short product title, not a sentence. "
    "Return one translation per input line, keyed by its number."
)

# Without the per-alphabet rule, models either left Cyrillic brands and
# units inside Latin-alphabet translations ("Mlijeko «Галичина» 900г") or,
# told to always use Latin units, wrote "900g" into Russian.
LATIN_SCRIPT_LOCALES = {"eng", "mne", "srb", "bos"}


def _batch_system_prompt(source: str, target: str) -> str:
    if target in LATIN_SCRIPT_LOCALES:
        rule = (
            ", but a brand written in Cyrillic must be transliterated into Latin "
            "letters. The whole result must use the Latin alphabet, units too "
            "(г->g, кг->kg, л->l, мл->ml)."
        )
    else:
        rule = (
            ", but a brand written in Latin letters stays in Latin letters. "
            "Units stay in Cyrillic (г, кг, л, мл)."
        )
    return BATCH_SYSTEM_PROMPT.format(source=LOCALE_NAMES[source], target=LOCALE_NAMES[target], script_rule=rule)


class _BatchItem(BaseModel):
    n: int
    text: str


class _BatchOut(BaseModel):
    translations: list[_BatchItem]


def _numbered(names: list[str]) -> str:
    return "\n".join(f"{i}. {name}" for i, name in enumerate(names, start=1))


def _collect(names: list[str], pairs: list[tuple[int, str]]) -> dict[str, str]:
    result = {}
    for n, text in pairs:
        text = (text or "").strip().strip('"')
        if 1 <= n <= len(names) and text:
            result[names[n - 1]] = text
    return result


async def _batch_groq(names: list[str], source: str, target: str) -> dict[str, str]:
    if not settings.groq_api_key:
        return {}
    system = _batch_system_prompt(source, target)
    user = (
        'Reply with only a JSON object {"translations": [{"n": 1, "text": "..."}, ...]}.\n\n'
        + _numbered(names)
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
            )
        if response.status_code == 429:
            logger.info("Groq rate-limited - batch goes to the fallback")
            return {}
        response.raise_for_status()
        content = json.loads(response.json()["choices"][0]["message"]["content"])
        pairs = [(int(item["n"]), str(item["text"])) for item in content.get("translations", [])]
        return _collect(names, pairs)
    except Exception as e:
        logger.warning(f"Groq batch translation failed ({source}->{target}, {len(names)} names): {e}")
        return {}


async def _batch_claude(names: list[str], source: str, target: str) -> dict[str, str]:
    if not settings.anthropic_api_key or not names:
        return {}
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        response = await client.messages.parse(
            model=settings.anthropic_model,
            max_tokens=8000,
            system=_batch_system_prompt(source, target),
            messages=[{"role": "user", "content": _numbered(names)}],
            output_config={"effort": "low"},
            output_format=_BatchOut,
        )
    except anthropic.RateLimitError as e:
        logger.warning(f"Claude batch translation rate-limited: {e}")
        return {}
    except anthropic.APIStatusError as e:
        logger.warning(f"Claude batch translation failed ({e.status_code}): {e.message}")
        return {}
    except anthropic.APIConnectionError as e:
        logger.warning(f"Claude batch translation connection error: {e}")
        return {}
    finally:
        await client.close()

    if response.stop_reason in ("refusal", "max_tokens") or response.parsed_output is None:
        logger.warning(f"Claude batch translation unusable (stop_reason={response.stop_reason})")
        return {}
    return _collect(names, [(item.n, item.text) for item in response.parsed_output.translations])


async def translate_batch(names: list[str], source: str, target: str) -> dict[str, str]:
    """{source name: translation} for as many of `names` as the AI steps
    managed; names missing from the result simply stay untranslated."""
    result = await _batch_groq(names, source, target)
    missing = [n for n in names if n not in result]
    if missing:
        result.update(await _batch_claude(missing, source, target))
    return result


# ---------------------------------------------------------------------------
# Search-query translation: someone browsing Montenegrin stores in Ukrainian
# types "молоко"; the catalog is searched for the Montenegrin "mlijeko" too.
# Used by app/services/product_query.py only when the query found (almost)
# nothing in any stored name, and cached there per country + query.
# ---------------------------------------------------------------------------

QUERY_SYSTEM_PROMPT = (
    "You translate search queries typed into a grocery price-comparison site. "
    "The query can be in any language. Translate it into {target} as the word(s) "
    "a shop would use in a product name (singular, no explanations). Keep brand "
    "names as they are. If it is already {target}, return it unchanged."
)


class _QueryOut(BaseModel):
    text: str


async def translate_search_query(query: str, target: str) -> Optional[str]:
    system = QUERY_SYSTEM_PROMPT.format(target=LOCALE_NAMES[target])
    if settings.groq_api_key:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                    json={
                        "model": settings.groq_model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": f'Reply with only {{"text": "..."}}.\n\nQuery: {query}'},
                        ],
                        "temperature": 0,
                        # A one-word translation needs no deliberation; the
                        # default effort made people wait ~7 s for results.
                        "reasoning_effort": "low",
                        "response_format": {"type": "json_object"},
                    },
                )
            response.raise_for_status()
            text = str(json.loads(response.json()["choices"][0]["message"]["content"]).get("text", "")).strip()
            if text:
                return text[:100]
        except Exception as e:
            logger.info(f"Groq query translation failed for '{query}': {e}")

    if not settings.anthropic_api_key:
        return None
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        response = await client.messages.parse(
            model=settings.anthropic_model,
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": query}],
            output_config={"effort": "low"},
            output_format=_QueryOut,
        )
    except anthropic.APIError as e:
        logger.warning(f"Claude query translation failed for '{query}': {e}")
        return None
    finally:
        await client.close()
    if response.parsed_output is None:
        return None
    return response.parsed_output.text.strip()[:100] or None
