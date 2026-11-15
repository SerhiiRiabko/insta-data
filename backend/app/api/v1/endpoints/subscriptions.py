"""Buying a plan from the website.

- Telegram Stars: needs a linked Telegram account; returns a Stars
  subscription invoice link (t.me/$...) that opens the payment sheet in
  Telegram. The bot process receives the payment and grants the plan.
- Card transfer: shows the admin-configured transfer details; "I've paid"
  creates a pending request, the admin approves/declines in the bot or the
  admin panel.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.database.mongodb import get_mongo_db
from app.services import telegram_api
from app.services.auth_service import get_current_user
from app.services.payment_notifications import notify_admins_new_request
from app.services.subscription_service import (
    PAID_PLANS,
    STARS_SUBSCRIPTION_PERIOD_SECONDS,
    access_payload,
    create_payment_request,
    get_plan_settings,
    stars_invoice_payload,
)
from app.services.telegram_texts import plan_name, t

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class PlanRequest(BaseModel):
    plan: str
    lang: str = "ukr"


class CardRequest(BaseModel):
    plan: str
    comment: str = ""


def _require_user(user: Optional[dict]) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def _check_plan(plan: str) -> None:
    if plan not in PAID_PLANS:
        raise HTTPException(status_code=400, detail="Unknown plan")


@router.get("/plans")
async def plans():
    s = await get_plan_settings()
    return {
        "plans": [
            {"id": "compare", "stars": s["compare_stars"], "eur": s["compare_eur"]},
            {"id": "gold", "stars": s["gold_stars"], "eur": s["gold_eur"]},
        ],
        "card_available": bool(s["card_details"]),
        "card_details": s["card_details"],
        "bot_username": settings.telegram_bot_username,
        "bot_url": telegram_api.bot_link(),
    }


@router.get("/me")
async def my_subscription(current_user: Optional[dict] = Depends(get_current_user)):
    user = _require_user(current_user)
    pending = await get_mongo_db().payment_requests.find(
        {"user_id": user["_id"], "status": "pending"}
    ).to_list(length=10)
    return {
        "access": access_payload(user),
        "pending_requests": [{"id": r["_id"], "plan": r["plan"], "amount_eur": r["amount_eur"]} for r in pending],
    }


@router.post("/stars-invoice")
async def stars_invoice(payload: PlanRequest, current_user: Optional[dict] = Depends(get_current_user)):
    user = _require_user(current_user)
    _check_plan(payload.plan)
    if not user.get("telegram_id"):
        raise HTTPException(status_code=409, detail="telegram_not_linked")

    s = await get_plan_settings()
    title = f"Shop Price Online · {plan_name(payload.lang, payload.plan)}"
    url = await telegram_api.create_stars_subscription_link(
        title=title,
        description=t(payload.lang, "invoice_description", plan=plan_name(payload.lang, payload.plan)),
        payload=stars_invoice_payload(payload.plan, user["_id"]),
        stars=s[f"{payload.plan}_stars"],
        period_seconds=STARS_SUBSCRIPTION_PERIOD_SECONDS,
    )
    if not url:
        raise HTTPException(status_code=502, detail="telegram_unavailable")
    return {"url": url}


@router.post("/card-request")
async def card_request(payload: CardRequest, current_user: Optional[dict] = Depends(get_current_user)):
    user = _require_user(current_user)
    _check_plan(payload.plan)
    s = await get_plan_settings()
    if not s["card_details"]:
        raise HTTPException(status_code=400, detail="card_unavailable")

    request, created = await create_payment_request(user["_id"], payload.plan, s[f"{payload.plan}_eur"], payload.comment)
    if created:
        await notify_admins_new_request(request)
    return {"id": request["_id"], "status": request["status"], "created": created}
