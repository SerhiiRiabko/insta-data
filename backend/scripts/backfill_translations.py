"""
One-off backfill: populate name_i18n on every existing product using the
dictionary translator (Phase 4.6 follow-up - see PHASE_4_PLAN.md).

New products get name_i18n automatically at scrape time (products.py
_persist_live_products); this script only needed to run once for products
that were already in the DB before that ingest-time hook existed.

Usage: venv/Scripts/python.exe scripts/backfill_translations.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.services.translation_service import LOCALES_NEEDING_TRANSLATION
from app.services.grocery_dictionary import translate_via_dictionary


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]

    products = await db.products.find({}).to_list(length=None)
    print(f"Found {len(products)} products")

    updated = 0
    unmatched = []
    for product in products:
        name = product.get("name", "")
        name_i18n = dict(product.get("name_i18n") or {})
        changed = False
        for locale in LOCALES_NEEDING_TRANSLATION:
            translated = translate_via_dictionary(name, locale)
            if translated:
                name_i18n[locale] = translated
                changed = True

        if changed:
            await db.products.update_one(
                {"_id": product["_id"]}, {"$set": {"name_i18n": name_i18n}}
            )
            updated += 1
        else:
            unmatched.append(name)

    lines = [f"Updated {updated}/{len(products)} products", f"No dictionary match for {len(unmatched)} products:"]
    for name in unmatched:
        lines.append(f"  - {name}")
    out_path = Path(__file__).resolve().parent / "backfill_result.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"done, see {out_path}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())