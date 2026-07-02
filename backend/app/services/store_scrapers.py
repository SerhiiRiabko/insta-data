"""Base class and implementations for store scrapers."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page
from app.core.config import settings

logger = logging.getLogger(__name__)


class StoreScraper(ABC):
    """Abstract base class for store website scrapers."""

    def __init__(self, store_name: str, base_url: str):
        """
        Initialize scraper.

        Args:
            store_name: Store identifier (aroma, voli, hdl, idea)
            base_url: Store website base URL
        """
        self.store_name = store_name
        self.base_url = base_url
        self.browser: Optional[Browser] = None
        self.timeout = settings.scraper_timeout * 1000  # Convert to ms
        self.retry_attempts = settings.scraper_retry_attempts

    async def init_browser(self) -> None:
        """Initialize Playwright browser."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            logger.info(f"Browser initialized for {self.store_name}")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def close_browser(self) -> None:
        """Close Playwright browser."""
        if self.browser:
            await self.browser.close()
            logger.info(f"Browser closed for {self.store_name}")

    async def scrape_products(self) -> list[dict]:
        """
        Scrape all products from store.

        Returns:
            List of product dicts with name, price, image_url
        """
        products = []

        try:
            await self.init_browser()
            await self._scrape_with_retry(products)
        except Exception as e:
            logger.error(f"Scraping failed for {self.store_name}: {e}")
        finally:
            await self.close_browser()

        return products

    async def _scrape_with_retry(self, products: list) -> None:
        """Scrape with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                await self._scrape_products_impl(products)
                logger.info(f"Scraped {len(products)} products from {self.store_name}")
                return
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{self.retry_attempts} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

    @abstractmethod
    async def _scrape_products_impl(self, products: list) -> None:
        """
        Implementation-specific scraping logic.

        Subclasses must populate the products list.
        """
        pass

    async def _get_page_content(self, url: str, use_javascript: bool = False) -> str:
        """
        Fetch page content.

        Args:
            url: Page URL
            use_javascript: If True, wait for JS rendering (Playwright)

        Returns:
            Page HTML content
        """
        if use_javascript:
            return await self._fetch_with_playwright(url)
        else:
            return await self._fetch_with_requests(url)

    async def _fetch_with_playwright(self, url: str) -> str:
        """Fetch page with Playwright (JS rendering)."""
        page: Optional[Page] = None
        try:
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=self.timeout)
            content = await page.content()
            return content
        finally:
            if page:
                await page.close()

    async def _fetch_with_requests(self, url: str) -> str:
        """Fetch page with httpx (no JS rendering)."""
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup."""
        return BeautifulSoup(html, "html.parser")

    def normalize_price(self, price_str: str) -> Optional[float]:
        """
        Normalize price string to float.

        Handles formats like:
        - "1.50 EUR"
        - "1,50€"
        - "€1.50"
        - "1.50"

        Returns:
            Float price or None if parsing fails
        """
        import re

        if not price_str:
            return None

        # Remove whitespace and non-numeric chars except . and ,
        cleaned = re.sub(r'[^\d.,€]', '', price_str.strip())

        if not cleaned:
            return None

        try:
            # Normalize: replace comma with dot (EU format)
            normalized = cleaned.replace(',', '.')

            # Extract numeric part
            match = re.search(r'(\d+\.?\d*)', normalized)
            if match:
                return float(match.group(1))
        except ValueError:
            pass

        return None

    def normalize_product_data(self, raw_product: dict) -> Optional[dict]:
        """
        Normalize scraped product data.

        Args:
            raw_product: Raw product dict from scraper

        Returns:
            Normalized product dict or None if invalid
        """
        name = raw_product.get("name", "").strip()
        price = self.normalize_price(raw_product.get("price", ""))
        image_url = raw_product.get("image_url", "").strip()

        if not name or price is None:
            return None

        return {
            "name": name,
            "description": raw_product.get("description", "").strip(),
            "category": raw_product.get("category"),
            "image_url": image_url if image_url.startswith('http') else None,
            "source": self.store_name,
            "prices": [
                {
                    "store": self.store_name,
                    "price": price,
                    "currency": "EUR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }


class AromaScraper(StoreScraper):
    """Scraper for Aroma store (Montenegro)."""

    def __init__(self):
        super().__init__("aroma", "https://www.aroma.me")

    async def _scrape_products_impl(self, products: list) -> None:
        """Scrape Aroma products - uses JavaScript rendering."""
        html = await self._get_page_content(self.base_url, use_javascript=True)
        soup = self._parse_html(html)

        # Aroma uses next.js with __NEXT_DATA__ JSON
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script_tag:
            logger.warning("Could not find product data in Aroma page")
            return

        try:
            import json
            data = json.loads(script_tag.string)
            # Navigate to products in Next.js data structure
            # Structure varies, so we extract from any available product listings
            self._extract_from_nextjs(data, products)
        except Exception as e:
            logger.error(f"Failed to parse Aroma data: {e}")

    def _extract_from_nextjs(self, data: dict, products: list) -> None:
        """Extract products from Next.js __NEXT_DATA__ structure."""
        # Recursive search for product arrays
        def find_products(obj, found=None):
            if found is None:
                found = []

            if isinstance(obj, dict):
                for key, value in obj.items():
                    if 'product' in key.lower() or 'item' in key.lower():
                        if isinstance(value, (list, dict)):
                            find_products(value, found)
                    else:
                        find_products(value, found)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict) and any(
                        k in item for k in ['name', 'title', 'product', 'price']
                    ):
                        found.append(item)
                    else:
                        find_products(item, found)

            return found

        product_data = find_products(data)

        for raw_product in product_data:
            normalized = self.normalize_product_data({
                "name": raw_product.get("name") or raw_product.get("title"),
                "price": raw_product.get("price"),
                "image_url": raw_product.get("image") or raw_product.get("image_url"),
                "description": raw_product.get("description")
            })
            if normalized:
                products.append(normalized)


class VoliScraper(StoreScraper):
    """Scraper for Voli store (Montenegro)."""

    def __init__(self):
        super().__init__("voli", "https://www.voli.me")

    async def _scrape_products_impl(self, products: list) -> None:
        """Scrape Voli products."""
        html = await self._get_page_content(self.base_url, use_javascript=True)
        soup = self._parse_html(html)

        # Voli also uses Next.js
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if script_tag:
            try:
                import json
                data = json.loads(script_tag.string)
                self._extract_from_nextjs(data, products)
                return
            except Exception as e:
                logger.warning(f"Failed to parse Voli Next.js data: {e}")

        # Fallback: search for product elements in DOM
        product_elements = soup.find_all("div", class_=lambda x: x and "product" in x.lower())

        for elem in product_elements:
            try:
                name = elem.find(class_=lambda x: x and "name" in x.lower())
                price = elem.find(class_=lambda x: x and "price" in x.lower())
                image = elem.find("img")

                normalized = self.normalize_product_data({
                    "name": name.text.strip() if name else None,
                    "price": price.text.strip() if price else None,
                    "image_url": image.get("src") if image else None
                })
                if normalized:
                    products.append(normalized)
            except Exception as e:
                logger.debug(f"Error parsing product element: {e}")

    def _extract_from_nextjs(self, data: dict, products: list) -> None:
        """Extract products from Next.js structure."""
        # Similar to Aroma
        def find_products(obj, found=None):
            if found is None:
                found = []

            if isinstance(obj, dict):
                for key, value in obj.items():
                    if 'product' in key.lower() or 'item' in key.lower():
                        if isinstance(value, (list, dict)):
                            find_products(value, found)
                    else:
                        find_products(value, found)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict) and any(
                        k in item for k in ['name', 'title', 'price']
                    ):
                        found.append(item)
                    else:
                        find_products(item, found)

            return found

        product_data = find_products(data)
        for raw_product in product_data:
            normalized = self.normalize_product_data({
                "name": raw_product.get("name") or raw_product.get("title"),
                "price": raw_product.get("price"),
                "image_url": raw_product.get("image") or raw_product.get("image_url")
            })
            if normalized:
                products.append(normalized)


class HDLScraper(StoreScraper):
    """Scraper for HDL store (Montenegro)."""

    def __init__(self):
        super().__init__("hdl", "https://www.hdl.me")

    async def _scrape_products_impl(self, products: list) -> None:
        """Scrape HDL products."""
        html = await self._get_page_content(self.base_url, use_javascript=True)
        soup = self._parse_html(html)

        # Try Next.js first
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if script_tag:
            try:
                import json
                data = json.loads(script_tag.string)
                self._extract_products(data, products)
                return
            except Exception as e:
                logger.warning(f"Failed to parse HDL data: {e}")

        # Fallback to DOM parsing
        product_elements = soup.find_all("div", class_=lambda x: x and "product" in x.lower())
        for elem in product_elements:
            try:
                name = elem.find(class_="product-title") or elem.find("h2")
                price = elem.find(class_="product-price") or elem.find(class_=lambda x: x and "price" in x.lower())

                normalized = self.normalize_product_data({
                    "name": name.text.strip() if name else None,
                    "price": price.text.strip() if price else None
                })
                if normalized:
                    products.append(normalized)
            except Exception as e:
                logger.debug(f"Error parsing HDL product: {e}")

    def _extract_products(self, data: dict, products: list) -> None:
        """Extract products recursively from data structure."""
        def search(obj):
            result = []
            if isinstance(obj, dict):
                if all(k in obj for k in ['name', 'price']):
                    result.append(obj)
                for v in obj.values():
                    result.extend(search(v))
            elif isinstance(obj, list):
                for item in obj:
                    result.extend(search(item))
            return result

        found = search(data)
        for raw_product in found:
            normalized = self.normalize_product_data({
                "name": raw_product.get("name"),
                "price": raw_product.get("price"),
                "image_url": raw_product.get("image_url")
            })
            if normalized:
                products.append(normalized)


class IDEAScraper(StoreScraper):
    """Scraper for IDEA store (Montenegro)."""

    def __init__(self):
        super().__init__("idea", "https://www.idea.me")

    async def _scrape_products_impl(self, products: list) -> None:
        """Scrape IDEA products."""
        html = await self._get_page_content(self.base_url, use_javascript=True)
        soup = self._parse_html(html)

        # IDEA uses Next.js
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if script_tag:
            try:
                import json
                data = json.loads(script_tag.string)
                self._extract_products(data, products)
                return
            except Exception as e:
                logger.warning(f"Failed to parse IDEA data: {e}")

        # Fallback DOM parsing
        product_elements = soup.find_all("article", class_=lambda x: x and "product" in x.lower())
        for elem in product_elements:
            try:
                name_elem = elem.find(class_="product-name") or elem.find("h3")
                price_elem = elem.find(class_="product-price") or elem.find(class_=lambda x: x and "price" in x.lower())
                img_elem = elem.find("img")

                normalized = self.normalize_product_data({
                    "name": name_elem.text.strip() if name_elem else None,
                    "price": price_elem.text.strip() if price_elem else None,
                    "image_url": img_elem.get("src") or img_elem.get("data-src") if img_elem else None
                })
                if normalized:
                    products.append(normalized)
            except Exception as e:
                logger.debug(f"Error parsing IDEA product: {e}")

    def _extract_products(self, data: dict, products: list) -> None:
        """Extract products from Next.js data."""
        def search(obj):
            result = []
            if isinstance(obj, dict):
                if any(k in obj for k in ['name', 'title', 'product_name']):
                    if 'price' in obj:
                        result.append(obj)
                for v in obj.values():
                    result.extend(search(v))
            elif isinstance(obj, list):
                for item in obj:
                    result.extend(search(item))
            return result

        found = search(data)
        for raw_product in found:
            normalized = self.normalize_product_data({
                "name": raw_product.get("name") or raw_product.get("title") or raw_product.get("product_name"),
                "price": raw_product.get("price"),
                "image_url": raw_product.get("image_url") or raw_product.get("image")
            })
            if normalized:
                products.append(normalized)