"""
Varus scraper (varus.ua) - Ukraine.

Vue Storefront (Nuxt) product cards - `.sf-product-card` elements carry full
name/price markup on first load. A plain aiohttp GET gets HTTP 403 (likely a
TLS/JA3 fingerprint check - no Cloudflare interstitial is shown), while a
real Playwright-driven browser loads the page fine every time, so this uses
Playwright like the АТБ and Сільпо scrapers.

Price markup (confirmed via live DOM inspection):
  - No discount: <span class="sf-price__regular">29.90 ₴</span>
  - Discounted:  <del class="sf-price__old">33.90</del>
                 <ins class="sf-price__special sf-price__special--sale">29.90 ₴</ins>
"""

import logging
import re
from typing import List, Optional

from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)

# Varus category paths are root-level (no /category/ prefix).
CATEGORIES = [
    ("ovochi-svizhi", "Овочі"),
    ("frukti-svizhi", "Фрукти"),
    ("moloko", "Молочка"),
    ("yogurti", "Молочка"),
    ("siri", "Сири"),
    ("kuryatina", "М'ясо і риба"),
    ("riba-oholodzhena", "М'ясо і риба"),
    ("hlibobulochni-virobi", "Хлібобулочні вироби"),
    ("bezalkogolni-napoi", "Напої"),
    ("konditerski-virobi-ta-solodoschi", "Солодощі та снеки"),
]

PRICE_NUM_RE = re.compile(r"[\d.,]+")


class VarusScraper(BaseScraper):
    """Scrapes real grocery prices from varus.ua (Ukraine)."""

    def __init__(self, category_limit: Optional[int] = None):
        super().__init__(
            name="Varus",
            base_url="https://varus.ua",
            max_retries=2,
            timeout=25,
        )
        self.categories = CATEGORIES[:category_limit] if category_limit else CATEGORIES

    async def scrape_with_beautifulsoup(self) -> List[ScrapedProduct]:
        return []  # Blocked (HTTP 403) - see module docstring.

    async def scrape_with_playwright(self) -> List[ScrapedProduct]:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning(f"[{self.name}] Playwright not installed, skipping")
            return []

        results: List[ScrapedProduct] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                for slug, category in self.categories:
                    url = f"{self.base_url}/{slug}"
                    try:
                        await page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                        await page.wait_for_selector(".sf-product-card", timeout=15000)
                        items = await page.eval_on_selector_all(
                            ".sf-product-card",
                            """
                            (cards) => cards.map(card => {
                                const title = card.querySelector('.sf-product-card__title-wrapper');
                                const special = card.querySelector('.sf-price__special');
                                const old = card.querySelector('.sf-price__old');
                                const regular = card.querySelector('.sf-price__regular');
                                const unitEl = card.querySelector('.sf-product-card__quantity');
                                const img = card.querySelector('img');
                                if (!title) return null;
                                return {
                                    name: title.textContent.trim(),
                                    href: title.getAttribute('href'),
                                    special: special ? special.textContent.trim() : null,
                                    old: old ? old.textContent.trim() : null,
                                    regular: regular ? regular.textContent.trim() : null,
                                    unit: unitEl ? unitEl.textContent.trim() : null,
                                    img: img ? img.getAttribute('src') : null,
                                };
                            })
                            """,
                        )
                    except Exception as e:
                        logger.warning(f"[{self.name}] Failed to load {url}: {e}")
                        continue

                    for item in items:
                        product = self._parse_item(item, category)
                        if product:
                            results.append(product)
                    logger.info(f"[{self.name}] {slug}: {len(items)} raw items")
            finally:
                await browser.close()

        logger.info(f"[{self.name}] Playwright: {len(results)} products across {len(self.categories)} categories")
        return results

    def _parse_item(self, item: Optional[dict], category: str) -> Optional[ScrapedProduct]:
        if not item or not item.get("name"):
            return None

        price = None
        old_price = None
        if item.get("special"):
            price = self._parse_number(item["special"])
            if item.get("old"):
                old_price = self._parse_number(item["old"])
        elif item.get("regular"):
            price = self._parse_number(item["regular"])

        if price is None:
            return None

        href = item.get("href") or ""
        url = href if href.startswith("http") else f"{self.base_url}{href}"

        return ScrapedProduct(
            name=item["name"],
            price=price,
            old_price=old_price,
            url=url,
            source="Varus",
            category=category,
            image_url=item.get("img"),
            unit=item.get("unit"),
        )

    def _parse_number(self, text: str) -> Optional[float]:
        match = PRICE_NUM_RE.search(text.replace("\xa0", " "))
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", "."))
        except ValueError:
            return None
