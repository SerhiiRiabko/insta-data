"""Shopping-list core shared by the web API (endpoints/lists.py) and the
Telegram bot, so both read/write the exact same documents.

A list belongs to one country: its prices are resolved against that
country's stores (`get_stores_for_country`), in the same column order the
price matrix uses. Lists created before the `country` field existed get it
inferred from their products the first time they're read.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from app.api.v1.endpoints.products import calculate_cheapest, get_stores_for_country
from app.database.mongodb import get_mongo_db
from app.services.subscription_service import get_plan_settings
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


async def active_list_for(user_id: str, country: str, default_name: str) -> dict:
    """The bot's "add to list" target: the owner's most recently touched
    list for this country, or a new one."""
    doc = await get_mongo_db().shopping_lists.find_one(
        {"owner_user_id": user_id, "country": country}, sort=[("updated_at", -1)]
    )
    if doc:
        return doc
    return await create_list(user_id, [], country, name=default_name)
