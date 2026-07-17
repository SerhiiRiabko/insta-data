"""One-time CLI to promote a user to admin (Phase 4.4).

There's no admin UI to create the first admin - that's a chicken-and-egg
problem an admin-gated panel can't solve for itself. Run this once, against
a user who has already registered/logged in at least once (via password or
magic link, either works), to flip their `is_admin` flag.

Usage:
    python scripts/bootstrap_admin.py user@example.com
"""

import asyncio
import sys

sys.path.insert(0, ".")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from app.core.config import settings  # noqa: E402


async def main(email: str) -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]

    email = email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        print(f"No user found for {email} - log in at least once first, then re-run this.")
        return

    await db.users.update_one({"_id": user["_id"]}, {"$set": {"is_admin": True}})
    print(f"{email} is now an admin.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/bootstrap_admin.py user@example.com")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))