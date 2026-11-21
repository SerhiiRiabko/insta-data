"""Product search shared by the Telegram bot and the website
(GET /products/search): one country's persisted catalog (the same documents
/products/matrix-cached serves), ranked by relevance.

Cross-language: every stored name is searched - the scraped source name and
all of its translations (`name_i18n.*`) - so someone browsing Montenegrin
stores in Ukrainian finds "Mlijeko ..." by typing "молоко". If a query still
finds (almost) nothing (an untranslated product, a language we don't store),
it is machine-translated into every stored language and each version is
searched too; those translations are cached in `db.query_translations`.

Every query word must match (AND). A country is a few thousand documents at
most, so an anchored-nowhere regex scan is fast enough and, unlike `$text`,
handles Cyrillic substrings ("молок" finds "молоко").
"""

import hashlib
import logging
import re
from datetime import datetime
from typing import Optional

from app.database.mongodb import get_mongo_db
from app.services.translation_service import (
    TRANSLATION_TARGETS,
    resolve_display_name,
    translate_search_query,
)

logger = logging.getLogger(__name__)

MAX_CANDIDATES = 500
# Fewer direct hits than this and the query is also translated.
MIN_DIRECT_RESULTS = 3
SEARCH_LOCALES = sorted({locale for targets in TRANSLATION_TARGETS.values() for locale in targets} | {"ukr"})
PROJECTION = {"id": 1, "name": 1, "name_i18n": 1, "unit": 1, "prices": 1, "promo": 1, "category": 1, "image_url": 1}


def _words(query: str) -> list[str]:
    return [w for w in re.split(r"\s+", query.strip().lower()) if len(w) >= 2][:5]


async def _find(words: list[str], country: str) -> list[dict]:
    fields = ["name"] + [f"name_i18n.{locale}" for locale in SEARCH_LOCALES]
    conditions = [
        {"$or": [{field: {"$regex": re.escape(word), "$options": "i"}} for field in fields]}
        for word in words
    ]
    return await get_mongo_db().products.find(
        {"country": country, "$and": conditions}, PROJECTION
    ).to_list(length=MAX_CANDIDATES)


async def translated_query(query: str) -> list[str]:
    """`query` in every stored language (cached), [] if the AI is unavailable."""
    normalized = " ".join(query.lower().split())
    key = hashlib.sha1(f"all|{normalized}".encode()).hexdigest()
    db = get_mongo_db()
    cached = await db.query_translations.find_one({"_id": key})
    if cached:
        return cached.get("texts") or []
    texts = await translate_search_query(normalized)
    if texts is None:
        return []  # AI unavailable right now - don't cache the miss
    await db.query_translations.update_one(
        {"_id": key},
        {"$set": {"query": normalized, "texts": texts, "created_at": datetime.utcnow()}},
        upsert=True,
    )
    return texts


async def search_country(query: str, country: str, lang: str, *, translate: bool = True) -> list[dict]:
    words = _words(query)
    if not words:
        return []
    docs = await _find(words, country)
    firsts = [words[0]]

    if translate and len(docs) < MIN_DIRECT_RESULTS:
        try:
            alternatives = await translated_query(query)
        except Exception as e:  # search must never fail because of the AI step
            logger.warning(f"Query translation failed for '{query}': {e}")
            alternatives = []
        seen = {d["id"] for d in docs}
        for alt in alternatives:
            alt_words = _words(alt)
            if not alt_words or alt_words == words:
                continue
            for doc in await _find(alt_words, country):
                if doc["id"] not in seen:
                    seen.add(doc["id"])
                    docs.append(doc)
            firsts.append(alt_words[0])

    def rank(doc: dict) -> tuple:
        display = resolve_display_name(doc, lang).lower()
        names = " ".join([display, doc.get("name", "").lower(), *(v.lower() for v in (doc.get("name_i18n") or {}).values())])
        starts = any(display.startswith(f) or doc.get("name", "").lower().startswith(f) for f in firsts)
        whole = any(re.search(rf"(^|\W){re.escape(f)}(\W|$)", names) for f in firsts)
        stores_with_price = sum(1 for p in (doc.get("prices") or []) if p is not None)
        return (0 if starts else 1 if whole else 2, -stores_with_price, len(display))

    docs.sort(key=rank)
    for doc in docs:
        doc["display_name"] = resolve_display_name(doc, lang)
    return docs


def in_store(docs: list[dict], index: int) -> list[tuple[dict, float]]:
    """(product, price) for products that store `index` sells, in relevance order."""
    return [(d, d["prices"][index]) for d in docs if index < len(d.get("prices") or []) and d["prices"][index] is not None]


def store_counts(docs: list[dict], store_count: int) -> list[int]:
    counts = [0] * store_count
    for doc in docs:
        for i, price in enumerate((doc.get("prices") or [])[:store_count]):
            if price is not None:
                counts[i] += 1
    return counts


def cheapest_index(prices: list[Optional[float]]) -> int:
    valid = [(p, i) for i, p in enumerate(prices) if p is not None]
    return min(valid)[1] if valid else -1
