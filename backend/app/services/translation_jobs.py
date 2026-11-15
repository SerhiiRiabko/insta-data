"""Fills `name_i18n` for a whole country's catalog.

Translations are cached in `db.name_translations`, keyed by
(source locale, exact source name) - NOT by product id: product ids are a
hash of name+category and change every time the matching logic changes (see
CLAUDE.md, entry 29), which would otherwise throw away paid-for AI
translations on every such fix. The weekly refresh therefore only sends
genuinely new names to the AI.

Order per name and target locale: cache -> grocery dictionary (Montenegro
only - it's a Montenegrin->X word list) -> translate_batch() (Groq, then
Claude Haiku).
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional

from pymongo import UpdateMany, UpdateOne

from app.database.mongodb import get_mongo_db
from app.services.grocery_dictionary import translate_via_dictionary
from app.services.translation_service import (
    SOURCE_LOCALE_BY_COUNTRY,
    TRANSLATION_TARGETS,
    translate_batch,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 40


def _cache_id(source: str, name: str) -> str:
    return hashlib.sha1(f"{source}|{name}".encode("utf-8")).hexdigest()


async def fill_translations(
    country: str,
    *,
    use_ai: bool = True,
    max_ai_names: Optional[int] = None,
    progress=None,
) -> dict:
    """Translates every product name of `country` that still lacks a target
    locale. `max_ai_names` caps how many names go to the AI per locale (cost
    guard for ad-hoc runs); `progress(locale, done, total)` is an optional
    callback for CLI scripts. Returns per-locale stats."""
    db = get_mongo_db()
    source = SOURCE_LOCALE_BY_COUNTRY[country]
    docs = await db.products.find({"country": country}, {"name": 1, "name_i18n": 1}).to_list(length=100000)
    stats = {}

    for target in TRANSLATION_TARGETS[country]:
        missing = sorted({d["name"] for d in docs if d.get("name") and not (d.get("name_i18n") or {}).get(target)})

        cached: dict[str, str] = {}
        if missing:
            ids = {_cache_id(source, n): n for n in missing}
            async for row in db.name_translations.find({"_id": {"$in": list(ids)}}, {"t": 1}):
                text = (row.get("t") or {}).get(target)
                if text:
                    cached[ids[row["_id"]]] = text
        await _write(db, country, source, target, cached, cache=False)

        dictionary: dict[str, str] = {}
        if source == "mne":
            for name in missing:
                if name not in cached:
                    text = translate_via_dictionary(name, target)
                    if text:
                        dictionary[name] = text
        await _write(db, country, source, target, dictionary, cache=True)

        todo = [n for n in missing if n not in cached and n not in dictionary]
        if max_ai_names is not None:
            todo = todo[:max_ai_names]
        from_ai = 0
        if use_ai:
            for start in range(0, len(todo), BATCH_SIZE):
                translated = await translate_batch(todo[start:start + BATCH_SIZE], source, target)
                # Written per batch, so an interrupted run keeps what it already paid for.
                await _write(db, country, source, target, translated, cache=True)
                from_ai += len(translated)
                if progress:
                    progress(target, min(start + BATCH_SIZE, len(todo)), len(todo))

        stats[target] = {
            "missing": len(missing),
            "cache": len(cached),
            "dictionary": len(dictionary),
            "ai": from_ai,
            "left": len(missing) - len(cached) - len(dictionary) - from_ai,
        }
        logger.info(f"Translations {country} -> {target}: {stats[target]}")
    return stats


async def _write(db, country: str, source: str, target: str, translations: dict[str, str], *, cache: bool) -> None:
    if not translations:
        return
    await db.products.bulk_write(
        [
            UpdateMany({"country": country, "name": name}, {"$set": {f"name_i18n.{target}": text}})
            for name, text in translations.items()
        ],
        ordered=False,
    )
    if cache:
        now = datetime.utcnow()
        await db.name_translations.bulk_write(
            [
                UpdateOne(
                    {"_id": _cache_id(source, name)},
                    {"$set": {f"t.{target}": text, "updated_at": now}, "$setOnInsert": {"name": name, "source": source}},
                    upsert=True,
                )
                for name, text in translations.items()
            ],
            ordered=False,
        )
