"""
One-off merge of manually-collected Сільпо (silpo.ua) product data into the
UA product matrix.

Why this exists: the automated silpo_scraper.py has worked reliably all
session (445+ products per run) until, after several dozen scrape runs
against silpo.ua today from the production server's IP, every category
request started timing out ("Timeout 15000ms exceeded" on every single
category) - most likely a rate-limit/soft-block triggered by the unusually
high request volume, not a code bug (the same category pages load fine
from a normal interactive browser session on a different IP). Rather than
wait out an unknown cooldown period, backend/scripts/data/silpo_raw.jsonl
holds a manual collection (same aria-label format the real scraper parses)
across the site's product categories, gathered by hand the same way
merge_atb_manual.py's data was.

Reuses SilpoScraper._parse_item directly (not a reimplementation) so the
promo/regular aria-label parsing AND the per-100g weighed-produce/meat
price fix apply identically to this data. See CLAUDE.md for the full
story.
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
from app.services.scrapers.silpo_scraper import SilpoScraper  # noqa: E402

RAW_FILE = Path(__file__).resolve().parent / "data" / "silpo_raw.jsonl"


async def main():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    matcher = ProductMatcherService()
    scraper = SilpoScraper()

    stores = await db.stores.find({"country": "UA", "active": True}).sort("name", 1).to_list(length=50)
    store_names = [s["name"] for s in stores]
    if "Сільпо" not in store_names:
        print("Сільпо not found in db.stores for country=UA - aborting")
        return
    store_idx = store_names.index("Сільпо")
    print(f"Store order: {store_names} (Сільпо at index {store_idx})")

    raw_lines = [json.loads(line) for line in RAW_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(raw_lines)} raw Сільпо items")

    by_key: dict[str, dict] = {}
    skipped = 0
    for row in raw_lines:
        item = {"label": row["label"]}
        product = scraper._parse_item(item, row["category"])
        if product is None:
            skipped += 1
            continue

        normalized = matcher._normalize_product({
            "name": product.name,
            "source": "сільпо",
            "category": row["category"],
        })

        by_key[normalized["canonical_key"]] = {
            "canonical_name": normalized["canonical_name"],
            "category": normalized["category"],
            "unit": normalized["unit"],
            "price": product.price,
            "is_promo": bool(product.old_price),
        }

    print(f"{len(by_key)} distinct canonical products after normalization ({skipped} rows skipped)")

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

    print(f"Merged Сільпо data: {updated} existing groups updated, {created} new groups created")


if __name__ == "__main__":
    asyncio.run(main())
