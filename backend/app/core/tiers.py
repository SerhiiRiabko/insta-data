"""User tier -> saved-list limits (Phase 4.2), now admin-editable (Phase 4.4).

`DEFAULT_TIER_LIMITS` is the fallback used until an admin ever saves
anything - once `db.settings` has a `tier_limits` document, that value wins.
Keeping a hardcoded fallback (rather than requiring the doc to exist) means
the app works out of the box on a fresh database, same as MOCK_STORES
elsewhere in this codebase.
"""

from app.database.mongodb import get_mongo_db

DEFAULT_TIER_LIMITS = {
    "free": 3,
    "simple": 10,
    "pro": 100,
}

DEFAULT_TIER = "free"

_SETTINGS_ID = "tier_limits"


async def get_tier_limits() -> dict:
    db = get_mongo_db()
    doc = await db.settings.find_one({"_id": _SETTINGS_ID})
    if not doc:
        return dict(DEFAULT_TIER_LIMITS)
    return {tier: doc.get(tier, DEFAULT_TIER_LIMITS[tier]) for tier in DEFAULT_TIER_LIMITS}


async def set_tier_limits(limits: dict) -> dict:
    db = get_mongo_db()
    update = {tier: int(limits[tier]) for tier in DEFAULT_TIER_LIMITS if tier in limits}
    await db.settings.update_one({"_id": _SETTINGS_ID}, {"$set": update}, upsert=True)
    return await get_tier_limits()