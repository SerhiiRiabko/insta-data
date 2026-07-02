"""
Base scraper class - provides common functionality for all website scrapers.

Implements:
- Playwright for JavaScript rendering
- BeautifulSoup fallback for HTML parsing
- Retry logic with exponential backoff
- Error logging and recovery
- Price normalization (EUR)
- Product deduplication
"""

import logging
import asyncio
import hashlib
from typing import List, Optional, Dict
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ScrapedProduct:
    """Represents a scraped product"""

    def __init__(
        self,
        name: str,
        price: float,
        url: str,
        source: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
    ):
        self.name = name.strip()
        self.price = float(price)
        self.url = url
        self.source = source
        self.category = category
        self.description = description
        self.image_url = image_url
        self.dedup_hash = self._generate_hash()
        self.timestamp = datetime.utcnow()

    def _generate_hash(self) -> str:
        """Generate MD5 hash for deduplication"""
        key = f"{self.name}_{self.source}".lower()
        return hashlib.md5(key.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Convert to MongoDB document"""
        return {
            "name": self.name,
            "price": self.price,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "description": self.description,
            "image_url": self.image_url,
            "dedup_hash": self.dedup_hash,
            "current_prices": {self.source: self.price},
            "min_price": self.price,
            "cheapest_store": self.source,
            "created_at": self.timestamp,
            "updated_at": self.timestamp,
        }


class BaseScraper(ABC):
    """
    Abstract base class for website scrapers.

    Subclasses must implement:
    - scrape_with_playwright()
    - scrape_with_beautifulsoup()
    - parse_products()
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.name = name
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = None

    async def scrape(self) -> List[ScrapedProduct]:
        """
        Main scrape method with fallback logic.

        1. Try Playwright (JavaScript rendering)
        2. Fallback to BeautifulSoup (HTML parsing)
        3. Retry on failure with exponential backoff
        4. Log results
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"🔄 [{self.name}] Attempt {attempt}/{self.max_retries}")

                # Try Playwright first
                try:
                    products = await self.scrape_with_playwright()
                    if products:
                        logger.info(
                            f"✅ [{self.name}] Playwright: {len(products)} products"
                        )
                        return products
                except Exception as e:
                    logger.warning(f"⚠️  [{self.name}] Playwright failed: {e}")

                # Fallback to BeautifulSoup
                try:
                    products = await self.scrape_with_beautifulsoup()
                    if products:
                        logger.info(
                            f"✅ [{self.name}] BeautifulSoup: {len(products)} products"
                        )
                        return products
                except Exception as e:
                    logger.warning(f"⚠️  [{self.name}] BeautifulSoup failed: {e}")

                # If both failed, retry with exponential backoff
                if attempt < self.max_retries:
                    wait_time = 2 ** (attempt - 1)  # 1s, 2s, 4s
                    logger.info(f"⏳ [{self.name}] Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"❌ [{self.name}] Scrape error: {e}")

        logger.error(
            f"❌ [{self.name}] Failed after {self.max_retries} attempts"
        )
        return []

    @abstractmethod
    async def scrape_with_playwright(self) -> List[ScrapedProduct]:
        """
        Scrape using Playwright (JavaScript rendering).

        Implementation notes:
        - Use for sites with dynamic content
        - Wait for elements to load
        - Handle modals/popups
        - Close browser on exit
        """
        pass

    @abstractmethod
    async def scrape_with_beautifulsoup(self) -> List[ScrapedProduct]:
        """
        Scrape using BeautifulSoup (HTML parsing).

        Implementation notes:
        - Use for static HTML sites
        - Parse DOM structure
        - Extract prices, names, links
        - Return list of ScrapedProduct
        """
        pass

    def normalize_price(self, price_str: str) -> Optional[float]:
        """
        Normalize price string to float (EUR).

        Handles:
        - Currency symbols (€, $)
        - Thousands separators (. or ,)
        - Decimal separators (. or ,)
        - Whitespace
        """
        try:
            # Remove common currency symbols
            cleaned = price_str.replace("€", "").replace("$", "").strip()

            # Handle thousands and decimal separators
            # Assuming format like "1.234,56" (EU) or "1,234.56" (US)
            # If last separator is comma, it's decimal
            if "," in cleaned and "." in cleaned:
                if cleaned.rfind(",") > cleaned.rfind("."):
                    # EU format: 1.234,56
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    # US format: 1,234.56
                    cleaned = cleaned.replace(",", "")
            elif "," in cleaned:
                # Could be thousands or decimal - assume decimal if single
                parts = cleaned.split(",")
                if len(parts[1]) <= 2:  # Likely decimal
                    cleaned = cleaned.replace(",", ".")
                else:  # Likely thousands
                    cleaned = cleaned.replace(",", "")

            return float(cleaned)
        except ValueError:
            logger.warning(f"Failed to parse price: {price_str}")
            return None

    async def close(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
