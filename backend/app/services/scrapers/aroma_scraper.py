"""
Aroma.me Scraper - scrapes grocery products from aroma.me

Site structure (typical):
- Product cards in grid layout
- Price in EUR (e.g., "€1.49")
- Category from breadcrumb or section

Fallback categories: Grocery, Fruits, Vegetables, Dairy, Meat, etc.
"""

import logging
import asyncio
from typing import List
from bs4 import BeautifulSoup
import aiohttp

from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class AromaScraper(BaseScraper):
    """Scrapes products from aroma.me"""

    def __init__(self):
        super().__init__(
            name="Aroma.me",
            base_url="https://www.aroma.me",
            max_retries=3,
            timeout=30,
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def scrape_with_playwright(self) -> List[ScrapedProduct]:
        """
        Scrape using Playwright for JavaScript rendering.

        Typical flow:
        1. Launch browser
        2. Go to products page
        3. Wait for products to load
        4. Scroll if needed (lazy loading)
        5. Extract HTML
        6. Parse with BeautifulSoup
        """
        try:
            # Lazy import to avoid dependency if not using
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                logger.warning("Playwright not installed, skipping")
                return []

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    logger.info(f"[{self.name}] Loading {self.base_url}...")
                    await page.goto(self.base_url, timeout=self.timeout * 1000)

                    # Wait for product elements to load
                    await page.wait_for_selector(
                        "[data-testid*='product'], .product-card, .item",
                        timeout=5000,
                    )

                    # Get rendered HTML
                    html = await page.content()
                    products = await self._parse_html(html)

                    logger.info(
                        f"✅ [{self.name}] Playwright: scraped {len(products)} products"
                    )
                    return products

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"❌ [{self.name}] Playwright error: {e}")
            return []

    async def scrape_with_beautifulsoup(self) -> List[ScrapedProduct]:
        """
        Scrape using BeautifulSoup (simple HTTP request).

        For sites that serve initial HTML with products.
        """
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"[{self.name}] Fetching {self.base_url}...")
                async with session.get(
                    self.base_url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status != 200:
                        logger.error(f"HTTP {response.status}: {self.base_url}")
                        return []

                    html = await response.text()
                    products = await self._parse_html(html)

                    logger.info(
                        f"✅ [{self.name}] BeautifulSoup: scraped {len(products)} products"
                    )
                    return products

        except asyncio.TimeoutError:
            logger.error(f"❌ [{self.name}] Request timeout")
            return []
        except Exception as e:
            logger.error(f"❌ [{self.name}] BeautifulSoup error: {e}")
            return []

    async def _parse_html(self, html: str) -> List[ScrapedProduct]:
        """
        Parse HTML and extract products.

        Selectors to try (in order):
        1. [data-testid*='product'] (modern React sites)
        2. .product-card (common class)
        3. .item, .product (fallback)
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            products = []

            # Try different product selectors
            selectors = [
                "[data-testid*='product']",
                ".product-card",
                ".item",
                ".product",
            ]

            product_elements = []
            for selector in selectors:
                product_elements = soup.select(selector)
                if product_elements:
                    logger.info(f"[{self.name}] Found {len(product_elements)} with {selector}")
                    break

            if not product_elements:
                logger.warning(f"[{self.name}] No product elements found")
                return []

            # Extract product data
            for i, elem in enumerate(product_elements[:50]):  # Limit to 50 for testing
                try:
                    # Extract name
                    name = self._extract_text(elem, ["h2", "h3", ".name", "[data-testid*='name']"])
                    if not name:
                        continue

                    # Extract price
                    price_str = self._extract_text(elem, [".price", "[data-testid*='price']", ".amount"])
                    price = self.normalize_price(price_str) if price_str else None
                    if not price:
                        logger.warning(f"[{self.name}] No price for {name}")
                        continue

                    # Extract URL
                    url = ""
                    link = elem.find("a", href=True)
                    if link:
                        url = link["href"]
                        if not url.startswith("http"):
                            url = self.base_url + url

                    # Extract category (if available)
                    category = self._extract_text(elem, [".category", ".tag", ".badge"])

                    product = ScrapedProduct(
                        name=name,
                        price=price,
                        url=url,
                        source="Aroma",
                        category=category,
                        description=None,
                    )
                    products.append(product)

                except Exception as e:
                    logger.warning(f"[{self.name}] Failed to parse product {i}: {e}")
                    continue

            logger.info(f"[{self.name}] Extracted {len(products)} valid products")
            return products

        except Exception as e:
            logger.error(f"❌ [{self.name}] HTML parsing error: {e}")
            return []

    def _extract_text(self, element, selectors: List[str]) -> str:
        """
        Try multiple selectors to extract text.
        Returns first non-empty match.
        """
        for selector in selectors:
            try:
                elem = element.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if text:
                        return text
            except:
                pass
        return ""
