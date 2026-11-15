"""Auth — three ways in, one `users` document per person:

- email + password
- passwordless magic link (email with a one-time link)
- Telegram: the site opens t.me/<bot>?start=login_<token>, the user confirms
  in the bot, the waiting browser polls /auth/telegram/login/{token} and gets
  the session cookie. The bot can also hand out a one-time web-login URL
  (/auth/telegram/web) for users who started in Telegram.

Accounts that started in the bot have no email; they can add email+password
later (POST /auth/credentials). An email account links Telegram via
POST /auth/telegram/link. See app/services/telegram_accounts.py.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.database.mongodb import get_mongo_db
from app.services import telegram_accounts
from app.services.auth_service import (
    create_session_token,
    get_current_user,
    get_or_create_user_by_email,
    get_user_by_email,
    hash_password,
    verify_password,
)
from app.services.email_service import send_magic_link_email
from app.services.subscription_service import PAID_PLANS, access_payload, apply_pending_grants
from app.services.telegram_accounts import LinkError
from app.services.telegram_api import bot_link

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "access_token"
MAGIC_LINK_TTL_SECONDS = 15 * 60


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MagicLinkRequest(BaseModel):
    email: EmailStr
    lang: str = "ukr"


class TelegramLinkRequest(BaseModel):
    # Optional purchase intent: after linking, the bot offers the Stars
    # invoice for this plan straight away.
    plan: Optional[str] = None


class TelegramLoginRequest(BaseModel):
    lang: str = "ukr"


def public_user(user: dict) -> dict:
    return {
        "id": user["_id"],
        "email": user.get("email"),
        "is_admin": user.get("is_admin", False),
        "has_password": bool(user.get("password_hash")),
        "telegram": (
            {"id": user["telegram_id"], "username": user.get("telegram_username"), "first_name": user.get("telegram_first_name")}
            if user.get("telegram_id") else None
        ),
        "access": access_payload(user),
    }


def _set_session_cookie(response: Response, user: dict) -> None:
    token = create_session_token(user["_id"], user.get("email"))
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.session_expire_days * 24 * 3600,
        path="/",
    )


async def _ensure_indexes():
    await telegram_accounts.ensure_indexes()
    await get_mongo_db().login_tokens.create_index("expires_at", expireAfterSeconds=0, name="ttl_expires_at")


@router.post("/register")
async def register(payload: RegisterRequest, response: Response):
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    await _ensure_indexes()
    db = get_mongo_db()
    email = payload.email.lower().strip()

    if await get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = {
        "_id": uuid.uuid4().hex,
        "email": email,
        "password_hash": hash_password(payload.password),
        "is_admin": False,
        "created_at": datetime.utcnow(),
    }
    await db.users.insert_one(user)
    user = await apply_pending_grants(user)
    _set_session_cookie(response, user)
    return public_user(user)


@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    user = await get_user_by_email(payload.email)
    if not user or not user.get("password_hash") or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    _set_session_cookie(response, user)
    return public_user(user)


@router.post("/credentials")
async def set_credentials(payload: RegisterRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """Adds email+password to an account that started in the Telegram bot,
    so it can also log in without Telegram."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if current_user.get("email"):
        raise HTTPException(status_code=400, detail="email_already_set")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    email = payload.email.lower().strip()
    if await get_user_by_email(email):
        # Someone with that email exists: they should log in with it and
        # connect Telegram from there (that merges the two accounts).
        raise HTTPException(status_code=409, detail="email_taken_link_from_it")

    db = get_mongo_db()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"email": email, "password_hash": hash_password(payload.password)}},
    )
    user = await apply_pending_grants(await db.users.find_one({"_id": current_user["_id"]}))
    return public_user(user)


@router.post("/magic-link/request")
async def request_magic_link(payload: MagicLinkRequest):
    await _ensure_indexes()
    db = get_mongo_db()

    token = uuid.uuid4().hex
    await db.login_tokens.insert_one({
        "_id": token,
        "email": payload.email.lower().strip(),
        "lang": payload.lang,
        "expires_at": datetime.utcnow() + timedelta(seconds=MAGIC_LINK_TTL_SECONDS),
        "used": False,
    })

    # Points straight at the backend - cookies are host-scoped (not
    # port-scoped), so a cookie set here on `localhost` is sent along with
    # any later fetch() from the frontend on localhost:3001 too, as long as
    # axios uses withCredentials (see frontend/src/lib/api.ts).
    link = f"{settings.backend_url.rstrip('/')}/api/v1/auth/magic-link/verify?token={token}"
    send_magic_link_email(payload.email, link)

    # Always the same response whether or not the email exists yet (magic
    # link doubles as signup) - no point leaking which emails are registered.
    return {"message": "If that email is valid, a login link was sent."}


