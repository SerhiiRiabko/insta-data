"""One-time CLI to reset a user's password (e.g. when the original admin
password wasn't recorded anywhere retrievable - passwords are bcrypt-hashed,
never stored in plaintext, so there is nothing to "look up").

Usage:
    python scripts/reset_admin_password.py user@example.com [new_password]

If new_password is omitted, a random 16-char password is generated and
printed once.
"""

import asyncio
import secrets
import sys

sys.path.insert(0, ".")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.auth_service import hash_password  # noqa: E402


async def main(email: str, new_password: str) -> None:
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]

    email = email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        print(f"No user found for {email}.")
        return

    await db.users.update_one(
        {"_id": user["_id"]}, {"$set": {"password_hash": hash_password(new_password)}}
    )
    print(f"Password for {email} reset to: {new_password}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage: python scripts/reset_admin_password.py user@example.com [new_password]")
        sys.exit(1)
    pwd = sys.argv[2] if len(sys.argv) == 3 else secrets.token_urlsafe(12)
    asyncio.run(main(sys.argv[1], pwd))
