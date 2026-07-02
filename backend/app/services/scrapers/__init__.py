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

__all__ = [
    "AromaScraper",
]