@router.get("/magic-link/verify")
async def verify_magic_link(token: str):
    """Opened directly from the email link in a real browser tab, so this
    redirects to the landing page (not JSON), with the session cookie set on
    the redirect response itself - mutating an injected `Response`
    dependency has no effect once a different Response object (this
    RedirectResponse) is what actually gets returned."""
    db = get_mongo_db()
    doc = await db.login_tokens.find_one({"_id": token})
    if not doc or doc["used"] or doc["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Link is invalid or expired")

    await db.login_tokens.update_one({"_id": token}, {"$set": {"used": True}})
    user = await get_or_create_user_by_email(doc["email"])

    lang = doc.get("lang", "ukr")
    redirect = RedirectResponse(url=f"{settings.frontend_url.rstrip('/')}/{lang}?authed=1")
    _set_session_cookie(redirect, user)
    return redirect


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

@router.post("/telegram/link")
async def telegram_link(payload: TelegramLinkRequest, current_user: Optional[dict] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    plan = payload.plan if payload.plan in PAID_PLANS else None
    await _ensure_indexes()
    token = await telegram_accounts.create_token("link", user_id=current_user["_id"], plan=plan)
    return {"url": bot_link(f"link_{token}"), "token": token}


@router.get("/telegram/link/{token}")
async def telegram_link_status(token: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Polled by the site while the user confirms in the bot."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    doc = await telegram_accounts.get_token(token, "link")
    if not doc or doc.get("user_id") != current_user["_id"]:
        raise HTTPException(status_code=410, detail="token_expired")
    # "confirmed" = tapped in the bot, link still being written; the bot
    # moves it to "linked" (or "failed") once done.
    if doc["status"] in ("pending", "confirmed"):
        return {"status": "pending"}
    if doc["status"] == "failed":
        return {"status": "failed", "error": doc.get("error")}
    user = await get_mongo_db().users.find_one({"_id": current_user["_id"]})
    return {"status": "linked", "user": public_user(user)}


@router.delete("/telegram")
async def telegram_unlink(current_user: Optional[dict] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        await telegram_accounts.unlink_telegram(current_user["_id"])
    except LinkError as e:
        raise HTTPException(status_code=400, detail=e.code)
    user = await get_mongo_db().users.find_one({"_id": current_user["_id"]})
    return public_user(user)


@router.post("/telegram/login")
async def telegram_login(payload: TelegramLoginRequest, request: Request):
    await _ensure_indexes()
    token = await telegram_accounts.create_token(
        "login",
        lang=payload.lang,
        requester_ip=request.client.host if request.client else None,
        requester_ua=(request.headers.get("user-agent") or "")[:200],
    )
    return {"url": bot_link(f"login_{token}"), "token": token}


@router.get("/telegram/login/{token}")
async def telegram_login_status(token: str, response: Response):
    """Polled by the browser that started the login. Once the user has
    confirmed in the bot, the first poll consumes the token (single use) and
    gets the session cookie."""
    doc = await telegram_accounts.get_token(token, "login")
    if not doc or doc["status"] == "used":
        raise HTTPException(status_code=410, detail="token_expired")
    if doc["status"] == "pending":
        return {"status": "pending"}

    consumed = await telegram_accounts.consume_token(token, "login", from_status="confirmed")
    if not consumed:
        raise HTTPException(status_code=410, detail="token_expired")
    user = await get_mongo_db().users.find_one({"_id": consumed["user_id"]})
    if not user:
        raise HTTPException(status_code=410, detail="token_expired")
    _set_session_cookie(response, user)
    return {"status": "ok", "user": public_user(user)}


@router.get("/telegram/web")
async def telegram_web_login(token: str, lang: str = "ukr"):
    """One-time URL the bot sends (/site) - opening it logs that Telegram
    user into the website."""
    doc = await telegram_accounts.consume_token(token, "web_login", from_status="pending")
    if not doc:
        raise HTTPException(status_code=400, detail="Link is invalid or expired")
    user = await get_mongo_db().users.find_one({"_id": doc["user_id"]})
    if not user:
        raise HTTPException(status_code=400, detail="Link is invalid or expired")
    redirect = RedirectResponse(url=f"{settings.frontend_url.rstrip('/')}/{doc.get('lang') or lang}?authed=1")
    _set_session_cookie(redirect, user)
    return redirect


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "Logged out"}


@router.get("/me")
async def me(current_user: dict | None = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return public_user(current_user)
