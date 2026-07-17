"""Stores — the shops prices are pulled from (Phase 4.3).

`GET /` is public (drives the "Магазини" page). The rest is admin-only
(Phase 4.4): add/edit/deactivate a store. Deactivation is soft (an `active`
flag, not a delete) since a scraper config or historic prices may still
reference the store id.

Seeded on first run from the same 4 stores that were previously hardcoded
as MOCK_STORES in products.py/lists.py/the frontend - this collection is now
the source of truth for the public store list and admin editing, but the
price-matrix scraping/matching pipeline (cijene_scraper.py,
product_matcher.py) still keys off the store `name` string, unchanged - see
PHASE_4_PLAN.md Phase 4.3 for why that's deliberately out of scope here.
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database.mongodb import get_mongo_db
from app.services.auth_service import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stores", tags=["stores"])

SEED_STORES = [
    {"name": "Aroma", "initial": "A", "color": "#e11d48", "url": "https://aromamarketi.me/uvijek-svjeze/"},
    {"name": "Voli", "initial": "V", "color": "#2563eb", "url": "https://voli.me/"},
    {"name": "HDL", "initial": "H", "color": "#d97706", "url": "https://www.digitalniletak.me/hd-lakovic"},
    {"name": "IDEA", "initial": "I", "color": "#0891b2", "url": "https://www.idea.co.me/"},
]


class StoreIn(BaseModel):
    name: str
    initial: str
    color: str
    url: str
    active: bool = True


async def _ensure_seeded():
    db = get_mongo_db()
    if await db.stores.count_documents({}) > 0:
        return
    now = datetime.utcnow()
    await db.stores.insert_many([
        {"_id": uuid.uuid4().hex, **s, "active": True, "created_at": now, "updated_at": now}
        for s in SEED_STORES
    ])


def _store_response(doc: dict) -> dict:
    return {
        "id": doc["_id"],
        "name": doc["name"],
        "initial": doc["initial"],
        "color": doc["color"],
        "url": doc["url"],
        "active": doc.get("active", True),
    }


@router.get("")
async def list_stores(include_inactive: bool = False):
    await _ensure_seeded()
    db = get_mongo_db()
    query = {} if include_inactive else {"active": True}
    docs = await db.stores.find(query).sort("name", 1).to_list(length=200)
    return {"stores": [_store_response(d) for d in docs]}


@router.post("")
async def create_store(payload: StoreIn, _admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    now = datetime.utcnow()
    doc = {"_id": uuid.uuid4().hex, **payload.model_dump(), "created_at": now, "updated_at": now}
    await db.stores.insert_one(doc)
    return _store_response(doc)


@router.put("/{store_id}")
async def update_store(store_id: str, payload: StoreIn, _admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    result = await db.stores.update_one(
        {"_id": store_id},
        {"$set": {**payload.model_dump(), "updated_at": datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Store not found")
    doc = await db.stores.find_one({"_id": store_id})
    return _store_response(doc)


@router.delete("/{store_id}")
async def deactivate_store(store_id: str, _admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    result = await db.stores.update_one(
        {"_id": store_id}, {"$set": {"active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Store not found")
    return {"message": "Store deactivated"}