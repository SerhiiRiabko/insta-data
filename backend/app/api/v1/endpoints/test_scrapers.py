"""
Test endpoint for Phase 3 scrapers - for debugging and manual testing
"""

import logging
import asyncio
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test-scrapers", tags=["test-scrapers"])


class TestScraperResponse(BaseModel):
    """Response from test scraper"""
    scraper: str
    status: str  # "success", "failed"
    products: int
    sample_products: List[dict]
    error: str = None
    duration_seconds: float = None


@router.post("/aroma", response_model=TestScraperResponse)
async def test_aroma_scraper() -> TestScraperResponse:
    """
    Test Aroma.me scraper (debugging endpoint)

    Response includes:
    - status: success/failed
    - products: number of products found
    - sample_products: first 3 products
    - duration_seconds: scraping time
    """
    import time
    start_time = time.time()

    try:
        # Use mock scraper for testing (no internet access)
        from app.services.scrapers.aroma_mock_scraper import AromaMockScraper

        scraper = AromaMockScraper()
        logger.info("🔄 Testing Aroma scraper...")

        products = await scraper.scrape()
        duration = time.time() - start_time

        logger.info(f"✅ Aroma test: {len(products)} products in {duration:.1f}s")

        # Return sample products
        sample = []
        for p in products[:3]:
            sample.append({
                "name": p.name,
                "price": p.price,
                "source": p.source,
                "url": p.url[:50] + "..." if len(p.url) > 50 else p.url,
            })

        return TestScraperResponse(
            scraper="Aroma",
            status="success",
            products=len(products),
            sample_products=sample,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Aroma test failed: {e}", exc_info=True)
        return TestScraperResponse(
            scraper="Aroma",
            status="failed",
            products=0,
            sample_products=[],
            error=str(e),
            duration_seconds=duration,
        )


@router.post("/voli", response_model=TestScraperResponse)
async def test_voli_scraper() -> TestScraperResponse:
    """Test Voli.me scraper"""
    import time
    start_time = time.time()

    try:
        from app.services.scrapers.voli_mock_scraper import VoliMockScraper

        scraper = VoliMockScraper()
        logger.info("Testing Voli scraper...")

        products = await scraper.scrape()
        duration = time.time() - start_time

        logger.info(f"Voli test: {len(products)} products in {duration:.1f}s")

        sample = []
        for p in products[:3]:
            sample.append({
                "name": p.name,
                "price": p.price,
                "source": p.source,
                "url": p.url[:50] + "..." if len(p.url) > 50 else p.url,
            })

        return TestScraperResponse(
            scraper="Voli",
            status="success",
            products=len(products),
            sample_products=sample,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Voli test failed: {e}", exc_info=True)
        return TestScraperResponse(
            scraper="Voli",
            status="failed",
            products=0,
            sample_products=[],
            error=str(e),
            duration_seconds=duration,
        )
