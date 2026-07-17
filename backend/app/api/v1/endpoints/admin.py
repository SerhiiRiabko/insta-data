"""Admin panel API (Phase 4.4) — tier limits + user tier assignment.
Stores CRUD lives in stores.py (same require_admin gate); scraper-agent
management (Phase 4.5) and About-page content editing (future phase) will
get their own modules here as those land - see PHASE_4_PLAN.md. Product
translation endpoints (Phase 4.6) live at the bottom of this file.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.tiers import DEFAULT_TIER_LIMITS, get_tier_limits, set_tier_limits
from app.database.mongodb import get_mongo_db
from app.services.auth_service import require_admin
from app.services.translation_service import SUPPORTED_LOCALES, translate_to_all_locales

router = APIRouter(prefix="/admin", tags=["admin"])


class TierLimitsIn(BaseModel):
    free: int
    simple: int
    pro: int


@router.get("/tiers")
async def get_tiers(_admin: dict = Depends(require_admin)):
    return await get_tier_limits()


@router.put("/tiers")
async def update_tiers(payload: TierLimitsIn, _admin: dict = Depends(require_admin)):
    for tier, value in payload.model_dump().items():
        if value < 1:
            raise HTTPException(status_code=400, detail=f"{tier} limit must be at least 1")
    return await set_tier_limits(payload.model_dump())


@router.get("/tiers/defaults")
async def get_tier_defaults(_admin: dict = Depends(require_admin)):
    return DEFAULT_TIER_LIMITS


@router.get("/users")
async def list_users(_admin: dict = Depends(require_admin)):
    db = get_mongo_db()
    docs = await db.users.find({}).sort("created_at", -1).to_list(length=500)
    return {
        "users": [
            {
                "id": d["_id"],
                "email": d["email"],
                "tier": d.get("tier", "free"),
                "is_admin": d.get("is_admin", False),
                "created_at": d["created_at"].isoformat(),
            }
            for d in docs
        ]
    }


class SetTierRequest(BaseModel):
    tier: str


@router.put("/users/{user_id}/tier")
async def set_user_tier(user_id: str, payload: SetTierRequest, _admin: dict = Depends(require_admin)):
    if payload.tier not in DEFAULT_TIER_LIMITS:
        raise HTTPException(status_code=400, detail=f"Unknown tier: {payload.tier}")
    db = get_mongo_db()
    result = await db.users.update_one({"_id": user_id}, {"$set": {"tier": payload.tier}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Tier updated"}


# ============================================================================
# Product translations (Phase 4.6) — `name_i18n` per product. Two paths:
# manual (admin types translations in directly) and AI-assisted (Groq, if
# `settings.groq_api_key` is set — see translation_service.py). Either way
# products.py's read endpoints resolve `name_i18n[locale]`, falling back to
# the original scraped name when a locale hasn't been translated yet.
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
    """AI-translates one product's name into every supported locale via
    Groq and persists the result. Requires `groq_api_key` to be configured —
    returns an empty `name_i18n` (not an error) if it isn't, since that's a
    valid, documented fallback state."""
    db = get_mongo_db()
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    name_i18n = await translate_to_all_locales(product["name"])
    if name_i18n:
        await db.products.update_one(
            {"id": product_id}, {"$set": {"name_i18n": name_i18n}}
        )
    return {"name_i18n": name_i18n}


@router.post("/products/translate-missing")
async def translate_missing_products(limit: int = 20, _admin: dict = Depends(require_admin)):
    """Bulk-translates up to `limit` products that have no `name_i18n` yet.
    Capped by default to keep a single admin click's AI cost/time bounded -
    call again to translate the next batch."""
    db = get_mongo_db()
    cursor = db.products.find(
        {"$or": [{"name_i18n": {"$exists": False}}, {"name_i18n": {}}]}
    ).limit(limit)
    products = await cursor.to_list(length=limit)

    translated_count = 0
    for product in products:
        name_i18n = await translate_to_all_locales(product["name"])
        if name_i18n:
            await db.products.update_one(
                {"id": product["id"]}, {"$set": {"name_i18n": name_i18n}}
            )
            translated_count += 1

    return {"checked": len(products), "translated": translated_count}