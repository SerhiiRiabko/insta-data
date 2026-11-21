"""Shopping-list core shared by the web API (endpoints/lists.py) and the
Telegram bot, so both read/write the exact same documents.

A list belongs to one country: its prices are resolved against that
country's stores (`get_stores_for_country`), in the same column order the
price matrix uses. Lists created before the `country` field existed get it
inferred from their products the first time they're read.

Access (2026-11): a list is private to its owner and the people it was
shared with (`member_user_ids`). Members join through the bot - by the owner
naming their @username/email, or by opening an invitation link
(t.me/<bot>?start=join_<token>) - so every member has a Telegram account,
and sees the list both in the bot and on the website once logged in there
with that Telegram. Members can tick items and add/remove products; adding
needs the owner's Gold to be active (the owner pays for the shared list).
Legacy guest lists without an owner stay open by link until their TTL.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from app.api.v1.endpoints.products import calculate_cheapest, get_stores_for_country
from app.database.mongodb import get_mongo_db
from app.services import telegram_accounts
from app.services.subscription_service import can_use_lists, get_plan_settings
from app.services.translation_service import resolve_display_name

logger = logging.getLogger(__name__)

# Guest lists aren't meant to live forever - 30 days of inactivity (no view,
# no toggle) and Mongo's TTL monitor reaps the document. Saved lists
# (owner_user_id set) are excluded via partialFilterExpression - they live
# until the owner deletes them.
LIST_TTL_SECONDS = 30 * 24 * 60 * 60


class ListError(Exception):
    def __init__(self, code: str, status: int = 400):
        super().__init__(code)
        self.code = code
        self.status = status


async def ensure_indexes() -> None:
    db = get_mongo_db()
    try:
        await db.shopping_lists.create_index(
            "updated_at",
            expireAfterSeconds=LIST_TTL_SECONDS,
            name="ttl_updated_at",
            partialFilterExpression={"owner_user_id": None},
        )
    except Exception:
        # Phase 4.1 created this index without partialFilterExpression;
        # Mongo rejects re-creating the same name with different options
        # rather than migrating it - drop and recreate once.
        await db.shopping_lists.drop_index("ttl_updated_at")
        await db.shopping_lists.create_index(
            "updated_at",
            expireAfterSeconds=LIST_TTL_SECONDS,
            name="ttl_updated_at",
            partialFilterExpression={"owner_user_id": None},
        )
    await db.shopping_lists.create_index([("owner_user_id", 1), ("updated_at", -1)], name="owner_updated")
    await db.shopping_lists.create_index([("member_user_ids", 1), ("updated_at", -1)], name="member_updated")


# ---------------------------------------------------------------------------
# Access
# ---------------------------------------------------------------------------

def role_of(doc: dict, user: Optional[dict]) -> Optional[str]:
    """"owner" / "member" / "admin" / "guest" (legacy ownerless list), or
    None = no access."""
    owner_id = doc.get("owner_user_id")
    if owner_id is None:
        return "guest"
    if not user:
        return None
    if owner_id == user["_id"]:
        return "owner"
    if user["_id"] in (doc.get("member_user_ids") or []):
        return "member"
    if user.get("is_admin"):
        return "admin"
    return None


def assert_can_view(doc: dict, user: Optional[dict]) -> str:
    role = role_of(doc, user)
    if role is None:
        raise ListError("login_required" if not user else "list_private", 401 if not user else 403)
    return role


async def can_edit(doc: dict, user: Optional[dict]) -> bool:
    """Adding/removing products: anyone with access, while the owner's Gold
    is active (ownerless legacy lists: the editor's own Gold)."""
    role = role_of(doc, user)
    if role is None:
        return False
    if role == "guest":
        return bool(user) and can_use_lists(user)
    if role == "owner":
        return can_use_lists(user)
    owner = await get_mongo_db().users.find_one({"_id": doc["owner_user_id"]})
    return bool(owner) and can_use_lists(owner)


async def assert_can_edit(doc: dict, user: Optional[dict]) -> None:
    assert_can_view(doc, user)
    if not await can_edit(doc, user):
        raise ListError("gold_required", 403)


def _display(user: dict) -> str:
    if user.get("telegram_username"):
        return f"@{user['telegram_username']}"
    return user.get("telegram_first_name") or user.get("email") or "—"


async def members_of(doc: dict) -> list[dict]:
    ids = doc.get("member_user_ids") or []
    if not ids:
        return []
    found = {u["_id"]: u async for u in get_mongo_db().users.find({"_id": {"$in": ids}})}
    return [{"id": uid, "name": _display(found[uid])} for uid in ids if uid in found]


async def owner_name(doc: dict) -> Optional[str]:
    if not doc.get("owner_user_id"):
        return None
    owner = await get_mongo_db().users.find_one({"_id": doc["owner_user_id"]})
    return _display(owner) if owner else None


async def add_member(list_id: str, user_id: str) -> tuple[dict, bool]:
    """(doc, added) - `added` False for the owner or an existing member."""
    doc = await get_list_doc(list_id)
    if doc.get("owner_user_id") in (None, user_id) or user_id in (doc.get("member_user_ids") or []):
        return doc, False
    await get_mongo_db().shopping_lists.update_one({"_id": list_id}, {"$addToSet": {"member_user_ids": user_id}})
    doc["member_user_ids"] = (doc.get("member_user_ids") or []) + [user_id]
    return doc, True


async def remove_member(list_id: str, user_id: str) -> dict:
    await get_mongo_db().shopping_lists.update_one({"_id": list_id}, {"$pull": {"member_user_ids": user_id}})
    return await get_list_doc(list_id)


async def create_invite(list_id: str, created_by: str, *, multi_use: bool = False) -> str:
    """An invitation opened in the bot (start=join_<token>). Single use by
    default - the "send to a person" case; `multi_use` for a list message
    posted into a chat via inline mode, where everyone in that chat is who
    it was shared with."""
    return await telegram_accounts.create_token("list_invite", list_id=list_id, user_id=created_by, multi_use=multi_use)


async def chat_invite(doc: dict) -> str:
    """The list's reusable invitation for inline (chat) shares - one per
    list, renewed once it expires."""
    token = doc.get("chat_invite_token")
    if token and await telegram_accounts.get_token(token, "list_invite"):
        return token
    token = await create_invite(doc["_id"], doc["owner_user_id"], multi_use=True)
    await get_mongo_db().shopping_lists.update_one({"_id": doc["_id"]}, {"$set": {"chat_invite_token": token}})
    doc["chat_invite_token"] = token
    return token


async def join_by_invite(token: str, user: dict) -> tuple[Optional[dict], bool]:
    """(list doc or None if the invitation is invalid/used, newly added)."""
    invite = await telegram_accounts.get_token(token, "list_invite")
    if not invite:
        return None, False
    try:
        doc = await get_list_doc(invite["list_id"])
    except ListError:
        return None, False
    if role_of(doc, user) is not None:
        return doc, False  # owner/member already: don't burn a single-use link
    if not invite.get("multi_use"):
        invite = await telegram_accounts.consume_token(token, "list_invite", "pending")
        if not invite:
            return None, False
    return await add_member(doc["_id"], user["_id"])


async def get_list_doc(list_id: str) -> dict:
    doc = await get_mongo_db().shopping_lists.find_one({"_id": list_id})
    if not doc:
        raise ListError("list_not_found", 404)
    return doc


async def _list_country(doc: dict) -> str:
    if doc.get("country") in ("ME", "UA"):
        return doc["country"]
    db = get_mongo_db()
    product_ids = [i["product_id"] for i in doc.get("items", [])]
    product = await db.products.find_one({"id": {"$in": product_ids}, "country": {"$in": ["ME", "UA"]}}, {"country": 1})
    country = product["country"] if product else "ME"
    await db.shopping_lists.update_one({"_id": doc["_id"]}, {"$set": {"country": country}})
    doc["country"] = country
    return country


async def resolve_list(doc: dict, lang: str = "ukr") -> dict:
    """The full list as the site and the bot show it: translated names,
    per-store prices aligned to `stores`, cheapest store, a cheapest total
    of what's still unchecked."""
    country = await _list_country(doc)
    stores = await get_stores_for_country(country)
    items = doc.get("items", [])

    docs = {}
    if items:
        try:
            cursor = get_mongo_db().products.find(
                {"id": {"$in": [i["product_id"] for i in items]}, "country": country}
            )
            async for product in cursor:
                docs[product["id"]] = product
        except Exception as e:
            logger.warning(f"Failed to resolve list item prices: {e}")

    resolved = []
    for item in items:
        product = docs.get(item["product_id"])
        prices = list(product.get("prices") or []) if product else []
        prices = (prices + [None] * len(stores))[: len(stores)]
        min_price, cheapest_idx = calculate_cheapest(prices)
        resolved.append({
            "product_id": item["product_id"],
            "name": resolve_display_name(product, lang) if product else item.get("name", ""),
            "unit": item.get("unit", "") or (product.get("unit", "") if product else ""),
            "checked": item.get("checked", False),
            "prices": prices,
            "min_price": min_price,
            "cheapest_store": stores[cheapest_idx]["name"] if cheapest_idx >= 0 else None,
        })

    total = sum(i["min_price"] for i in resolved if not i["checked"] and i["min_price"] is not None)
    return {
        "id": doc["_id"],
        "name": doc.get("name"),
        "saved": doc.get("owner_user_id") is not None,
        "owner_user_id": doc.get("owner_user_id"),
        "country": country,
        "stores": stores,
        "items": resolved,
        "total_cheapest": round(total, 2),
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat(),
    }


async def gold_list_limit() -> int:
    return int((await get_plan_settings())["gold_list_limit"])


async def assert_under_limit(user_id: str, excluding_list_id: Optional[str] = None) -> None:
    query: dict = {"owner_user_id": user_id}
    if excluding_list_id:
        query["_id"] = {"$ne": excluding_list_id}
    count = await get_mongo_db().shopping_lists.count_documents(query)
    if count >= await gold_list_limit():
        raise ListError("list_limit_reached", 403)


async def create_list(
    owner_user_id: Optional[str],
    items: list[dict],
    country: str,
    *,
    session_id: Optional[str] = None,
    name: Optional[str] = None,
) -> dict:
    await ensure_indexes()
    if owner_user_id:
        await assert_under_limit(owner_user_id)
    now = datetime.utcnow()
    doc = {
        "_id": uuid.uuid4().hex,
        "name": name,
        "country": country,
        "items": [
            {"product_id": i["product_id"], "name": i.get("name", ""), "unit": i.get("unit", ""), "checked": False}
            for i in items
        ],
        "owner_session_id": session_id,
        "owner_user_id": owner_user_id,
        "created_at": now,
        "updated_at": now,
    }
    await get_mongo_db().shopping_lists.insert_one(doc)
    return doc


async def _save_items(doc: dict, items: list[dict]) -> dict:
    now = datetime.utcnow()
    await get_mongo_db().shopping_lists.update_one({"_id": doc["_id"]}, {"$set": {"items": items, "updated_at": now}})
    return {**doc, "items": items, "updated_at": now}


async def toggle_item(list_id: str, *, product_id: Optional[str] = None, index: Optional[int] = None) -> dict:
    doc = await get_list_doc(list_id)
    items = doc["items"]
    if index is not None:
        if not 0 <= index < len(items):
            raise ListError("item_not_found", 404)
        target = items[index]
    else:
        target = next((i for i in items if i["product_id"] == product_id), None)
        if target is None:
            raise ListError("item_not_found", 404)
    target["checked"] = not target.get("checked", False)
    return await _save_items(doc, items)


async def add_item(list_id: str, product_id: str, name: str = "", unit: str = "") -> tuple[dict, bool]:
    """Returns (doc, added) - `added` False if it was already on the list."""
    doc = await get_list_doc(list_id)
    if any(i["product_id"] == product_id for i in doc["items"]):
        return doc, False
    items = doc["items"] + [{"product_id": product_id, "name": name, "unit": unit, "checked": False}]
    return await _save_items(doc, items), True


async def add_items(list_id: str, new_items: list[dict]) -> dict:
    doc = await get_list_doc(list_id)
    have = {i["product_id"] for i in doc["items"]}
    items = list(doc["items"])
    for item in new_items:
        if item["product_id"] not in have:
            have.add(item["product_id"])
            items.append({"product_id": item["product_id"], "name": item.get("name", ""), "unit": item.get("unit", ""), "checked": False})
    return await _save_items(doc, items)


async def remove_item(list_id: str, product_id: str) -> dict:
    doc = await get_list_doc(list_id)
    return await _save_items(doc, [i for i in doc["items"] if i["product_id"] != product_id])


async def save_list(list_id: str, user_id: str, name: str) -> dict:
    doc = await get_list_doc(list_id)
    if doc.get("owner_user_id") not in (None, user_id):
        raise ListError("list_owned_by_other", 403)
    if doc.get("owner_user_id") is None:
        await assert_under_limit(user_id)
    now = datetime.utcnow()
    await get_mongo_db().shopping_lists.update_one(
        {"_id": list_id}, {"$set": {"owner_user_id": user_id, "name": name, "updated_at": now}}
    )
    return {**doc, "owner_user_id": user_id, "name": name, "updated_at": now}


async def owned_lists(user_id: str, limit: int = 100) -> list[dict]:
    cursor = get_mongo_db().shopping_lists.find({"owner_user_id": user_id}).sort("updated_at", -1)
    return await cursor.to_list(length=limit)


async def accessible_lists(user_id: str, limit: int = 100) -> list[dict]:
    """Own lists and lists shared with the user, most recently touched first."""
    cursor = get_mongo_db().shopping_lists.find(
        {"$or": [{"owner_user_id": user_id}, {"member_user_ids": user_id}]}
    ).sort("updated_at", -1)
    return await cursor.to_list(length=limit)


async def set_active_list(user: dict, list_id: str) -> None:
    await get_mongo_db().users.update_one({"_id": user["_id"]}, {"$set": {"active_list_id": list_id}})
    user["active_list_id"] = list_id


async def active_list_for(user: dict, country: str, default_name: Optional[str] = None) -> Optional[dict]:
    """The bot's "add to list" target for a search in `country`: the list
    last opened in the bot (own or shared), else the most recently touched
    editable one, else - with Gold and `default_name` given - a new list.
    None if the user has nowhere to add to."""
    db = get_mongo_db()
    active_id = user.get("active_list_id")
    if active_id:
        doc = await db.shopping_lists.find_one({"_id": active_id, "country": country})
        if doc and await can_edit(doc, user):
            return doc
    cursor = db.shopping_lists.find(
        {"country": country, "$or": [{"owner_user_id": user["_id"]}, {"member_user_ids": user["_id"]}]}
    ).sort("updated_at", -1)
    async for doc in cursor:
        if await can_edit(doc, user):
            return doc
    if default_name and can_use_lists(user):
        return await create_list(user["_id"], [], country, name=default_name)
    return None
