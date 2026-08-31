"""
One-off merge of manually-collected Коло product data into the UA
product matrix.

Why this exists: "Коло" ("Продукти коло дому", ~250 small "near-home"
mini-markets) has no online store or price catalog of its own - confirmed
on both its correct official site (kolomarket.com.ua - not to be confused
with kolo.ua, an unrelated Polish bathroom-fixtures brand) and on two
third-party flyer aggregators (gotoshop.ua, ukrtopshop.com), which
explicitly say the store's promotional catalog is unavailable. The one
real source found: ukrtopshop.com hosts scanned Instagram-story-style
promo images for occasional Коло campaigns, each showing one or two
products with a real crossed-out old price and a real new price baked
into the image (not extractable text - read by hand, screenshot by
screenshot, same as the ATB/Сільпо manual collections this session).

Very low volume by nature (single digits to ~10 products at a time, not
a real catalog) and not automatable without adding OCR to the stack
(deliberately not done - pytesseract/pillow were already removed once
this project as dead weight from an abandoned Instagram-OCR pipeline).
Rerun by re-collecting backend/scripts/data/kolo_raw.jsonl by hand from
whatever Коло campaign images ukrtopshop.com/kiev-kolomarket.html
currently lists, then running this script again.
"""

import asyncio
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.product_matcher import ProductMatcherService  # noqa: E402

RAW_FILE = Path(__file__).resolve().parent / "data" / "kolo_raw.jsonl"


async def main():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    matcher = ProductMatcherService()

    stores = await db.stores.find({"country": "UA", "active": True}).sort("name", 1).to_list(length=50)
    store_names = [s["name"] for s in stores]
    if "Коло" not in store_names:
        print("Коло not found in db.stores for country=UA - aborting")
        return
    store_idx = store_names.index("Коло")
    print(f"Store order: {store_names} (Коло at index {store_idx})")

    rows = [json.loads(line) for line in RAW_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(rows)} raw Коло items")

    by_key: dict[str, dict] = {}
    for row in rows:
        normalized = matcher._normalize_product({
            "name": row["name"],
            "source": "коло",
            "category": row["category"],
        })
        by_key[normalized["canonical_key"]] = {
            "canonical_name": normalized["canonical_name"],
            "category": normalized["category"],
            "unit": normalized["unit"],
            "price": row["price"],
            "is_promo": row.get("old_price") is not None and row["old_price"] > row["price"],
        }

    print(f"{len(by_key)} distinct canonical products after normalization")

    now = datetime.utcnow()
    updated = 0
    created = 0
    for entry in by_key.values():
        group_id = hashlib.md5(
            f"{entry['canonical_name'].lower().strip()}:{entry['category'].lower().strip()}".encode()
        ).hexdigest()

        existing = await db.products.find_one({"id": group_id, "country": "UA"})

        if existing:
            prices = existing.get("prices") or [None] * len(store_names)
            promo = existing.get("promo") or [False] * len(store_names)
            while len(prices) < len(store_names):
                prices.append(None)
            while len(promo) < len(store_names):
                promo.append(False)
            prices[store_idx] = entry["price"]
            promo[store_idx] = entry["is_promo"]
            updated += 1
        else:
            prices = [None] * len(store_names)
            promo = [False] * len(store_names)
            prices[store_idx] = entry["price"]
            promo[store_idx] = entry["is_promo"]
            created += 1

        valid_prices = [p for p in prices if p is not None and p > 0]
        min_price = min(valid_prices) if valid_prices else None
        cheapest_store = store_names[prices.index(min_price)] if min_price is not None else None

        set_fields = {
            "id": group_id,
            "country": "UA",
            "name": entry["canonical_name"],
            "unit": entry["unit"],
            "category": entry["category"],
            "prices": prices,
            "promo": promo,
            "min_price": min_price,
            "cheapest_store": cheapest_store,
            "updated_at": now,
        }

        await db.products.update_one(
            {"id": group_id, "country": "UA"},
            {
                "$set": set_fields,
                "$push": {
                    "price_history": {
                        "$each": [{"date": now, "prices": prices}],
                        "$slice": -30,
                    }
                },
            },
            upsert=True,
        )

    print(f"Merged Коло data: {updated} existing groups updated, {created} new groups created")


if __name__ == "__main__":
    asyncio.run(main())
