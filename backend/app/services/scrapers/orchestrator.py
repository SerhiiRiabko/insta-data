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
        # Which country each registered scraper's data belongs to - lets
        # run_all(country=...) run only the scrapers relevant to one country
        # instead of e.g. re-scraping Montenegro when the UA tab refreshes.
        self.scraper_country = {}
        self._register_scrapers()

    def _register_scrapers(self):
        """Register all available scrapers"""
        try:
            from app.services.scrapers.cijene_scraper import CijeneScraper
            # Real data source: one scraper covers Aroma/Voli/HDL/IDEA at once,
            # since cijene.me already aggregates all 4 chains' prices per product.
            self.scrapers["cijene"] = CijeneScraper()
            self.scraper_country["cijene"] = "ME"
        except Exception as e:
            logger.error(f"Failed to load Cijene.me scraper: {e}")

        try:
            from app.services.scrapers.instagram_mock_scraper import InstagramMockScraper
            self.scrapers["instagram"] = InstagramMockScraper()
            self.scraper_country["instagram"] = "ME"
        except Exception as e:
            logger.error(f"Failed to load Instagram scraper: {e}")

        # АТБ scraper (atb_scraper.py) intentionally NOT registered: its site
        # sits behind a Cloudflare managed challenge that blocks Playwright
        # automation outright - confirmed with navigator.webdriver patched,
        # headed mode, AND the real installed Chrome via channel="chrome",
        # none of which cleared the challenge even after 18s. This needs a
        # dedicated stealth/anti-detect solution (e.g. playwright-stealth or
        # a paid unlocker API), which is a separate, bigger piece of work -
        # left disabled rather than burning ~20s/category on every scrape
        # for nothing. The scraper code itself is ready to register once a
        # working bypass exists.

        try:
            from app.services.scrapers.silpo_scraper import SilpoScraper
            self.scrapers["silpo"] = SilpoScraper()
            self.scraper_country["silpo"] = "UA"
        except Exception as e:
            logger.error(f"Failed to load Сільпо scraper: {e}")

        try:
            from app.services.scrapers.varus_scraper import VarusScraper
            self.scrapers["varus"] = VarusScraper()
            self.scraper_country["varus"] = "UA"
        except Exception as e:
            logger.error(f"Failed to load Varus scraper: {e}")

        logger.info(f"Registered {len(self.scrapers)} scrapers: {list(self.scrapers.keys())}")

    async def run_all(self, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Run all scrapers in parallel (optionally scoped to one country's).

        Args:
            country: "ME" or "UA" - if given, only scrapers tagged for that
                country run (see scraper_country). None runs everything.

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
        logger.info(f"Starting orchestrated scraping (country={country or 'all'})...")

        import time
        start_time = time.time()

        scrapers = (
            self.scrapers
            if country is None
            else {k: v for k, v in self.scrapers.items() if self.scraper_country.get(k) == country}
        )

        # Create tasks for the selected scrapers
        tasks = {
            store_name: self._scrape_store(store_name, scraper)
            for store_name, scraper in scrapers.items()
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
                    "old_price": p.old_price,
                    "is_promo": p.is_promo,
                    "unit": p.unit,
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
