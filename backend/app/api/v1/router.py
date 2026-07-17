"""API v1 router - includes all endpoints"""

import logging

from fastapi import APIRouter
from app.api.v1.endpoints import search, products, test_scrapers, lists, auth, stores, admin, scraper_agents

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Include routers
api_router.include_router(products.router)  # Frontend integration (Phase 1)
api_router.include_router(search.router)
api_router.include_router(test_scrapers.router)  # Phase 3 testing
api_router.include_router(lists.router)  # Shopping lists (Phase 4.1)
api_router.include_router(auth.router)  # Accounts (Phase 4.2)
api_router.include_router(stores.router)  # Stores (Phase 4.3)
api_router.include_router(admin.router)  # Admin panel (Phase 4.4)
api_router.include_router(scraper_agents.router)  # Scraper agents (Phase 4.5)

# The Instagram router (and the legacy scrapers router, which pulls in the
# same chain via app.services.orchestrator) need instagrapi, which pins
# pydantic 1.x and conflicts with the pydantic v2 stack the rest of this app
# runs on - keep them optional so the app still boots without it installed.
try:
    from app.api.v1.endpoints import instagram
    api_router.include_router(instagram.router)
except ImportError as e:
    logger.warning(f"Instagram router unavailable: {e}")

try:
    from app.api.v1.endpoints import scrapers
    api_router.include_router(scrapers.router)
except ImportError as e:
    logger.warning(f"Legacy scrapers router unavailable: {e}")


@api_router.get("/status")
async def api_status():
    """API status endpoint"""
    return {"status": "ok", "version": "0.1.0"}