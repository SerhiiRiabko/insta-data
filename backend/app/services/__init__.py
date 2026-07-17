"""Services package - business logic layer"""

import logging

logger = logging.getLogger(__name__)

__all__ = []

# instagrapi (Instagram auth/scraping) and Playwright-based store scrapers pull
# in dependency versions (e.g. instagrapi needs pydantic 1.x) that conflict
# with the FastAPI/pydantic-settings v2 stack this app otherwise runs on. Keep
# these imports optional so the app still boots (and the cijene.me + mock
# scrapers, which don't need them, still work) when they aren't installed.
try:
    from .instagram_auth import InstagramSessionManager
    __all__.append("InstagramSessionManager")
except ImportError as e:
    logger.warning(f"InstagramSessionManager unavailable: {e}")

try:
    from .instagram_scraper import InstagramPostScraper
    __all__.append("InstagramPostScraper")
except ImportError as e:
    logger.warning(f"InstagramPostScraper unavailable: {e}")

try:
    from .price_extractor import PriceExtractor
    __all__.append("PriceExtractor")
except ImportError as e:
    logger.warning(f"PriceExtractor unavailable: {e}")

try:
    from .product_service import ProductService
    __all__.append("ProductService")
except ImportError as e:
    logger.warning(f"ProductService unavailable: {e}")

try:
    from .store_scrapers import StoreScraper, AromaScraper, VoliScraper, HDLScraper, IDEAScraper
    __all__.extend(["StoreScraper", "AromaScraper", "VoliScraper", "HDLScraper", "IDEAScraper"])
except ImportError as e:
    logger.warning(f"StoreScraper family unavailable: {e}")

try:
    from .search_service import SearchService
    __all__.append("SearchService")
except ImportError as e:
    logger.warning(f"SearchService unavailable: {e}")

try:
    from .orchestrator import ScraperOrchestrator
    __all__.append("ScraperOrchestrator")
except ImportError as e:
    logger.warning(f"ScraperOrchestrator unavailable: {e}")