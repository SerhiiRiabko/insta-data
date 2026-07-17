"""
Website scrapers package

Implements scrapers for:
- Cijene.me (aggregates Aroma/Voli/HDL/IDEA prices) — active, real data source
- Instagram (price posts) — mock
- Aroma (legacy, unused Playwright-based scraper) — optional import, see below
"""

import logging

from app.services.scrapers.cijene_scraper import CijeneScraper
from app.services.scrapers.instagram_mock_scraper import InstagramMockScraper

logger = logging.getLogger(__name__)

__all__ = [
    "CijeneScraper",
    "InstagramMockScraper",
]

# AromaScraper needs Playwright, which isn't part of the active pipeline
# (ScraperOrchestrator only registers CijeneScraper + InstagramMockScraper).
# Optional, like the instagrapi imports in services/__init__.py, so this
# package doesn't hard-fail when Playwright isn't installed.
try:
    from app.services.scrapers.aroma_scraper import AromaScraper
    __all__.append("AromaScraper")
except ImportError as e:
    logger.warning(f"AromaScraper unavailable: {e}")
