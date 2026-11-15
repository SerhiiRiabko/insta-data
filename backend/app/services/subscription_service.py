"""Paid plans — replaces the old free/simple/pro list-limit tiers.

Three effective plans, shared by the site and the Telegram bot (one account,
one subscription, wherever it was paid):

- free     — prices of ONE store at a time (site: store picker; bot: pick a
             store per query, the previous answer is removed).
- compare  — side-by-side comparison across every store of a country.
             300 ⭐ / 3 € per month.
- gold     — compare + shopping lists + sharing them. 900 ⭐ / 10 € per month.

A user document carries `compare_until` / `gold_until` (UTC datetimes). The
effective plan is the best one still in the future; site admins always get
gold. Paying again (renewal, admin approval of a second transfer) extends
from the current expiry rather than from today, so nobody loses days.

Prices, the card-transfer details shown to payers and the gold list limit
live in `db.settings` (`_id: "plan_settings"`), editable from the admin panel.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.database.mongodb import get_mongo_db

logger = logging.getLogger(__name__)

PLAN_FREE = "free"
PLAN_COMPARE = "compare"
PLAN_GOLD = "gold"
PAID_PLANS = (PLAN_COMPARE, PLAN_GOLD)

PLAN_PERIOD_DAYS = 30
# Telegram Stars subscriptions only support exactly 30 days.
STARS_SUBSCRIPTION_PERIOD_SECONDS = 30 * 24 * 3600
# Admin "forever" grants - a fixed far-future date keeps every comparison a
# plain datetime comparison (no None-means-forever special case).
FOREVER = datetime(2100, 1, 1)

DEFAULT_PLAN_SETTINGS = {
    "compare_stars": 300,
    "gold_stars": 900,
    "compare_eur": 3,
    "gold_eur": 10,
    "gold_list_limit": 100,
    # Free text shown to card payers (card number / IBAN / recipient name).
    # Empty until the admin fills it in - the card option is hidden until then.
    "card_details": "",
}

_SETTINGS_ID = "plan_settings"


async def get_plan_settings() -> dict:
    db = get_mongo_db()
    doc = await db.settings.find_one({"_id": _SETTINGS_ID}) or {}
    return {key: doc.get(key, default) for key, default in DEFAULT_PLAN_SETTINGS.items()}


async def set_plan_settings(update: dict) -> dict:
    clean = {}
    for key, default in DEFAULT_PLAN_SETTINGS.items():
        if key not in update or update[key] is None:
            continue
        clean[key] = str(update[key]).strip() if isinstance(default, str) else type(default)(update[key])
    if clean:
        await get_mongo_db().settings.update_one({"_id": _SETTINGS_ID}, {"$set": clean}, upsert=True)
    return await get_plan_settings()


def _until(user: dict, plan: str) -> Optional[datetime]:
    return user.get(f"{plan}_until")


def effective_plan(user: Optional[dict]) -> str:
    if not user:
        return PLAN_FREE
    if user.get("is_admin"):
        return PLAN_GOLD
    now = datetime.utcnow()
    for plan in (PLAN_GOLD, PLAN_COMPARE):
        until = _until(user, plan)
        if until and until > now:
            return plan
    return PLAN_FREE


def can_compare(user: Optional[dict]) -> bool:
    return effective_plan(user) in PAID_PLANS


def can_use_lists(user: Optional[dict]) -> bool:
    return effective_plan(user) == PLAN_GOLD


def plan_expires_at(user: Optional[dict]) -> Optional[datetime]:
    plan = effective_plan(user)
    if plan == PLAN_FREE or user.get("is_admin"):
        return None
    return _until(user, plan)


def access_payload(user: Optional[dict]) -> dict:
    """What the frontend/bot needs to decide what to show."""
    plan = effective_plan(user)
    expires = plan_expires_at(user)
    return {
        "plan": plan,
        "compare": plan in PAID_PLANS,
        "lists": plan == PLAN_GOLD,
        "expires_at": expires.isoformat() if expires and expires < FOREVER else None,
        "forever": bool(expires and expires >= FOREVER) or bool(user and user.get("is_admin")),
    }


async def grant_plan(
    user_id: str,
    plan: str,
    *,
    source: str,
    days: Optional[int] = PLAN_PERIOD_DAYS,
    until: Optional[datetime] = None,
    ref: Optional[str] = None,
) -> Optional[dict]:
    """Extends `plan` for a user. `until` (absolute) wins over `days`
    (relative to the later of now / current expiry); `days=None` with no
    `until` means forever. Returns the updated user doc, or None if missing."""
    if plan not in PAID_PLANS:
        raise ValueError(f"Unknown plan: {plan}")

    db = get_mongo_db()
    user = await db.users.find_one({"_id": user_id})
    if not user:
        return None

    now = datetime.utcnow()
    current = _until(user, plan)
    base = current if current and current > now else now
    if until is not None:
        new_until = max(until, current) if current else until
    elif days is None:
        new_until = FOREVER
    else:
        new_until = base + timedelta(days=days)

    await db.users.update_one({"_id": user_id}, {"$set": {f"{plan}_until": new_until}})
    await db.plan_events.insert_one({
        "_id": uuid.uuid4().hex,
        "user_id": user_id,
        "plan": plan,
        "action": "grant",
        "source": source,
        "ref": ref,
        "until": new_until,
        "created_at": now,
    })
    user[f"{plan}_until"] = new_until
    logger.info(f"Granted {plan} to {user_id} until {new_until} ({source})")
    return user


async def revoke_plan(user_id: str, plan: Optional[str] = None, *, source: str = "admin") -> Optional[dict]:
    db = get_mongo_db()
    plans = [plan] if plan else list(PAID_PLANS)
    result = await db.users.find_one_and_update(
        {"_id": user_id},
        {"$unset": {f"{p}_until": "" for p in plans}},
        return_document=True,
    )
    if result:
        await db.plan_events.insert_one({
            "_id": uuid.uuid4().hex,
            "user_id": user_id,
            "plan": plan or "all",
            "action": "revoke",
            "source": source,
            "created_at": datetime.utcnow(),
        })
    return result


async def queue_grant_for_email(email: str, plan: str, days: Optional[int], source: str = "admin") -> None:
    """Admin granted a plan to an email nobody has registered yet - applied
    on that email's first registration / login (apply_pending_grants)."""
    await get_mongo_db().pending_grants.insert_one({
        "_id": uuid.uuid4().hex,
        "email": email.lower().strip(),
        "plan": plan,
        "days": days,
        "source": source,
        "created_at": datetime.utcnow(),
    })


