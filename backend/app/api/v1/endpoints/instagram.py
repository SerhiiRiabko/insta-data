"""Instagram scraper API endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from app.services.instagram_auth import InstagramSessionManager
from app.services.instagram_scraper import InstagramPostScraper
from app.services.price_extractor import PriceExtractor
from app.services.product_service import ProductService
from app.database.mongodb import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/instagram", tags=["instagram"])


class ScrapeRequest(BaseModel):
    """Request to scrape Instagram account."""
    username: str = Field(..., description="Instagram username (without @)", min_length=1, max_length=100)
    hours_back: int = Field(default=48, ge=1, le=720, description="How many hours back to search")


class ScrapeResponse(BaseModel):
    """Response from scrape operation."""
    success: bool
    username: str
    posts_scraped: int
    products_extracted: int
    products_saved: int
    errors: list[str] = Field(default_factory=list)


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_instagram(
    request: ScrapeRequest,
    db=Depends(get_db)
) -> ScrapeResponse:
    """
    Scrape Instagram account and extract product prices.

    Args:
        request: Scrape parameters

    Returns:
        Scrape results
    """
    errors = []

    try:
        # Initialize services
        session_mgr = InstagramSessionManager()
        price_extractor = PriceExtractor()
        scraper = InstagramPostScraper(session_mgr, price_extractor)
        product_svc = ProductService(db)

        # Ensure indexes
        await product_svc.ensure_indexes()

        logger.info(f"Starting Instagram scrape for @{request.username}")

        # Scrape posts
        posts = await scraper.scrape_recent_posts(request.username, hours_back=request.hours_back)
        logger.info(f"Scraped {len(posts)} posts")

        # Process posts (extract images, OCR, prices)
        products = await scraper.process_posts(posts)
        logger.info(f"Extracted {len(products)} products")

        # Save to MongoDB
        products_saved = 0
        for product in products:
            try:
                product_id = await product_svc.save_product(product)
                if product_id:
                    products_saved += 1
            except Exception as e:
                logger.error(f"Failed to save product: {e}")
                errors.append(f"Failed to save product: {str(e)}")

        logger.info(f"Saved {products_saved} products to database")

        return ScrapeResponse(
            success=True,
            username=request.username,
            posts_scraped=len(posts),
            products_extracted=len(products),
            products_saved=products_saved,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scrape failed: {str(e)}"
        )


@router.get("/status")
async def scrape_status() -> dict:
    """Get Instagram scraper status and last run info."""
    return {
        "status": "ready",
        "service": "instagram",
        "last_run": None,
        "next_run": None,
        "enabled": True
    }


@router.post("/test-connection")
async def test_instagram_connection() -> dict:
    """Test Instagram connection (verify credentials work)."""
    try:
        session_mgr = InstagramSessionManager()
        client = session_mgr.load_or_create_session()
        user = client.get_me()

        return {
            "status": "connected",
            "user_id": user.pk,
            "username": user.username,
            "verified": getattr(user, 'is_verified', False)
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Instagram connection failed: {str(e)}"
        )