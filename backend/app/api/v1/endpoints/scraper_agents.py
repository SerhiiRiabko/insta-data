"""Scraper agents (Phase 4.5) — admin visibility + manual trigger for the
active scraping pipeline (`app/services/scrapers/orchestrator.py`).

An "agent" is a configured scraper: which strategy runs it (`cijene`,
`instagram`, or `custom`), which store(s) in `db.stores` it produces prices
for, and its last-run status/timestamp/error. Seeded on first run from the
two scrapers the active `ScraperOrchestrator` already knows about — cijene.me
covers Aroma/Voli/HDL/IDEA in one scrape (it's a price-aggregator site, not
a per-store scraper), and the Instagram mock.

Running a `cijene`/`instagram` agent calls the real orchestrator and records
the result. Running a `custom` agent (the "add a new site" flow for a site
cijene.me doesn't cover) is intentionally NOT executable yet — per
PHASE_4_PLAN.md Phase 4.5, a genuinely new site layout needs a hand-written
scraper class registered in `orchestrator.py`'s `_register_scrapers()`; this
phase lets an admin record the config (name/url/store) ahead of that work,
not auto-generate a scraper.

Deliberately NOT touching the legacy `app/services/orchestrator.py` +
`endpoints/scrapers.py` chain (instagrapi-gated, already disabled — see
router.py's ImportError guard) or the weekly APScheduler job in `main.py` —
this module is additive admin visibility on top of the pipeline that's
actually running today.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database.mongodb import get_mongo_db
from app.services.auth_service import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scraper-agents", tags=["scraper-agents"])

KNOWN_STRATEGIES = {"cijene", "instagram", "custom"}
RUNNABLE_STRATEGIES = {"cijene", "instagram"}  # match orchestrator.py's registered keys

# Seeded against the store *names* already seeded by stores.py - resolved to
# real store ids the first time this module runs (stores.py's seed always
# runs first since every admin page loads stores too).
SEED_AGENTS = [
    {
        "name": "Cijene.me",
        "strategy": "cijene",
        "store_names": ["Aroma", "Voli", "HDL", "IDEA"],
        "url": "https://cijene.me",
    },
    {
        "name": "Instagram (mock)",
        "strategy": "instagram",
        "store_names": ["Aroma", "Voli", "HDL", "IDEA"],
        "url": None,
    },
]


class ScraperAgentIn(BaseModel):
    name: str
    strategy: str
    store_ids: List[str] = []
    url: Optional[str] = None
    active: bool = True


async def _ensure_seeded():
    db = get_mongo_db()
    if await db.scraper_agents.count_documents({}) > 0:
        return
    stores_by_name = {
        d["name"]: d["_id"] async for d in db.stores.find({}, {"name": 1})
    }
    now = datetime.utcnow()
    docs = []
    for seed in SEED_AGENTS:
        store_ids = [stores_by_name[n] for n in seed["store_names"] if n in stores_by_name]
        docs.append({
            "_id": uuid.uuid4().hex,
            "name": seed["name"],
            "strategy": seed["strategy"],
            "store_ids": store_ids,
            "url": seed["url"],
            "active": True,
            "last_run_at": None,
            "last_run_status": "never",
            "last_run_products_found": None,
            "last_run_error": None,
            "created_at": now,
            "updated_at": now,
        })
    if docs:
        await db.scraper_agents.insert_many(docs)


def _agent_response(doc: dict) -> dict:
    return {
        "id": doc["_id"],
        "name": doc["name"],
        "strategy": doc["strategy"],
        "store_ids": doc.get("store_ids", []),
        "url": doc.get("url"),
        "active": doc.get("active", True),
        "runnable": doc["strategy"] in RUNNABLE_STRATEGIES,
        "last_run_at": doc["last_run_at"].isoformat() if doc.get("last_run_at") else None,
        "last_run_status": doc.get("last_run_status", "never"),
        "last_run_products_found": doc.get("last_run_products_found"),
        "last_run_error": doc.get("last_run_error"),
    }


@router.get("")
async def list_scraper_agents(_admin: dict = Depends(require_admin)):
    await _ensure_seeded()
    db = get_mongo_db()
    docs = await db.scraper_agents.find({}).sort("name", 1).to_list(length=200)
    return {"agents": [_agent_response(d) for d in docs]}


@router.post("")
async def create_scraper_agent(payload: ScraperAgentIn, _admin: dict = Depends(require_admin)):
    if payload.strategy not in KNOWN_STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {payload.strategy}")
    db = get_mongo_db()
    now = datetime.utcnow()
    doc = {
        "_id": uuid.uuid4().hex,
        **payload.model_dump(),
        "last_run_at": None,
        "last_run_status": "never",
        "last_run_products_found": None,
        "last_run_error": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.scraper_agents.insert_one(doc)
    return _agent_response(doc)


@router.put("/{agent_id}")
async def update_scraper_agent(agent_id: str, payload: ScraperAgentIn, _admin: dict = Depends(require_admin)):
    if payload.strategy not in KNOWN_STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {payload.strategy}")
    db = get_mongo_db()
    result = await db.scraper_agents.update_one(
        {"_id": agent_id},
        {"$set": {**payload.model_dump(), "updated_at": datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Scraper agent not found")
    doc = await db.scraper_agents.find_one({"_id": agent_id})
    return _agent_response(doc)


@router.delete("/{agent_id}")
async def deactivate_scraper_agent(agent_id: str, _admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    result = await db.scraper_agents.update_one(
        {"_id": agent_id}, {"$set": {"active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Scraper agent not found")
    return {"message": "Scraper agent deactivated"}


@router.post("/{agent_id}/run")
async def run_scraper_agent(agent_id: str, _admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    doc = await db.scraper_agents.find_one({"_id": agent_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Scraper agent not found")

    strategy = doc["strategy"]
    now = datetime.utcnow()

    if strategy not in RUNNABLE_STRATEGIES:
        update = {
            "last_run_at": now,
            "last_run_status": "not_implemented",
            "last_run_products_found": None,
            "last_run_error": (
                "Custom scraper strategy has no runner yet - a genuinely new "
                "site layout needs a hand-written scraper class registered in "
                "orchestrator.py (see PHASE_4_PLAN.md Phase 4.5)."
            ),
            "updated_at": now,
        }
        await db.scraper_agents.update_one({"_id": agent_id}, {"$set": update})
        raise HTTPException(status_code=400, detail=update["last_run_error"])

    from app.services.scrapers.orchestrator import ScraperOrchestrator

    orchestrator = ScraperOrchestrator()
    result = await orchestrator.run_single(strategy)

    status = result.get("status", "failed")
    update = {
        "last_run_at": now,
        "last_run_status": status,
        "last_run_products_found": result.get("products"),
        "last_run_error": result.get("error"),
        "updated_at": now,
    }
    await db.scraper_agents.update_one({"_id": agent_id}, {"$set": update})

    doc.update(update)
    return {"agent": _agent_response(doc), "result": result}
