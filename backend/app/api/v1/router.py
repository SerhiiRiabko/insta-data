"""API v1 router - includes all endpoints"""

from fastapi import APIRouter

# Import endpoint routers when created
# from app.api.v1.endpoints import prices, search, wishlist

api_router = APIRouter()

# Include routers
# api_router.include_router(prices.router, prefix="/prices", tags=["prices"])
# api_router.include_router(search.router, prefix="/search", tags=["search"])
# api_router.include_router(wishlist.router, prefix="/wishlist", tags=["wishlist"])


@api_router.get("/status")
async def api_status():
    """API status endpoint"""
    return {"status": "ok", "version": "0.1.0"}