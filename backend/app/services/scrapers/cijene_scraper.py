"""
Cijene.me Scraper - real product/price data from cijene.me (Montenegro price comparison portal).

Site is a Laravel + Inertia.js SPA. The home page ("/") is paginated and, for
each product, returns: full name, a photo (relative path under /storage/...),
and a list of prices per physical store, each store tagged with its vendor_id
(the retail chain: Aroma, Voli, HDL, IDEA, ...).

Approach:
1. Plain GET "/" (no Inertia headers) to read the embedded Inertia `data-page`
   JSON — this gives the current asset `version` (required by every
   subsequent Inertia request or the server replies 409) plus page 1 data,
   the vendor list (id -> name) and category list (id -> name).
2. GET "/?page=N&city_id=<city>" with `X-Inertia: true` + the version header
   for every remaining page — these return pure JSON, much lighter than HTML.
3. For each product, group its per-store prices by vendor (a chain can have
   several branches in one city) and take the cheapest branch price per
   vendor, then emit one ScrapedProduct per (product, target vendor).

Only the 4 vendors this project already tracks (Aroma, Voli, HDL, IDEA) are
kept - matching the "stores" columns on the landing page's price matrix.
"""

import asyncio
import html
import json
import logging
import re
from typing import Any, Dict, List, Optional

import aiohttp

from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)

# cijene.me vendor slug -> display name used elsewhere in this project
# (MOCK_STORES / design brief: Aroma, Voli, HDL, IDEA).
TARGET_VENDOR_SLUGS = {
    "aroma": "Aroma",
    "voli": "Voli",
    "lakovic": "HDL",  # HDL's vendor slug on cijene.me is "lakovic"
    "idea": "IDEA",
}

DATA_PAGE_RE = re.compile(r'data-page="(.*?)"', re.DOTALL)


class CijeneScraper(BaseScraper):
    """Scrapes real grocery prices for Aroma/Voli/HDL/IDEA from cijene.me"""

    def __init__(self, city_id: int = 18, max_pages: int = 40):
        # city_id=18 is Podgorica (the capital, and cijene.me's own default) -
        # comparing prices within one city keeps the matrix meaningful.
        super().__init__(
            name="Cijene.me",
            base_url="https://cijene.me",
            max_retries=3,
            timeout=20,
        )
        self.city_id = city_id
        self.max_pages = max_pages
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    async def scrape_with_playwright(self) -> List[ScrapedProduct]:
        # cijene.me serves its data as JSON via Inertia.js - no JS rendering needed.
        return []

    async def scrape_with_beautifulsoup(self) -> List[ScrapedProduct]:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            first_page = await self._fetch_first_page(session)
            if first_page is None:
                return []

            version = first_page["version"]
            props = first_page["props"]
            vendors_by_id = {v["id"]: v["name"] for v in props.get("vendors", [])}
            # cijene.me vendors are looked up by slug (see TARGET_VENDOR_SLUGS);
            # build id -> our-display-name only for the 4 chains we track.
            vendor_slug_by_id = {v["id"]: v.get("slug") for v in props.get("vendors", [])}
            categories_by_id = {c["id"]: c["name"] for c in props.get("categories", [])}

            products_page = props["products"]
            all_scraped: List[ScrapedProduct] = []
            all_scraped += self._extract_products(
                products_page["data"], vendor_slug_by_id, categories_by_id
            )

            last_page = min(products_page.get("last_page", 1), self.max_pages)
            for page_num in range(2, last_page + 1):
                await asyncio.sleep(0.3)  # be polite
                page_data = await self._fetch_page(session, page_num, version)
                if page_data is None:
                    continue
                all_scraped += self._extract_products(
                    page_data["props"]["products"]["data"], vendor_slug_by_id, categories_by_id
                )

            logger.info(
                f"[{self.name}] Scraped {last_page} pages, {len(all_scraped)} store-priced products"
            )
            return all_scraped

    async def _fetch_first_page(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/?city_id={self.city_id}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as resp:
                if resp.status != 200:
                    logger.error(f"[{self.name}] HTTP {resp.status} loading {url}")
                    return None
                body = await resp.text()
                return self._parse_data_page(body)
        except Exception as e:
            logger.error(f"[{self.name}] Failed to load first page: {e}")
            return None

    async def _fetch_page(
        self, session: aiohttp.ClientSession, page_num: int, version: str
    ) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/?page={page_num}&city_id={self.city_id}"
            headers = {
                "X-Inertia": "true",
                "X-Inertia-Version": version,
                "Accept": "application/json",
            }
            async with session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"[{self.name}] HTTP {resp.status} on page {page_num}")
                    return None
                return await resp.json()
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to load page {page_num}: {e}")
            return None

    def _parse_data_page(self, html_body: str) -> Optional[Dict[str, Any]]:
        match = DATA_PAGE_RE.search(html_body)
        if not match:
            logger.error(f"[{self.name}] Could not find Inertia data-page in HTML")
            return None
        return json.loads(html.unescape(match.group(1)))

    def _extract_products(
        self,
        products: List[Dict[str, Any]],
        vendor_slug_by_id: Dict[int, str],
        categories_by_id: Dict[int, str],
    ) -> List[ScrapedProduct]:
        results = []
        for product in products:
            name = product.get("name")
            if not name:
                continue

            photo = product.get("photo")
            image_url = f"{self.base_url}/storage/{photo}" if photo else None
            category = categories_by_id.get(product.get("category_id"), "Other")
            product_url = f"{self.base_url}/proizvodi/{product['id']}/{product.get('slug', '')}"

            # A vendor can have several branches in the city; take the
            # cheapest branch price as "the" price for that chain.
            cheapest_by_vendor: Dict[str, float] = {}
            for price_entry in product.get("prices", []):
                store = price_entry.get("store") or {}
                vendor_slug = vendor_slug_by_id.get(store.get("vendor_id"))
                display_name = TARGET_VENDOR_SLUGS.get(vendor_slug) if vendor_slug else None
                if not display_name:
                    continue  # not one of the 4 chains we track

                try:
                    price = float(price_entry.get("effective_price") or price_entry.get("price"))
                except (TypeError, ValueError):
                    continue

                if display_name not in cheapest_by_vendor or price < cheapest_by_vendor[display_name]:
                    cheapest_by_vendor[display_name] = price

            for vendor_name, price in cheapest_by_vendor.items():
                results.append(
                    ScrapedProduct(
                        name=name,
                        price=price,
                        url=product_url,
                        source=vendor_name,
                        category=category,
                        image_url=image_url,
                    )
                )

        return results
