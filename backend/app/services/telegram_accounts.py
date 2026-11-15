"""Telegram identity <-> site account.

Every Telegram user who talks to the bot gets a `users` document
(`telegram_id` set, `email` None until they add one). Linking from the site
attaches the Telegram identity to an existing email account; if the bot had
already created a Telegram-only document for that person, it's merged into
the email account (paid days, lists, payments) and deleted, so there is
always exactly one account per person.

One-time tokens (`db.telegram_tokens`, TTL-indexed) carry the handshakes:

- link       site (logged in) -> t.me/<bot>?start=link_<token> -> bot confirms
- login      site (logged out) -> t.me/<bot>?start=login_<token> -> bot
             confirms -> the waiting browser polls and gets a session
- web_login  bot -> one-time URL that logs that Telegram user into the site

link/login require an explicit "confirm" tap in the bot: a link someone else
generated and sent you must not silently log *their* browser into *your*
account (or bind your Telegram to their account).
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.database.mongodb import get_mongo_db
from app.services.subscription_service import PAID_PLANS

logger = logging.getLogger(__name__)

TOKEN_TTL = {
    "link": timedelta(minutes=15),
    "login": timedelta(minutes=5),
    "web_login": timedelta(minutes=10),
}

BOT_LANG_FROM_CODE = {
    "uk": "ukr",
    "ru": "rus",
    "sr": "mne",
    "bs": "mne",
    "hr": "mne",
    "me": "mne",
    "cnr": "mne",
}


class LinkError(Exception):
    """Raised with a stable `code` the caller maps to a localized message."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


async def ensure_indexes() -> None:
    db = get_mongo_db()
    # Email is optional now (Telegram-only accounts), so the unique index has
    # to skip documents without one - a plain unique index treats every
    # missing email as the same `null` value and allows only one such user.
    indexes = {i["name"]: i async for i in db.users.list_indexes()}
    if "email_unique" in indexes and "partialFilterExpression" not in indexes["email_unique"]:
        await db.users.drop_index("email_unique")
    await db.users.create_index(
        "email", unique=True, name="email_unique",
        partialFilterExpression={"email": {"$type": "string"}},
    )
    await db.users.create_index(
        "telegram_id", unique=True, name="telegram_id_unique",
        partialFilterExpression={"telegram_id": {"$type": "number"}},
    )
    await db.users.create_index("telegram_username_lc", name="telegram_username_lc")
    await db.telegram_tokens.create_index("expires_at", expireAfterSeconds=0, name="ttl_expires_at")


def bot_lang_for(language_code: Optional[str]) -> str:
    code = (language_code or "").split("-")[0].lower()
    return BOT_LANG_FROM_CODE.get(code, "eng")


def _telegram_fields(tg_user: dict) -> dict:
    username = tg_user.get("username")
    return {
        "telegram_id": int(tg_user["id"]),
        "telegram_username": username,
        "telegram_username_lc": username.lower() if username else None,
        "telegram_first_name": tg_user.get("first_name"),
    }


def is_bot_admin(user: dict) -> bool:
    if user.get("is_admin"):
        return True
    admins = {u.strip().lstrip("@").lower() for u in settings.admin_telegram_usernames.split(",") if u.strip()}
    return bool(user.get("telegram_username_lc")) and user["telegram_username_lc"] in admins


async def get_or_create_telegram_user(tg_user: dict) -> dict:
    """`tg_user`: {id, username, first_name, language_code}. Refreshes the
    stored username every time (people rename themselves)."""
    db = get_mongo_db()
    fields = _telegram_fields(tg_user)
    user = await db.users.find_one_and_update(
        {"telegram_id": fields["telegram_id"]},
        {"$set": fields},
        return_document=True,
    )
    if user:
        return user

    user = {
        "_id": uuid.uuid4().hex,
        "email": None,
        "password_hash": None,
        "is_admin": False,
        "bot_lang": bot_lang_for(tg_user.get("language_code")),
        "country": None,
        "created_at": datetime.utcnow(),
        **fields,
    }
    try:
        await db.users.insert_one(user)
    except Exception:
        # Two updates from a brand-new user processed concurrently - the
        # other one won the insert, just read it back.
        user = await db.users.find_one({"telegram_id": fields["telegram_id"]})
    return user


async def find_user_by_identifier(identifier: str) -> Optional[dict]:
    """Admin lookup: email, @username or numeric Telegram id."""
    db = get_mongo_db()
    value = identifier.strip()
    if "@" in value and not value.startswith("@"):
        return await db.users.find_one({"email": value.lower()})
    if value.lstrip("-").isdigit():
        return await db.users.find_one({"telegram_id": int(value)})
    return await db.users.find_one({"telegram_username_lc": value.lstrip("@").lower()})


