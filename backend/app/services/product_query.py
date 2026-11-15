"""Product search for the Telegram bot: one country's persisted catalog
(the same documents /products/matrix-cached serves), matched on the source
name and the translated name for the user's language, ranked by relevance.

Every query word must match (AND). A country is a few thousand documents at
most, so an anchored-nowhere regex scan is fast enough and, unlike `$text`,
handles Cyrillic substrings ("молок" finds "молоко").
"""

import re
from typing import Optional

from app.database.mongodb import get_mongo_db
from app.services.translation_service import LOCALE_FALLBACK, resolve_display_name

MAX_CANDIDATES = 500


def _words(query: str) -> list[str]:
    return [w for w in re.split(r"\s+", query.strip().lower()) if len(w) >= 2][:5]


async def search_country(query: str, country: str, lang: str) -> list[dict]:
    words = _words(query)
    if not words:
        return []
    locale = LOCALE_FALLBACK.get(lang, lang)
    fields = ["name", f"name_i18n.{locale}"]
    conditions = [
        {"$or": [{field: {"$regex": re.escape(word), "$options": "i"}} for field in fields]}
        for word in words
    ]
    docs = await get_mongo_db().products.find(
        {"country": country, "$and": conditions},
        {"id": 1, "name": 1, "name_i18n": 1, "unit": 1, "prices": 1, "promo": 1, "category": 1},
    ).to_list(length=MAX_CANDIDATES)

    first = words[0]

    def rank(doc: dict) -> tuple:
        display = resolve_display_name(doc, lang).lower()
        source = doc.get("name", "").lower()
        starts = display.startswith(first) or source.startswith(first)
        whole = bool(re.search(rf"(^|\W){re.escape(first)}(\W|$)", f"{display} {source}"))
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
