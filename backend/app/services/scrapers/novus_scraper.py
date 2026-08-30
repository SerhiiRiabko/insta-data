"""
Novus scraper (novus.zakaz.ua) - Ukraine.

Runs on the zakaz.ua marketplace platform (shared by several Ukrainian
chains). The platform normally ties pricing/stock to a chosen delivery
address, but the "Каталог товарів" category pages (/uk/categories/<slug>/)
render real products with real prices WITHOUT selecting an address first -
presumably a default/Kyiv catalog. No bot-protection interstitial observed.

React SPA (Next.js-style `jsx-<hash>` class names) - products aren't in the
raw HTML, so this uses Playwright like Фора/Сільпо/Varus.

Price markup uses explicit `data-marker` attributes rather than fragile
class names:
  <div data-marker="Price">
    <div data-marker="Old Price">...<span class="Price__value_body...">49.79</span></div>  (only when discounted)
    <div data-marker="Discounted Price">...<span class="Price__value_caption">59.89</span></div>
  </div>
"""

import logging
import re
from typing import List, Optional

from app.services.base_scraper import BaseScraper, ScrapedProduct
from app.services.category_map import split_ua_produce_category

logger = logging.getLogger(__name__)

# "fruits-and-vegetables" is Novus's own combined category - split per-item
# by name keyword (see split_ua_produce_category) rather than kept as one
# "Фрукти та овочі" bucket, so it lines up with Сільпо/Varus/Фора's already
# -split "Овочі"/"Фрукти" categories. Category is part of the product-
# matching key (product_matcher.py), so a mismatched category here silently
# prevented identical produce names from ever matching across stores.
_PRODUCE_SLUG = "fruits-and-vegetables"

CATEGORIES = [
    (_PRODUCE_SLUG, "Фрукти та овочі"),
    ("dairy-and-eggs", "Молочка"),
    ("meat-fish-poultry", "М'ясо і риба"),
    # The combined page's first ~30 tiles are mostly deli/sausage items -
    # these facet filters (found via site nav) surface raw cuts like ribs
    # and brisket that never appeared otherwise.
    ("meat-fish-poultry/meat-part=ribs", "М'ясо і риба"),
    ("meat-fish-poultry/meat-part=brisket", "М'ясо і риба"),
    ("bakery", "Хлібобулочні вироби"),
    ("drinks", "Напої"),
    ("snacks-and-sweets", "Солодощі та снеки"),
    # Whole grocery aisles that weren't covered at all before (found via
    # site nav) - pantry staples, canned goods, frozen food.
    ("packets-cereals", "Бакалія"),
    ("tins-jars-cooking", "Консервація"),
    ("frozen", "Заморожені продукти"),
]

PRICE_NUM_RE = re.compile(r"[\d.,]+")

# Category pages paginate via ?page=N (confirmed live) - capped to bound
# total scrape time. See varus_scraper.py for the same pattern/reasoning.
MAX_PAGES_PER_CATEGORY = 2
MIN_ITEMS_FOR_NEXT_PAGE = 20

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class NovusScraper(BaseScraper):
    """Scrapes real grocery prices from novus.zakaz.ua (Ukraine)."""

    def __init__(self, category_limit: Optional[int] = None):
        super().__init__(
            name="Novus",
            base_url="https://novus.zakaz.ua",
            max_retries=2,
            timeout=25,
        )
        self.categories = CATEGORIES[:category_limit] if category_limit else CATEGORIES

    async def scrape_with_beautifulsoup(self) -> List[ScrapedProduct]:
        return []  # CSR - products aren't in the initial HTML, see module docstring.

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
                        url = f"{self.base_url}/uk/categories/{slug}/" + (f"?page={page_num}" if page_num > 1 else "")
                        try:
                            if page.is_closed():
                                # A previous navigation crashed the page - without
                                # this every remaining category would silently
                                # fail too.
                                page = await browser.new_page(user_agent=USER_AGENT)
                            await page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                            await page.wait_for_selector(".ProductTile", timeout=15000)
                            items = await page.eval_on_selector_all(
                                ".ProductTile",
                                """
                                (tiles) => tiles.map(t => {
                                    const title = t.querySelector('.ProductTile__title');
                                    const weight = t.querySelector('.ProductTile__weight');
                                    const oldPrice = t.querySelector('[data-marker="Old Price"] span');
                                    const curPrice = t.querySelector('[data-marker="Discounted Price"] span');
                                    const link = t.closest('a.ProductTileLink') || t.querySelector('a');
                                    const img = t.querySelector('img');
                                    if (!title || !curPrice) return null;
                                    return {
                                        name: title.textContent.trim(),
                                        weight: weight ? weight.textContent.trim() : null,
                                        old: oldPrice ? oldPrice.textContent.trim() : null,
                                        price: curPrice.textContent.trim(),
                                        href: link ? link.getAttribute('href') : null,
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
        if not item or not item.get("name") or not item.get("price"):
            return None

        price = self._parse_number(item["price"])
        if price is None:
            return None

        old_price = self._parse_number(item["old"]) if item.get("old") else None

        href = item.get("href") or ""
        url = href if href.startswith("http") else f"{self.base_url}{href}"

        if category == "Фрукти та овочі":
            category = split_ua_produce_category(item["name"])

        return ScrapedProduct(
            name=item["name"],
            price=price,
            old_price=old_price,
            url=url,
            source="Novus",
            category=category,
            image_url=item.get("img"),
            unit=item.get("weight"),
        )

    def _parse_number(self, text: str) -> Optional[float]:
        match = PRICE_NUM_RE.search(text.replace("\xa0", " "))
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", "."))
        except ValueError:
            return None
