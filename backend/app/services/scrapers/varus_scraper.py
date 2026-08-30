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
    # Found by browsing the site nav (kuryatina only covers chicken) -
    # svinina/yalovichina are the pork/beef listing pages, grudinka is a
    # dedicated brisket page; without these, cuts like ribs/brisket never
    # appeared in the scrape at all.
    ("svinina", "М'ясо і риба"),
    ("yalovichina", "М'ясо і риба"),
    ("grudinka", "М'ясо і риба"),
    ("hlibobulochni-virobi", "Хлібобулочні вироби"),
    ("bezalkogolni-napoi", "Напої"),
    ("konditerski-virobi-ta-solodoschi", "Солодощі та снеки"),
    # Whole grocery aisles that weren't covered at all before (found via
    # site nav) - pantry staples, canned goods, frozen food, deli meats.
    ("bakaliya", "Бакалія"),
    ("konservi-ta-solinnya", "Консервація"),
    ("zamorozheni-produkti", "Заморожені продукти"),
    ("kolbasy-sosiski-delikatesy", "М'ясо і риба"),
    ("alkogol", "Алкоголь"),
    # Whole product groups that weren't covered at all before, not just
    # more food (found via site nav).
    ("tovari-dlya-ditey", "Дитячі товари"),
    ("kosmetika-ta-doglyad", "Особиста гігієна"),
    ("pobutova-himiya", "Побутова хімія"),
    ("tovari-dlya-tvarin", "Зоотовари"),
]

PRICE_NUM_RE = re.compile(r"[\d.,]+")

# Each category page paginates via ?page=N (confirmed live - page 1 of
# frukti-svizhi has 40 cards, ?page=2 has 32 different ones). Capped rather
# than following every page (some categories run 10+ pages) to keep total
# scrape time bounded - this alone still roughly doubles/triples per-category
# yield versus only reading page 1.
MAX_PAGES_PER_CATEGORY = 2
# A page this short is very likely the last one - not worth spending another
# request finding that out.
MIN_ITEMS_FOR_NEXT_PAGE = 20

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


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
                page = await browser.new_page(user_agent=USER_AGENT)
                for slug, category in self.categories:
                    category_count = 0
                    for page_num in range(1, MAX_PAGES_PER_CATEGORY + 1):
                        url = f"{self.base_url}/{slug}" + (f"?page={page_num}" if page_num > 1 else "")
                        try:
                            if page.is_closed():
                                # A previous navigation crashed the page (seen on
                                # a couple of categories during testing, cause
                                # unconfirmed) - without this every remaining
                                # category would silently fail too.
                                page = await browser.new_page(user_agent=USER_AGENT)
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
                            break

                        if not items:
                            break  # past the last page

                        for item in items:
                            product = self._parse_item(item, category)
                            if product:
                                results.append(product)
                        category_count += len(items)

                        if len(items) < MIN_ITEMS_FOR_NEXT_PAGE:
                            break  # short page - unlikely to be more after it
                    logger.info(f"[{self.name}] {slug}: {category_count} raw items")
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

        unit = item.get("unit")
        # Weighed meat/deli/cheese cards explicitly label the price "за 100 г"
        # (per 100g) instead of "за 1 кг" like every other store - found by
        # comparing a Varus rib price (~15-25 грн) against Novus/Сільпо's for
        # the exact same cut (~200-300 грн) after matching started merging
        # them: it wasn't a mismatch, Varus's raw number is just 1/10th of
        # the per-kg price. Scale up so cross-store comparisons are apples-
        # to-apples instead of making Varus look ~10x cheaper than it is.
        if unit and re.search(r'\b100\s*г\b', unit, re.IGNORECASE):
            price *= 10
            if old_price is not None:
                old_price *= 10
            unit = "за 1 кг"

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
            unit=unit,
        )

    def _parse_number(self, text: str) -> Optional[float]:
        match = PRICE_NUM_RE.search(text.replace("\xa0", " "))
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", "."))
        except ValueError:
            return None
