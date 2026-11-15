"""Translate a country's whole product catalog into the other site languages
(cache -> dictionary -> Groq -> Claude Haiku, see app/services/translation_jobs.py).

Usage (from backend/):
    python scripts/translate_catalog.py UA --max 40      # small trial run first
    python scripts/translate_catalog.py UA --reset-ua    # one-off: drop the old dictionary output on UA names
    python scripts/translate_catalog.py UA
    python scripts/translate_catalog.py ME

--reset-ua: before 2026-11 the Montenegrin->X grocery dictionary also ran on
Ukrainian names at scrape time; it only swapped stray Latin brand words and
even wrote a "ukr" override onto Ukrainian names. This removes those
`name_i18n` values on UA products so the AI pass replaces them.
Re-running is safe: already translated names are skipped (and cached).
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from app.database.mongodb import get_mongo_db, init_mongo_db  # noqa: E402
from app.services.translation_jobs import fill_translations  # noqa: E402


def progress(locale: str, done: int, total: int) -> None:
    print(f"  {locale}: {done}/{total}", flush=True)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("country", choices=["ME", "UA"])
    parser.add_argument("--max", type=int, default=None, help="max names per language sent to the AI")
    parser.add_argument("--reset-ua", action="store_true", help="drop old dictionary output on UA products first")
    args = parser.parse_args()

    print(f"Groq: {'on' if settings.groq_api_key else 'OFF'} ({settings.groq_model}) · "
          f"Claude: {'on' if settings.anthropic_api_key else 'OFF'} ({settings.anthropic_model})")
    await init_mongo_db()

    if args.reset_ua:
        if args.country != "UA":
            raise SystemExit("--reset-ua only applies to UA")
        result = await get_mongo_db().products.update_many({"country": "UA"}, {"$unset": {"name_i18n": ""}})
        print(f"Reset name_i18n on {result.modified_count} UA products")

    stats = await fill_translations(args.country, max_ai_names=args.max, progress=progress)
    for locale, s in stats.items():
        print(f"{locale}: {s}")


if __name__ == "__main__":
    asyncio.run(main())
