"""Orchestrate and schedule all scrapers."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.instagram_scraper import InstagramPostScraper
from app.services.instagram_auth import InstagramSessionManager
from app.services.price_extractor import PriceExtractor
from app.services.store_scrapers import AromaScraper, VoliScraper, HDLScraper, IDEAScraper
from app.services.product_service import ProductService
from app.core.config import settings
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """Manage all scrapers and schedule daily runs."""

    def __init__(self, mongo_db, redis_client=None):
        self.mongo_db = mongo_db
        self.redis = redis_client
        self.scheduler: AsyncIOScheduler = None
        self.scrapers = {}
        self.status = {}
        self._init_scrapers()

    def _init_scrapers(self) -> None:
        """Initialize all scrapers."""
        # Instagram
        if settings.scraper_instagram_enabled:
            session_mgr = InstagramSessionManager()
            price_extractor = PriceExtractor()
            self.scrapers["instagram"] = InstagramPostScraper(session_mgr, price_extractor)
            self.status["instagram"] = {"status": "ready", "last_run": None}

        # Store scrapers
        if settings.scraper_aroma_enabled:
            self.scrapers["aroma"] = AromaScraper()
            self.status["aroma"] = {"status": "ready", "last_run": None}

        if settings.scraper_voli_enabled:
            self.scrapers["voli"] = VoliScraper()
            self.status["voli"] = {"status": "ready", "last_run": None}

        if settings.scraper_hdl_enabled:
            self.scrapers["hdl"] = HDLScraper()
            self.status["hdl"] = {"status": "ready", "last_run": None}

        if settings.scraper_idea_enabled:
            self.scrapers["idea"] = IDEAScraper()
            self.status["idea"] = {"status": "ready", "last_run": None}

        logger.info(f"Initialized {len(self.scrapers)} scrapers")

    async def start_scheduler(self) -> None:
        """Start APScheduler with daily job at 06:00 UTC (Kyiv time)."""
        self.scheduler = AsyncIOScheduler()

        # Schedule daily scrape at 06:00 UTC (8:00 Kyiv summer time)
        self.scheduler.add_job(
            self.run_all_scrapers,
            CronTrigger(hour=6, minute=0, timezone="UTC"),
            id="daily_scrape",
            name="Daily Product Scrape",
            max_instances=1  # Prevent concurrent runs
        )

        self.scheduler.start()
        logger.info("Scheduler started: Daily scrape at 06:00 UTC")

    async def stop_scheduler(self) -> None:
        """Stop scheduler gracefully."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    async def run_all_scrapers(self) -> Dict[str, Dict]:
        """
        Run all enabled scrapers in parallel.

        Returns:
            Dict with results for each scraper
        """
        logger.info("Starting all scrapers...")
        start_time = datetime.utcnow()

        # Run scrapers in parallel
        tasks = {
            name: self._run_scraper(name, scraper)
            for name, scraper in self.scrapers.items()
        }

        results = {}
        for name, task in tasks.items():
            try:
                result = await task
                results[name] = result
            except Exception as e:
                logger.error(f"Scraper {name} failed: {e}")
                results[name] = {
                    "status": "failed",
                    "error": str(e),
                    "products": 0
                }

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"All scrapers completed in {duration:.1f}s")

        # Cache results in Redis
        await self._cache_results(results)

        return results

    async def _run_scraper(self, name: str, scraper) -> Dict:
        """Run single scraper with error handling."""
        self.status[name]["status"] = "running"
        self.status[name]["last_run"] = datetime.utcnow().isoformat()

        start_time = datetime.utcnow()

        try:
            if name == "instagram":
                return await self._run_instagram_scraper(scraper)
            else:
                return await self._run_store_scraper(name, scraper)
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.status[name]["duration"] = duration
            self.status[name]["status"] = "completed"

    async def _run_instagram_scraper(self, scraper: InstagramPostScraper) -> Dict:
        """Run Instagram scraper."""
        logger.info("Starting Instagram scraper...")

        # Scrape posts from monitoring account (hardcoded or from config)
        # In production, you'd have a list of target accounts
        accounts = ["groceryprice_me"]  # Example account

        total_posts = 0
        total_products = 0

        product_svc = ProductService(self.mongo_db)
        await product_svc.ensure_indexes()

        for account in accounts:
            posts = await scraper.scrape_recent_posts(account, hours_back=48)
            total_posts += len(posts)

            products = await scraper.process_posts(posts)
            total_products += len(products)

            for product in products:
                try:
                    await product_svc.save_product(product)
                except Exception as e:
                    logger.error(f"Failed to save product: {e}")

        logger.info(f"Instagram: {total_posts} posts, {total_products} products")

        return {
            "status": "success",
            "posts": total_posts,
            "products": total_products
        }

    async def _run_store_scraper(self, name: str, scraper) -> Dict:
        """Run store website scraper."""
        logger.info(f"Starting {name} scraper...")

        try:
            products = await scraper.scrape_products()
            logger.info(f"{name}: Found {len(products)} products")

            # Save to MongoDB
            product_svc = ProductService(self.mongo_db)
            saved = 0

            for product in products:
                try:
                    product_id = await product_svc.save_product(product)
                    if product_id:
                        saved += 1
                except Exception as e:
                    logger.error(f"Failed to save product from {name}: {e}")

            logger.info(f"{name}: Saved {saved}/{len(products)} products")

            return {
                "status": "success",
                "found": len(products),
                "saved": saved
            }

        except Exception as e:
            logger.error(f"{name} scraper failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "found": 0,
                "saved": 0
            }

    async def _cache_results(self, results: Dict) -> None:
        """Cache scraper results in Redis."""
        if not self.redis:
            return

        try:
            cache_key = f"scraper:results:{datetime.utcnow().date()}"
            import json
            await self.redis.set(
                cache_key,
                json.dumps(results, default=str),
                ex=86400  # 24 hours TTL
            )
        except Exception as e:
            logger.warning(f"Failed to cache results: {e}")

    async def get_status(self) -> Dict:
        """Get current scraper status."""
        return {
            "scrapers": self.status,
            "scheduler_running": self.scheduler is not None and self.scheduler.running,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def run_instagram_scraper_only(self, account: str = None) -> Dict:
        """Run only Instagram scraper (manual trigger)."""
        if "instagram" not in self.scrapers:
            return {"error": "Instagram scraper not enabled"}

        scraper = self.scrapers["instagram"]
        return await self._run_instagram_scraper(scraper)

    async def run_store_scraper_only(self, store: str) -> Dict:
        """Run specific store scraper (manual trigger)."""
        if store not in self.scrapers:
            return {"error": f"Store {store} not enabled"}

        scraper = self.scrapers[store]
        return await self._run_store_scraper(store, scraper)