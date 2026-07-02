"""
Website scrapers package

Implements scrapers for:
- Aroma.me (Montenegrin grocery)
- Voli.me (Montenegrin grocery)
- HDL.me (Montenegrin grocery)
- IDEA.me (Montenegrin grocery)
- Instagram (price posts)
"""

from app.services.scrapers.aroma_scraper import AromaScraper
from app.services.scrapers.aroma_mock_scraper import AromaMockScraper
from app.services.scrapers.voli_mock_scraper import VoliMockScraper

__all__ = [
    "AromaScraper",
    "AromaMockScraper",
    "VoliMockScraper",
]
