"""Password hashing, session JWTs, and the current-user FastAPI dependencies
(Phase 4.2). The session token lives in an HttpOnly cookie - see
`COOKIE_NAME` / `set_session_cookie` in app/api/v1/endpoints/auth.py.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.tiers import DEFAULT_TIER
from app.database.mongodb import get_mongo_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_session_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.session_expire_days)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_session_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


async def get_user_by_email(email: str) -> Optional[dict]:
    db = get_mongo_db()
    return await db.users.find_one({"email": email.lower().strip()})


async def get_or_create_user_by_email(email: str) -> dict:
    """Used by magic-link verify - clicking the link is enough to both
    register (first time) and log in (every other time)."""
    db = get_mongo_db()
    email = email.lower().strip()
    user = await db.users.find_one({"email": email})
    if user:
        return user

    now = datetime.utcnow()
    user = {
        "_id": uuid.uuid4().hex,
        "email": email,
        "password_hash": None,
        "tier": DEFAULT_TIER,
        "is_admin": False,
        "created_at": now,
    }
    await db.users.insert_one(user)
    return user


async def get_current_user(request: Request) -> Optional[dict]:
    """Optional auth - returns None (not a 401) when there's no/invalid
    session, so the same dependency works for both guest and logged-in
    routes (e.g. list creation attaches an owner only if logged in)."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_session_token(token)
    if not payload:
        return None
    db = get_mongo_db()
    return await db.users.find_one({"_id": payload["sub"]})


async def require_admin(request: Request) -> dict:
    """Hard auth (401/403, not optional) for the admin panel (Phase 4.4).
    There's no admin UI to promote the first admin - see
    scripts/bootstrap_admin.py, which is the one-time chicken-and-egg step
    run outside the app."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user