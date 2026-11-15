"""Admin panel API — plans/prices, users and their plans, card-transfer
requests, product translations. Stores CRUD lives in stores.py and scraper
agents in scraper_agents.py (same require_admin gate).

Replaces the Phase 4.4 free/simple/pro list-limit tiers: the paid plans
(compare / gold) and their prices are in app/services/subscription_service.py.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.database.mongodb import get_mongo_db
from app.services.auth_service import require_admin
from app.services.payment_notifications import describe_user, notify_request_decided
from app.services.subscription_service import (
    PAID_PLANS,
    FOREVER,
    access_payload,
    decide_payment_request,
    get_plan_settings,
    grant_plan,
    queue_grant_for_email,
    revoke_plan,
    set_plan_settings,
)
from app.services.telegram_accounts import find_user_by_identifier
from app.services.translation_service import SUPPORTED_LOCALES, translate_to_all_locales

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


def _iso(value: Optional[datetime]) -> Optional[str]:
    if not value:
        return None
    return "forever" if value >= FOREVER else value.isoformat()


# ---------------------------------------------------------------------------
# Plan settings
# ---------------------------------------------------------------------------

class PlanSettingsIn(BaseModel):
    compare_stars: Optional[int] = None
    gold_stars: Optional[int] = None
    compare_eur: Optional[float] = None
    gold_eur: Optional[float] = None
    gold_list_limit: Optional[int] = None
    card_details: Optional[str] = None


@router.get("/plan-settings")
async def plan_settings(_admin: dict = Depends(require_admin)):
    return await get_plan_settings()


@router.put("/plan-settings")
async def update_plan_settings(payload: PlanSettingsIn, _admin: dict = Depends(require_admin)):
    values = payload.model_dump(exclude_none=True)
    for key in ("compare_stars", "gold_stars", "gold_list_limit"):
        if key in values and values[key] < 1:
            raise HTTPException(status_code=400, detail=f"{key} must be at least 1")
    for key in ("compare_eur", "gold_eur"):
        if key in values and values[key] <= 0:
            raise HTTPException(status_code=400, detail=f"{key} must be positive")
    return await set_plan_settings(values)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def _admin_user_row(d: dict) -> dict:
    return {
        "id": d["_id"],
        "email": d.get("email"),
        "telegram_id": d.get("telegram_id"),
        "telegram_username": d.get("telegram_username"),
        "label": describe_user(d),
        "is_admin": d.get("is_admin", False),
        "access": access_payload(d),
        "compare_until": _iso(d.get("compare_until")),
        "gold_until": _iso(d.get("gold_until")),
        "created_at": d["created_at"].isoformat() if d.get("created_at") else None,
    }


@router.get("/users")
async def list_users(q: Optional[str] = None, _admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    query: dict = {}
    if q:
        needle = {"$regex": q.strip().lstrip("@"), "$options": "i"}
        query = {"$or": [{"email": needle}, {"telegram_username": needle}, {"telegram_first_name": needle}]}
    docs = await db.users.find(query).sort("created_at", -1).to_list(length=500)
    return {"users": [_admin_user_row(d) for d in docs]}


class GrantRequest(BaseModel):
    identifier: str  # email, @username or numeric Telegram id
    plan: str = "gold"
    months: Optional[int] = 1  # None = forever


@router.post("/users/grant")
async def grant(payload: GrantRequest, _admin: dict = Depends(require_admin)):
    if payload.plan not in PAID_PLANS:
        raise HTTPException(status_code=400, detail="Unknown plan")
    if payload.months is not None and payload.months < 1:
        raise HTTPException(status_code=400, detail="months must be at least 1")
    days = payload.months * 30 if payload.months else None

    user = await find_user_by_identifier(payload.identifier)
    if not user:
        identifier = payload.identifier.strip()
        if "@" in identifier and not identifier.startswith("@"):
            await queue_grant_for_email(identifier, payload.plan, days)
            return {"status": "queued", "message": "Цей email ще не зареєстрований — тариф застосується при першому вході."}
        raise HTTPException(
            status_code=404,
            detail="Користувача не знайдено. Telegram-користувач має хоч раз запустити бота.",
        )

    updated = await grant_plan(user["_id"], payload.plan, source="admin", days=days)
    return {"status": "granted", "user": _admin_user_row(updated)}


class RevokeRequest(BaseModel):
    plan: Optional[str] = None  # None = both


@router.post("/users/{user_id}/revoke")
async def revoke(user_id: str, payload: RevokeRequest, _admin: dict = Depends(require_admin)):
    if payload.plan is not None and payload.plan not in PAID_PLANS:
        raise HTTPException(status_code=400, detail="Unknown plan")
    user = await revoke_plan(user_id, payload.plan)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": _admin_user_row(user)}


# ---------------------------------------------------------------------------
# Card-transfer requests
# ---------------------------------------------------------------------------

@router.get("/payment-requests")
async def payment_requests(status: str = Query("pending"), _admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    query = {} if status == "all" else {"status": status}
    docs = await db.payment_requests.find(query).sort("created_at", -1).to_list(length=200)
    users = {u["_id"]: u async for u in db.users.find({"_id": {"$in": [d["user_id"] for d in docs]}})}
    return {
        "requests": [
            {
                "id": d["_id"],
                "user": describe_user(users[d["user_id"]]) if d["user_id"] in users else d["user_id"],
                "plan": d["plan"],
                "amount_eur": d["amount_eur"],
                "comment": d.get("comment", ""),
                "status": d["status"],
                "created_at": d["created_at"].isoformat(),
            }
            for d in docs
        ]
    }


@router.post("/payment-requests/{request_id}/{decision}")
async def decide(request_id: str, decision: str, admin: dict = Depends(require_admin)):
    if decision not in ("approve", "decline"):
        raise HTTPException(status_code=400, detail="decision must be approve or decline")
    request = await decide_payment_request(request_id, decision == "approve", admin["_id"])
    if not request:
        raise HTTPException(status_code=409, detail="Запит уже оброблено")
    await notify_request_decided(request)
    return {"status": request["status"]}


# ============================================================================
# Product translations (Phase 4.6) — `name_i18n` per product. Manual (admin
# types translations in) or AI (Groq, then Claude Haiku — see
# translation_service.py). products.py's read endpoints resolve
# `name_i18n[locale]`, falling back to the original scraped name.
# ============================================================================

class SetTranslationsRequest(BaseModel):
    name_i18n: dict[str, str]


@router.put("/products/{product_id}/translations")
async def set_product_translations(
    product_id: str, payload: SetTranslationsRequest, _admin: dict = Depends(require_admin)
):
    unknown = [loc for loc in payload.name_i18n if loc not in SUPPORTED_LOCALES]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown locale(s): {unknown}")
    db = get_mongo_db()
    result = await db.products.update_one(
        {"id": product_id}, {"$set": {"name_i18n": payload.name_i18n}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Translations updated"}


@router.post("/products/{product_id}/translate")
async def translate_product(product_id: str, _admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    name_i18n = await translate_to_all_locales(product["name"], product.get("country", "ME"))
    if name_i18n:
        await db.products.update_one(
            {"id": product_id}, {"$set": {f"name_i18n.{k}": v for k, v in name_i18n.items()}}
        )
    return {"name_i18n": name_i18n}


_translation_runs: dict[str, asyncio.Task] = {}


@router.post("/translations/fill")
async def fill_country_translations(country: str = Query(..., regex="^(ME|UA)$"), _admin: dict = Depends(require_admin)):
    """Starts a background pass that translates every still-untranslated
    product name of a country (cache -> dictionary -> Groq -> Claude Haiku)."""
    from app.services.translation_jobs import fill_translations

    running = _translation_runs.get(country)
    if running and not running.done():
        return {"status": "already_running"}
    _translation_runs[country] = asyncio.create_task(fill_translations(country))
    return {"status": "started"}


@router.get("/translations/status")
async def translation_status(_admin: dict = Depends(require_admin)):
    from app.services.translation_service import TRANSLATION_TARGETS

    db = get_mongo_db()
    result = {}
    for country, targets in TRANSLATION_TARGETS.items():
        total = await db.products.count_documents({"country": country})
        result[country] = {
            "total": total,
            "running": bool(_translation_runs.get(country) and not _translation_runs[country].done()),
            "translated": {
                loc: await db.products.count_documents({"country": country, f"name_i18n.{loc}": {"$exists": True, "$ne": ""}})
                for loc in targets
            },
        }
    return result
