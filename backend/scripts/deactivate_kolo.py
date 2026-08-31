"""
One-off migration: deactivate Коло (set stores.active=False) and remove its
slot from every UA product's `prices`/`promo` arrays so the remaining
stores stay correctly aligned by position.

Why this can't be just "flip active to false": `/matrix-cached` returns
each product's `prices`/`promo` arrays exactly as stored (6-wide, indexed
to the OLD 6-store order including Коло), while `get_stores_for_country`
would now return only 5 active stores. The frontend zips `stores[i]` with
`prices[i]` by position - leaving the arrays 6-wide would shift Сільпо's
price under the "Фора" column and drop Фора's price entirely. So every
UA product doc needs its Коло slot spliced out too, not just the store
flipped inactive.

Reason for removing Коло: VARUS acquired the chain (closed 2026-08-04,
see kolomarket.com.ua news) but explicitly said pricing/branding changes
would be "gradual" - Coло is a convenience-store format, VARUS a
supermarket, so its manually-collected 7-product price set
(merge_kolo_manual.py) can't be assumed to reflect VARUS pricing. User
asked to pull it from the table until the situation is clearer. Reversible:
re-run seed/activate Коло in db.stores and re-run merge_kolo_manual.py
(the stores.country migration script already backfills a country-sorted
prices array shape from scratch on next live scrape regardless).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from app.core.config import settings  # noqa: E402

STORE_NAME = "Коло"


async def main():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]

    old_stores = await db.stores.find({"country": "UA", "active": True}).sort("name", 1).to_list(length=50)
    old_names = [s["name"] for s in old_stores]
    if STORE_NAME not in old_names:
        print(f"{STORE_NAME} not found among active UA stores - nothing to do")
        return
    kolo_idx = old_names.index(STORE_NAME)
    new_names = [n for n in old_names if n != STORE_NAME]
    print(f"Old store order: {old_names} ({STORE_NAME} at index {kolo_idx})")
    print(f"New store order: {new_names}")

    result = await db.stores.update_one({"country": "UA", "name": STORE_NAME}, {"$set": {"active": False}})
    print(f"Deactivated {STORE_NAME}: matched={result.matched_count}, modified={result.modified_count}")

    docs = await db.products.find({"country": "UA"}).to_list(length=100000)
    print(f"Fixing prices/promo arrays on {len(docs)} UA product docs...")

    fixed = 0
    for doc in docs:
        prices = list(doc.get("prices") or [])
        promo = list(doc.get("promo") or [])
        if len(prices) <= kolo_idx:
            continue  # already short/malformed - leave alone rather than guess

        new_prices = prices[:kolo_idx] + prices[kolo_idx + 1:]
        new_promo = (promo[:kolo_idx] + promo[kolo_idx + 1:]) if len(promo) > kolo_idx else promo

        valid = [p for p in new_prices if p is not None and p > 0]
        min_price = min(valid) if valid else None
        cheapest_store = None
        if min_price is not None and len(new_names) == len(new_prices):
            cheapest_store = new_names[new_prices.index(min_price)]

        await db.products.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "prices": new_prices,
                "promo": new_promo,
                "min_price": min_price,
                "cheapest_store": cheapest_store,
            }},
        )
        fixed += 1

    print(f"Fixed {fixed} product docs")


if __name__ == "__main__":
    asyncio.run(main())
