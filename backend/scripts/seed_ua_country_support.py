"""One-off migration for multi-country support (Phase "Shop Price Online").

Before this, `stores` and `products` had no `country` field at all - every
existing document implicitly meant Montenegro. This script:

1. Backfills `country: "ME"` on any `stores`/`products` doc missing it.
2. Seeds the 6 Ukrainian stores (АТБ, Сільпо, Фора, Novus, Varus, Коло) into
   `stores` with `country: "UA"`, `active: True` - no scraper exists for them
   yet, so they'll show with zero products until that's built, but the
   country selector and "Магазини" page can already list them.

Idempotent: safe to re-run (upserts UA stores by name, backfill only touches
docs missing the field).

Usage:
    python scripts/seed_ua_country_support.py
"""

import asyncio
import sys
import uuid
from datetime import datetime

sys.path.insert(0, ".")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from app.core.config import settings  # noqa: E402

UA_STORES = [
    {"name": "АТБ", "initial": "А", "color": "#e11d48", "url": "https://www.atbmarket.com/"},
    {"name": "Сільпо", "initial": "С", "color": "#16a34a", "url": "https://silpo.ua/"},
    {"name": "Фора", "initial": "Ф", "color": "#f59e0b", "url": "https://fora.ua/"},
    {"name": "Novus", "initial": "N", "color": "#2563eb", "url": "https://novus.zakaz.ua/uk/"},
    {"name": "Varus", "initial": "V", "color": "#7c3aed", "url": "https://varus.ua/"},
    {"name": "Коло", "initial": "К", "color": "#0891b2", "url": ""},
]


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    now = datetime.utcnow()

    stores_result = await db.stores.update_many(
        {"country": {"$exists": False}}, {"$set": {"country": "ME"}}
    )
    print(f"Backfilled country=ME on {stores_result.modified_count} existing store(s).")

    products_result = await db.products.update_many(
        {"country": {"$exists": False}}, {"$set": {"country": "ME"}}
    )
    print(f"Backfilled country=ME on {products_result.modified_count} existing product(s).")

    inserted = 0
    for store in UA_STORES:
        existing = await db.stores.find_one({"name": store["name"], "country": "UA"})
        if existing:
            continue
        await db.stores.insert_one({
            "_id": uuid.uuid4().hex,
            **store,
            "country": "UA",
            "active": True,
            "created_at": now,
            "updated_at": now,
        })
        inserted += 1
    print(f"Inserted {inserted} new Ukrainian store(s) (skipped {len(UA_STORES) - inserted} already present).")


if __name__ == "__main__":
    asyncio.run(main())