async def apply_pending_grants(user: dict) -> dict:
    email = user.get("email")
    if not email:
        return user
    db = get_mongo_db()
    async for grant in db.pending_grants.find({"email": email}):
        updated = await grant_plan(user["_id"], grant["plan"], source=grant["source"], days=grant["days"], ref=grant["_id"])
        await db.pending_grants.delete_one({"_id": grant["_id"]})
        user = updated or user
    return user


# ---------------------------------------------------------------------------
# Telegram Stars payments
# ---------------------------------------------------------------------------

def stars_invoice_payload(plan: str, user_id: str) -> str:
    return f"sub:{plan}:{user_id}"


def parse_stars_payload(payload: str) -> Optional[tuple[str, str]]:
    parts = (payload or "").split(":")
    if len(parts) == 3 and parts[0] == "sub" and parts[1] in PAID_PLANS and parts[2]:
        return parts[1], parts[2]
    return None


async def record_stars_payment(
    *,
    charge_id: str,
    payload: str,
    stars: int,
    payer_telegram_id: int,
    subscription_expiration_date: Optional[int],
    is_recurring: bool,
) -> Optional[dict]:
    """Applies a successful Stars payment (first payment or a monthly
    renewal - Telegram sends `successful_payment` for both). Idempotent per
    `charge_id`. Returns the updated user, or None if the payload is bad."""
    parsed = parse_stars_payload(payload)
    if not parsed:
        logger.warning(f"Stars payment {charge_id} with unknown payload {payload!r}")
        return None
    plan, user_id = parsed

    db = get_mongo_db()
    if await db.payments.find_one({"_id": charge_id}):
        return await db.users.find_one({"_id": user_id})

    await db.payments.insert_one({
        "_id": charge_id,
        "method": "stars",
        "user_id": user_id,
        "plan": plan,
        "stars": stars,
        "payer_telegram_id": payer_telegram_id,
        "is_recurring": is_recurring,
        "subscription_expiration_date": subscription_expiration_date,
        "created_at": datetime.utcnow(),
    })
    until = datetime.utcfromtimestamp(subscription_expiration_date) if subscription_expiration_date else None
    return await grant_plan(user_id, plan, source="stars", until=until, ref=charge_id)


# ---------------------------------------------------------------------------
# Card transfers — the payer sends money manually, an admin approves
# ---------------------------------------------------------------------------

async def create_payment_request(user_id: str, plan: str, amount_eur: float, comment: str = "") -> tuple[dict, bool]:
    """Returns (request, created). A second click while one is still
    pending returns the existing request instead of spamming the admin."""
    if plan not in PAID_PLANS:
        raise ValueError(f"Unknown plan: {plan}")
    db = get_mongo_db()
    existing = await db.payment_requests.find_one({"user_id": user_id, "plan": plan, "status": "pending"})
    if existing:
        return existing, False

    request = {
        "_id": uuid.uuid4().hex,
        "user_id": user_id,
        "plan": plan,
        "amount_eur": amount_eur,
        "comment": comment.strip()[:500],
        "status": "pending",
        "admin_messages": [],
        "created_at": datetime.utcnow(),
    }
    await db.payment_requests.insert_one(request)
    return request, True


async def decide_payment_request(request_id: str, approve: bool, admin_user_id: Optional[str]) -> Optional[dict]:
    """Approves (grants the plan for 30 days) or declines a pending request.
    Atomic on status, so two admins clicking at once can't double-grant.
    Returns the updated request, or None if it wasn't pending anymore."""
    db = get_mongo_db()
    request = await db.payment_requests.find_one_and_update(
        {"_id": request_id, "status": "pending"},
        {"$set": {
            "status": "approved" if approve else "declined",
            "decided_at": datetime.utcnow(),
            "decided_by": admin_user_id,
        }},
        return_document=True,
    )
    if request and approve:
        await grant_plan(request["user_id"], request["plan"], source="card", ref=request_id)
    return request
