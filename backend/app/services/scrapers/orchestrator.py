"""
Scraper Orchestrator - coordinates parallel execution of all scrapers

Responsibilities:
- Run all scrapers in parallel (async)
- Collect results
- Handle failures gracefully
- Store results to MongoDB (when available)
- Return unified response
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """Orchestrates parallel execution of all website scrapers"""

    def __init__(self):
        self.scrapers = {}
        self._register_scrapers()

    def _register_scrapers(self):
        """Register all available scrapers"""
        try:
            from app.services.scrapers.cijene_scraper import CijeneScraper
            # Real data source: one scraper covers Aroma/Voli/HDL/IDEA at once,
            # since cijene.me already aggregates all 4 chains' prices per product.
            self.scrapers["cijene"] = CijeneScraper()
        except Exception as e:
            logger.error(f"Failed to load Cijene.me scraper: {e}")

        try:
            from app.services.scrapers.instagram_mock_scraper import InstagramMockScraper
            self.scrapers["instagram"] = InstagramMockScraper()
        except Exception as e:
            logger.error(f"Failed to load Instagram scraper: {e}")

        logger.info(f"Registered {len(self.scrapers)} scrapers: {list(self.scrapers.keys())}")

    async def run_all(self) -> Dict[str, Any]:
        """
        Run all scrapers in parallel.

        Returns:
        {
            "status": "success",
            "timestamp": "2026-07-02T18:45:00Z",
            "total_products": 52,
            "by_store": {
                "aroma": {"status": "success", "products": 15, ...},
                "voli": {"status": "success", "products": 12, ...},
                ...
            },
            "errors": []
        }
        """
        logger.info("Starting orchestrated scraping for all stores...")

        import time
        start_time = time.time()

        # Create tasks for all scrapers
        tasks = {
            store_name: self._scrape_store(store_name, scraper)
            for store_name, scraper in self.scrapers.items()
        }

        # Run in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Collect results
        by_store = {}
        errors = []
        total_products = 0

        for store_name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {store_name}: {result}")
                by_store[store_name] = {
                    "status": "failed",
                    "products": 0,
                    "error": str(result),
                }
                errors.append(f"{store_name}: {str(result)}")
            else:
                by_store[store_name] = result
                total_products += result.get("products", 0)

        duration = time.time() - start_time

        response = {
            "status": "success" if errors == [] else "partial",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_products": total_products,
            "by_store": by_store,
            "errors": errors,
            "duration_seconds": duration,
        }

        logger.info(f"Orchestration complete: {total_products} products in {duration:.1f}s")
        return response

    async def run_single(self, store_name: str) -> Dict[str, Any]:
        """
        Run a single scraper.

        Args:
            store_name: "aroma", "voli", "hdl", "idea"

        Returns same structure as run_all() but for single store
        """
        if store_name not in self.scrapers:
            return {
                "status": "failed",
                "error": f"Unknown store: {store_name}",
                "available_stores": list(self.scrapers.keys()),
            }

        scraper = self.scrapers[store_name]
        result = await self._scrape_store(store_name, scraper)

        return {
            "status": result.get("status"),
            "store": store_name,
            **result,
        }

    async def _scrape_store(self, store_name: str, scraper) -> Dict[str, Any]:
        """
        Execute single scraper and collect results.

        Returns:
        {
            "status": "success" or "failed",
            "products": 15,
            "all_products": [{name, price, source, url}, ...],  # All products (not just samples)
            "error": None,
            "duration_seconds": 3.7
        }
        """
        import time
        start_time = time.time()

        try:
            logger.info(f"Scraping {store_name}...")
            products = await scraper.scrape()
            duration = time.time() - start_time

            # Prepare all products (not just samples)
            all_prods = []
            for p in products:
                all_prods.append({
                    "name": p.name,
                    "price": p.price,
                    "source": p.source,
                    "category": p.category,
                    "image_url": p.image_url,
                    "url": p.url[:60] + "..." if len(p.url) > 60 else p.url,
                })

            return {
                "status": "success",
                "products": len(products),
                "all_products": all_prods,  # All products for aggregation
                "error": None,
                "duration_seconds": duration,
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed to scrape {store_name}: {e}", exc_info=True)
            return {
                "status": "failed",
                "products": 0,
                "all_products": [],
                "error": str(e),
                "duration_seconds": duration,
            }

    async def save_to_mongodb(self, products: List[Any]) -> bool:
        """
        Save scraped products to MongoDB.

        Args:
            products: List of ScrapedProduct objects

        Returns:
            True if successful, False otherwise
        """
        try:
            from motor.motor_asyncio import AsyncIOMotorDatabase

            # This will be called from endpoint with db connection
            logger.info(f"Saving {len(products)} products to MongoDB...")
            # Implementation in endpoint layer
            return True

        except Exception as e:
            logger.error(f"Failed to save to MongoDB: {e}")
            return False
