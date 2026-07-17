"""Auth — Phase 4.2. Two login methods, user's choice: email+password, or a
passwordless magic link (email with a one-time link). Both end up at the
same place: a `users` document with a `tier` field (free/simple/pro, see
app/core/tiers.py) and an HttpOnly session cookie.
"""

import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.tiers import DEFAULT_TIER
from app.database.mongodb import get_mongo_db
from app.services.auth_service import (
    create_session_token,
    get_current_user,
    get_or_create_user_by_email,
    get_user_by_email,
    hash_password,
    verify_password,
)
from app.services.email_service import send_magic_link_email

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


def _public_user(user: dict) -> dict:
    return {
        "id": user["_id"],
        "email": user["email"],
        "tier": user.get("tier", DEFAULT_TIER),
        "is_admin": user.get("is_admin", False),
    }


def _set_session_cookie(response: Response, user: dict) -> None:
    token = create_session_token(user["_id"], user["email"])
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
    db = get_mongo_db()
    await db.users.create_index("email", unique=True, name="email_unique")
    await db.login_tokens.create_index(
        "expires_at", expireAfterSeconds=0, name="ttl_expires_at"
    )


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
        "tier": DEFAULT_TIER,
        "is_admin": False,
        "created_at": datetime.utcnow(),
    }
    await db.users.insert_one(user)
    _set_session_cookie(response, user)
    return _public_user(user)


@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    user = await get_user_by_email(payload.email)
    if not user or not user.get("password_hash") or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    _set_session_cookie(response, user)
    return _public_user(user)


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


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "Logged out"}


@router.get("/me")
async def me(current_user: dict | None = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _public_user(current_user)