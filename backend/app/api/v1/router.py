"""API v1 router - includes all endpoints"""

from fastapi import APIRouter
from app.api.v1.endpoints import instagram, scrapers, search, products, test_scrapers

api_router = APIRouter()

# Include routers
api_router.include_router(products.router)  # Frontend integration (Phase 1)
api_router.include_router(search.router)
api_router.include_router(instagram.router)
api_router.include_router(scrapers.router)
api_router.include_router(test_scrapers.router)  # Phase 3 testing


@api_router.get("/status")
async def api_status():
    """API status endpoint"""
    return {"status": "ok", "version": "0.1.0"}