async def _merge_into(target: dict, source: dict) -> None:
    """Moves a Telegram-only account's belongings into `target`, then
    deletes it. Paid days: keep the later expiry of each plan."""
    db = get_mongo_db()
    update = {}
    for plan in PAID_PLANS:
        key = f"{plan}_until"
        if source.get(key) and (not target.get(key) or source[key] > target[key]):
            update[key] = source[key]
    for key in ("bot_lang", "country"):
        if source.get(key) and not target.get(key):
            update[key] = source[key]
    if update:
        await db.users.update_one({"_id": target["_id"]}, {"$set": update})

    for collection in (db.shopping_lists,):
        await collection.update_many({"owner_user_id": source["_id"]}, {"$set": {"owner_user_id": target["_id"]}})
    for collection in (db.payments, db.payment_requests, db.plan_events):
        await collection.update_many({"user_id": source["_id"]}, {"$set": {"user_id": target["_id"]}})
    await db.users.delete_one({"_id": source["_id"]})
    logger.info(f"Merged Telegram-only account {source['_id']} into {target['_id']}")


async def link_telegram(user_id: str, tg_user: dict) -> dict:
    """Attaches `tg_user` to site account `user_id`. Raises LinkError."""
    db = get_mongo_db()
    target = await db.users.find_one({"_id": user_id})
    if not target:
        raise LinkError("account_not_found")

    fields = _telegram_fields(tg_user)
    other = await db.users.find_one({"telegram_id": fields["telegram_id"]})
    if other and other["_id"] != user_id:
        if other.get("email"):
            raise LinkError("telegram_linked_elsewhere")
        await _merge_into(target, other)

    await db.users.update_one({"_id": user_id}, {"$set": fields})
    return await db.users.find_one({"_id": user_id})


async def unlink_telegram(user_id: str) -> None:
    db = get_mongo_db()
    user = await db.users.find_one({"_id": user_id})
    if not user or not user.get("email") or not user.get("password_hash"):
        # Without email+password the Telegram link is the only way back in.
        raise LinkError("no_other_login")
    await db.users.update_one(
        {"_id": user_id},
        {"$unset": {"telegram_id": "", "telegram_username": "", "telegram_username_lc": "", "telegram_first_name": ""}},
    )


# ---------------------------------------------------------------------------
# One-time tokens
# ---------------------------------------------------------------------------

async def create_token(kind: str, **fields) -> str:
    token = secrets.token_urlsafe(24).replace("-", "").replace("_", "")[:32]
    await get_mongo_db().telegram_tokens.insert_one({
        "_id": token,
        "kind": kind,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + TOKEN_TTL[kind],
        **fields,
    })
    return token


async def get_token(token: str, kind: str) -> Optional[dict]:
    doc = await get_mongo_db().telegram_tokens.find_one({"_id": token, "kind": kind})
    if not doc or doc["expires_at"] < datetime.utcnow():
        return None
    return doc


async def confirm_token(token: str, kind: str, **fields) -> Optional[dict]:
    """pending -> confirmed, atomically. None if missing/expired/used."""
    return await get_mongo_db().telegram_tokens.find_one_and_update(
        {"_id": token, "kind": kind, "status": "pending", "expires_at": {"$gt": datetime.utcnow()}},
        {"$set": {"status": "confirmed", "confirmed_at": datetime.utcnow(), **fields}},
        return_document=True,
    )


async def consume_token(token: str, kind: str, from_status: str) -> Optional[dict]:
    """-> used, atomically (single use). None if not in `from_status`."""
    return await get_mongo_db().telegram_tokens.find_one_and_update(
        {"_id": token, "kind": kind, "status": from_status, "expires_at": {"$gt": datetime.utcnow()}},
        {"$set": {"status": "used", "used_at": datetime.utcnow()}},
        return_document=True,
    )


async def admin_chat_ids() -> list[int]:
    """Telegram chats that receive payment-approval requests."""
    db = get_mongo_db()
    admins = {u.strip().lstrip("@").lower() for u in settings.admin_telegram_usernames.split(",") if u.strip()}
    query = {"telegram_id": {"$type": "number"}, "$or": [{"is_admin": True}, {"telegram_username_lc": {"$in": list(admins)}}]}
    return [u["telegram_id"] async for u in db.users.find(query, {"telegram_id": 1})]
