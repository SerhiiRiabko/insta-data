"""
Website scrapers package

Implements scrapers for:
- Cijene.me (aggregates Aroma/Voli/HDL/IDEA prices)
- Instagram (price posts)
"""

from app.services.scrapers.aroma_scraper import AromaScraper
from app.services.scrapers.cijene_scraper import CijeneScraper
from app.services.scrapers.instagram_mock_scraper import InstagramMockScraper

__all__ = [
    "AromaScraper",
    "CijeneScraper",
    "InstagramMockScraper",
]
