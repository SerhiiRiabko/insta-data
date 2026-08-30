"""
One-off merge of manually-collected ATB (atbmarket.com) product data into
the UA product matrix.

Why this exists: atbmarket.com sits behind a Cloudflare managed challenge
that blocks every automated Playwright configuration tried in
atb_scraper.py (plain launch, navigator.webdriver patch, patchright,
persistent real-Chrome context, headed mode - see CLAUDE.md). A real
browser session (verified: an actual Chrome instance, not a scripted
launch) DOES pass, so the data behind this file was collected by manually
driving that session through the same 11 categories atb_scraper.py already
defines, and dumping each category's raw product cards (name/price/promo)
to backend/scripts/data/atb_raw.jsonl. This script turns that dump into
proper MongoDB updates, reusing the exact same ProductMatcherService
normalization every other store's live scrape goes through, so ATB's
prices land in the SAME groups as Novus/Varus/Сільпо/Фора instead of a
separate, inconsistent code path.

Not a repeatable pipeline - rerun by re-collecting atb_raw.jsonl by hand
and running this script again. See CLAUDE.md for the full story.
"""

import asyncio
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.product_matcher import ProductMatcherService  # noqa: E402

RAW_FILE = Path(__file__).resolve().parent / "data" / "atb_raw.jsonl"

# Same as atb_scraper.NAME_RE but tolerant of the "Купити "/" у АТБ Market"
# wrapper being partially stripped already (some entries in the manual dump
# were pre-cleaned inconsistently while transcribing).
NAME_RE = re.compile(r"^(?:Купити\s+)?(.+?)(?:\s+у\s+АТБ\s*Market)?$", re.IGNORECASE)


def clean_name(alt: str) -> str:
    match = NAME_RE.match(alt.strip())
    return match.group(1).strip() if match else alt.strip()


async def main():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    matcher = ProductMatcherService()

    stores = await db.stores.find({"country": "UA", "active": True}).sort("name", 1).to_list(length=50)
    store_names = [s["name"] for s in stores]
    if "АТБ" not in store_names:
        print("АТБ not found in db.stores for country=UA - aborting")
        return
    atb_idx = store_names.index("АТБ")
    print(f"Store order: {store_names} (АТБ at index {atb_idx})")

    raw_lines = [json.loads(line) for line in RAW_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(raw_lines)} raw ATB items")

    # canonical_key -> normalized product dict (last one wins on duplicate
    # keys within this batch, matching group_products()'s own behavior for
    # duplicate canonical keys within a single store's product list).
    by_key: dict[str, dict] = {}
    skipped = 0
    for row in raw_lines:
        name = clean_name(row["alt"])
        prices_raw = row.get("prices") or []
        try:
            prices = [float(p) for p in prices_raw if p]
        except (TypeError, ValueError):
            skipped += 1
            continue
        if not prices or not name:
            skipped += 1
            continue

        price = prices[0]
        old_price = prices[1] if row.get("isSale") and len(prices) > 1 else None
        category_raw = row["category"]

        normalized = matcher._normalize_product({
            "name": name,
            "source": "атб",
            "category": category_raw,
        })

        by_key[normalized["canonical_key"]] = {
            "canonical_name": normalized["canonical_name"],
            "category": normalized["category"],
            "unit": normalized["unit"],
            "price": price,
            "old_price": old_price,
            "is_promo": bool(old_price),
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
            prices[atb_idx] = entry["price"]
            promo[atb_idx] = entry["is_promo"]
            updated += 1
        else:
            prices = [None] * len(store_names)
            promo = [False] * len(store_names)
            prices[atb_idx] = entry["price"]
            promo[atb_idx] = entry["is_promo"]
            created += 1

        valid_prices = [p for p in prices if p is not None and p > 0]
        min_price = min(valid_prices) if valid_prices else None
        cheapest_store = None
        if min_price is not None:
            cheapest_store = store_names[prices.index(min_price)]

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

    print(f"Merged ATB data: {updated} existing groups updated, {created} new groups created")


if __name__ == "__main__":
    asyncio.run(main())
