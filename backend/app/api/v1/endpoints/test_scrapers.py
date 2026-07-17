"""
Test endpoint for Phase 3 scrapers - for debugging and manual testing
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/test-scrapers", tags=["test-scrapers"])


class TestScraperResponse(BaseModel):
    """Response from single scraper test"""
    scraper: str
    status: str  # "success", "failed"
    products: int
    sample_products: List[dict]
    error: str = None
    duration_seconds: float = None


class OrchestratorResponse(BaseModel):
    """Response from orchestrator (all scrapers)"""
    status: str  # "success", "partial", "failed"
    timestamp: str
    total_products: int
    by_store: Dict[str, Any]
    errors: List[str]
    duration_seconds: float


@router.post("/cijene", response_model=TestScraperResponse)
async def test_cijene_scraper() -> TestScraperResponse:
    """
    Test the real Cijene.me scraper (debugging endpoint).

    Covers Aroma/Voli/HDL/IDEA at once, since cijene.me aggregates all 4
    chains' prices per product.
    """
    import time
    start_time = time.time()

    try:
        from app.services.scrapers.cijene_scraper import CijeneScraper

        scraper = CijeneScraper()
        logger.info("🔄 Testing Cijene.me scraper...")

        products = await scraper.scrape()
        duration = time.time() - start_time

        logger.info(f"✅ Cijene.me test: {len(products)} products in {duration:.1f}s")

        sample = []
        for p in products[:3]:
            sample.append({
                "name": p.name,
                "price": p.price,
                "source": p.source,
                "url": p.url[:50] + "..." if len(p.url) > 50 else p.url,
            })

        return TestScraperResponse(
            scraper="Cijene.me",
            status="success",
            products=len(products),
            sample_products=sample,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Cijene.me test failed: {e}", exc_info=True)
        return TestScraperResponse(
            scraper="Cijene.me",
            status="failed",
            products=0,
            sample_products=[],
            error=str(e),
            duration_seconds=duration,
        )


@router.post("/instagram", response_model=TestScraperResponse)
async def test_instagram_scraper() -> TestScraperResponse:
    """Test Instagram scraper"""
    import time
    start_time = time.time()

    try:
        from app.services.scrapers.instagram_mock_scraper import InstagramMockScraper

        scraper = InstagramMockScraper()
        logger.info("Testing Instagram scraper...")

        products = await scraper.scrape()
        duration = time.time() - start_time

        sample = []
        for p in products[:3]:
            sample.append({
                "name": p.name,
                "price": p.price,
                "source": p.source,
                "url": p.url[:50] + "..." if len(p.url) > 50 else p.url,
            })

        return TestScraperResponse(
            scraper="Instagram",
            status="success",
            products=len(products),
            sample_products=sample,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Instagram test failed: {e}", exc_info=True)
        return TestScraperResponse(
            scraper="Instagram",
            status="failed",
            products=0,
            sample_products=[],
            error=str(e),
            duration_seconds=duration,
        )


@router.post("/run-all", response_model=OrchestratorResponse)
async def run_all_scrapers() -> OrchestratorResponse:
    """
    Run all 4 store scrapers in parallel.

    Response includes:
    - status: "success", "partial", or "failed"
    - total_products: sum of all products found
    - by_store: results for each store (status, products, samples, error, duration)
    - errors: list of errors from failed scrapers
    - duration_seconds: total time
    """
    try:
        from app.services.scrapers.orchestrator import ScraperOrchestrator

        orchestrator = ScraperOrchestrator()
        logger.info("Running all scrapers in parallel...")

        result = await orchestrator.run_all()

        return OrchestratorResponse(
            status=result.get("status", "failed"),
            timestamp=result.get("timestamp", ""),
            total_products=result.get("total_products", 0),
            by_store=result.get("by_store", {}),
            errors=result.get("errors", []),
            duration_seconds=result.get("duration_seconds", 0),
        )

    except Exception as e:
        logger.error(f"Orchestrator failed: {e}", exc_info=True)
        return OrchestratorResponse(
            status="failed",
            timestamp="",
            total_products=0,
            by_store={},
            errors=[str(e)],
            duration_seconds=0,
        )
