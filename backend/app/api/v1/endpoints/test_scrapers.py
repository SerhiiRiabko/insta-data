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


@router.post("/hdl", response_model=TestScraperResponse)
async def test_hdl_scraper() -> TestScraperResponse:
    """Test HDL.me scraper"""
    import time
    start_time = time.time()

    try:
        from app.services.scrapers.hdl_mock_scraper import HDLMockScraper

        scraper = HDLMockScraper()
        logger.info("Testing HDL scraper...")

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
            scraper="HDL",
            status="success",
            products=len(products),
            sample_products=sample,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"HDL test failed: {e}", exc_info=True)
        return TestScraperResponse(
            scraper="HDL",
            status="failed",
            products=0,
            sample_products=[],
            error=str(e),
            duration_seconds=duration,
        )


@router.post("/idea", response_model=TestScraperResponse)
async def test_idea_scraper() -> TestScraperResponse:
    """Test IDEA.me scraper"""
    import time
    start_time = time.time()

    try:
        from app.services.scrapers.idea_mock_scraper import IDEAMockScraper

        scraper = IDEAMockScraper()
        logger.info("Testing IDEA scraper...")

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
            scraper="IDEA",
            status="success",
            products=len(products),
            sample_products=sample,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"IDEA test failed: {e}", exc_info=True)
        return TestScraperResponse(
            scraper="IDEA",
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
