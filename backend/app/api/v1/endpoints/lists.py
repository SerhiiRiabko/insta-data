"""Shopping lists — Phase 4.1 (guest mode) + Phase 4.2 (accounts).

A list is created once (POST /), then viewed/shared via its id
(GET /{list_id}) - anyone with the link can toggle items off/on
(PATCH .../toggle), and the strike-through state is shared (persisted
server-side), matching the "Share List" flow in PHASE_4_PLAN.md Phase 4.1.

`owner_session_id` is a client-generated UUID (localStorage), not an
authenticated user. If the caller IS logged in when a list is created,
`owner_user_id` is set immediately (subject to their tier's list limit) and
the list is exempt from the guest TTL. A logged-in user can also "save" a
list that started as a guest list via POST /{list_id}/save (Phase 4.2).
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.tiers import get_tier_limits, DEFAULT_TIER
from app.database.mongodb import get_mongo_db
from app.api.v1.endpoints.products import MOCK_STORES, calculate_cheapest
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lists", tags=["lists"])

# Guest lists aren't meant to live forever - 30 days of inactivity (no view,
# no toggle) and Mongo's TTL monitor reaps the document. Saved lists
# (owner_user_id set) are excluded via partialFilterExpression - they live
# until the owner deletes them.
LIST_TTL_SECONDS = 30 * 24 * 60 * 60


class ListItemIn(BaseModel):
    product_id: str
    name: str
    unit: str = ""


class CreateListRequest(BaseModel):
    session_id: Optional[str] = None
    items: list[ListItemIn]


class ToggleItemRequest(BaseModel):
    product_id: str


class SaveListRequest(BaseModel):
    name: str


async def _tier_limit(user: dict) -> int:
    limits = await get_tier_limits()
    tier = user.get("tier", DEFAULT_TIER)
    return limits.get(tier, limits[DEFAULT_TIER])


async def _assert_under_tier_limit(user: dict, excluding_list_id: Optional[str] = None) -> None:
    db = get_mongo_db()
    query = {"owner_user_id": user["_id"]}
    if excluding_list_id:
        query["_id"] = {"$ne": excluding_list_id}
    count = await db.shopping_lists.count_documents(query)
    limit = await _tier_limit(user)
    if count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"List limit reached for your plan ({limit}). Upgrade to save more.",
        )


async def _ensure_indexes():
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


async def _resolve_items(items: list[dict]) -> list[dict]:
    """Attach current prices to each list item by looking up its product id
    in the persisted products cache - same MOCK_STORES-aligned shape the
    price matrix uses, so the list view can reuse formatPrice/withCheapest."""
    if not items:
        return []

    db = get_mongo_db()
    product_ids = [item["product_id"] for item in items]
    docs = {}
    try:
        cursor = db.products.find({"id": {"$in": product_ids}})
        async for doc in cursor:
            docs[doc["id"]] = doc
    except Exception as e:
        logger.warning(f"Failed to resolve list item prices: {e}")

    resolved = []
    for item in items:
        doc = docs.get(item["product_id"])
        if doc:
            prices = doc.get("prices")
            if prices is None:
                current_prices = doc.get("current_prices", {})
                prices = [current_prices.get(store["name"].lower()) for store in MOCK_STORES]
            min_price, cheapest_idx = calculate_cheapest(prices)
            cheapest_store = MOCK_STORES[cheapest_idx]["name"] if cheapest_idx >= 0 else None
        else:
            prices = [None] * len(MOCK_STORES)
            min_price, cheapest_store = None, None

        resolved.append({
            "product_id": item["product_id"],
            "name": item.get("name", ""),
            "unit": item.get("unit", ""),
            "checked": item.get("checked", False),
            "prices": prices,
            "min_price": min_price,
            "cheapest_store": cheapest_store,
        })
    return resolved


def _list_response(doc: dict, resolved_items: list[dict]) -> dict:
    return {
        "id": doc["_id"],
        "name": doc.get("name"),
        "saved": doc.get("owner_user_id") is not None,
        "items": resolved_items,
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat(),
    }


@router.post("")
async def create_list(payload: CreateListRequest, current_user: Optional[dict] = Depends(get_current_user)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="List must have at least one item")

    await _ensure_indexes()
    db = get_mongo_db()

    # If logged in, the list is owned (and counted against the tier limit)
    # from the start - a guest who logs in mid-session still goes through
    # POST /{list_id}/save for lists they built before logging in.
    if current_user:
        await _assert_under_tier_limit(current_user)

    now = datetime.utcnow()
    doc = {
        "_id": uuid.uuid4().hex,
        "name": None,
        "items": [{"product_id": i.product_id, "name": i.name, "unit": i.unit, "checked": False} for i in payload.items],
        "owner_session_id": payload.session_id,
        "owner_user_id": current_user["_id"] if current_user else None,
        "created_at": now,
        "updated_at": now,
    }
    await db.shopping_lists.insert_one(doc)

    resolved = await _resolve_items(doc["items"])
    return _list_response(doc, resolved)


@router.get("/mine")
async def my_lists(current_user: Optional[dict] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = get_mongo_db()
    limit = await _tier_limit(current_user)
    cursor = db.shopping_lists.find({"owner_user_id": current_user["_id"]}).sort("updated_at", -1)
    docs = await cursor.to_list(length=limit + 1)
    return {
        "lists": [
            {
                "id": doc["_id"],
                "name": doc.get("name"),
                "item_count": len(doc["items"]),
                "updated_at": doc["updated_at"].isoformat(),
            }
            for doc in docs
        ],
        "limit": limit,
        "tier": current_user.get("tier", DEFAULT_TIER),
    }


@router.post("/{list_id}/save")
async def save_list(list_id: str, payload: SaveListRequest, current_user: Optional[dict] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = get_mongo_db()
    doc = await db.shopping_lists.find_one({"_id": list_id})
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")

    already_owned_by_me = doc.get("owner_user_id") == current_user["_id"]
    if not already_owned_by_me:
        if doc.get("owner_user_id") is not None:
            raise HTTPException(status_code=403, detail="List already saved by another account")
        await _assert_under_tier_limit(current_user)

    now = datetime.utcnow()
    await db.shopping_lists.update_one(
        {"_id": list_id},
        {"$set": {"owner_user_id": current_user["_id"], "name": payload.name, "updated_at": now}},
    )
    doc.update({"owner_user_id": current_user["_id"], "name": payload.name, "updated_at": now})

    resolved = await _resolve_items(doc["items"])
    return _list_response(doc, resolved)


@router.get("/{list_id}")
async def get_list(list_id: str):
    db = get_mongo_db()
    doc = await db.shopping_lists.find_one({"_id": list_id})
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")

    resolved = await _resolve_items(doc["items"])
    return _list_response(doc, resolved)


@router.patch("/{list_id}/toggle")
async def toggle_item(list_id: str, payload: ToggleItemRequest):
    db = get_mongo_db()
    doc = await db.shopping_lists.find_one({"_id": list_id})
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")

    found = False
    for item in doc["items"]:
        if item["product_id"] == payload.product_id:
            item["checked"] = not item["checked"]
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Item not in list")

    now = datetime.utcnow()
    await db.shopping_lists.update_one(
        {"_id": list_id}, {"$set": {"items": doc["items"], "updated_at": now}}
    )

    resolved = await _resolve_items(doc["items"])
    return _list_response({**doc, "updated_at": now}, resolved)


@router.post("/{list_id}/items")
async def add_item(list_id: str, item: ListItemIn):
    db = get_mongo_db()
    doc = await db.shopping_lists.find_one({"_id": list_id})
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")

    if not any(i["product_id"] == item.product_id for i in doc["items"]):
        doc["items"].append({"product_id": item.product_id, "name": item.name, "unit": item.unit, "checked": False})
        now = datetime.utcnow()
        await db.shopping_lists.update_one(
            {"_id": list_id}, {"$set": {"items": doc["items"], "updated_at": now}}
        )
        doc["updated_at"] = now

    resolved = await _resolve_items(doc["items"])
    return _list_response(doc, resolved)


@router.delete("/{list_id}/items/{product_id}")
async def remove_item(list_id: str, product_id: str):
    db = get_mongo_db()
    doc = await db.shopping_lists.find_one({"_id": list_id})
    if not doc:
        raise HTTPException(status_code=404, detail="List not found")

    remaining = [i for i in doc["items"] if i["product_id"] != product_id]
    now = datetime.utcnow()
    await db.shopping_lists.update_one(
        {"_id": list_id}, {"$set": {"items": remaining, "updated_at": now}}
    )

    resolved = await _resolve_items(remaining)
    return _list_response({**doc, "items": remaining, "updated_at": now}, resolved)
