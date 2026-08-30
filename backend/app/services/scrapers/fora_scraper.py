"""
Fora scraper (fora.ua) - Ukraine.

Client-side rendered (React) - no bot-protection interstitial observed, but
product cards only exist in the DOM after JS runs, so this uses Playwright
(same as Сільпо/Varus) rather than a plain HTTP GET.

Price markup (confirmed via live DOM inspection):
  - No discount: <div class="current-price">
                   <div class="current-integer">12</div>
                   <div class="current-fraction">29 грн</div>
                 </div>
  - Discounted:  <div class="current-price isPromo">
                   <div class="price-addition">
                     <div class="old-price"><div class="old-integer">50,90 грн</div></div>
                     <div class="discount-count">-45%</div>
                   </div>
                   <div class="current-integer">27</div>
                   <div class="current-fraction">90 грн</div>
                 </div>
`.product-title` already includes the unit as a trailing ", кг"/", 350г" etc.
(e.g. "Картопля біла, кг"), so it's kept as-is rather than split out.
"""

import logging
import re
from typing import List, Optional

from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)

CATEGORIES = [
    ("ovochi-2794", "Овочі"),
    ("frukty-2797", "Фрукти"),
    ("moloko-2675", "Молочка"),
    ("kyslomolochni-napoi-2672", "Молочка"),
    ("syry-tverdi-3636", "Сири"),
    ("8svizhe-m-iaso-2700", "М'ясо і риба"),
    ("zhyva-ta-okholodzhena-ryba-ta-moreprodukty-2702", "М'ясо і риба"),
    # Pork/beef listing pages (found via site nav) - not yet covered by the
    # combined "Свіже м'ясо" page above.
    ("svynyna-2725", "М'ясо і риба"),
    ("yalovychyna-2729", "М'ясо і риба"),
    ("khlib-2912", "Хлібобулочні вироби"),
    ("soky-ta-bezalkogolni-napoi-2479", "Напої"),
    ("tsukerky-2934", "Солодощі та снеки"),
    # Whole grocery aisles that weren't covered at all before (found via
    # site nav) - pantry staples, canned goods, frozen food, deli meats.
    ("bakaliia-konservy-ta-sousy-2492", "Бакалія"),
    ("zamorozhena-produktsiia-2686", "Заморожені продукти"),
    ("kovbasy-ta-syry-2738", "М'ясо і риба"),
    ("alkogol-2451", "Алкоголь"),
    # Whole product groups that weren't covered at all before, not just
    # more food (found via site nav).
    ("dytiachi-tovary-2865", "Дитячі товари"),
    ("osobysta-gigiiena-2946", "Особиста гігієна"),
    ("pobutova-khimiia-2984", "Побутова хімія"),
    ("dlia-tvaryn-3060", "Зоотовари"),
]

PRICE_NUM_RE = re.compile(r"[\d.,]+")

# Category pages paginate via ?to=N&from=N (not ?page=N like the other 3
# stores - confirmed live) - capped to bound total scrape time. See
# varus_scraper.py for the same pattern/reasoning.
MAX_PAGES_PER_CATEGORY = 2
MIN_ITEMS_FOR_NEXT_PAGE = 20

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class ForaScraper(BaseScraper):
    """Scrapes real grocery prices from fora.ua (Ukraine)."""

    def __init__(self, category_limit: Optional[int] = None):
        super().__init__(
            name="Фора",
            base_url="https://fora.ua",
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
                        url = f"{self.base_url}/category/{slug}" + (
                            f"?to={page_num}&from={page_num}" if page_num > 1 else ""
                        )
                        try:
                            if page.is_closed():
                                # A previous navigation crashed the page - without
                                # this every remaining category would silently
                                # fail too.
                                page = await browser.new_page(user_agent=USER_AGENT)
                            await page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                            await page.wait_for_selector(".product-list-item", timeout=15000)
                            items = await page.eval_on_selector_all(
                                ".product-list-item",
                                """
                                (cards) => cards.map(card => {
                                    const titleEl = card.querySelector('.product-title');
                                    const linkEl = card.querySelector('.image-content-wrapper');
                                    const priceBox = card.querySelector('.product-price-container');
                                    const img = card.querySelector('img.product-list-item__image');
                                    if (!titleEl || !priceBox) return null;
                                    const isPromo = !!priceBox.querySelector('.current-price.isPromo');
                                    const oldEl = priceBox.querySelector('.old-price .old-integer');
                                    const curInt = priceBox.querySelector('.current-integer');
                                    const curFrac = priceBox.querySelector('.current-fraction');
                                    return {
                                        name: titleEl.textContent.trim(),
                                        href: linkEl ? linkEl.getAttribute('href') : null,
                                        isPromo,
                                        old: oldEl ? oldEl.textContent.trim() : null,
                                        curInt: curInt ? curInt.textContent.trim() : null,
                                        curFrac: curFrac ? curFrac.textContent.trim() : null,
                                        img: img ? img.getAttribute('src') : null,
                                    };
                                })
                                """,
                            )
                        except Exception as e:
                            logger.warning(f"[{self.name}] Failed to load {url}: {e}")
                            break

                        if not items:
                            break  # past the last page (or this category has no stock right now)

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
        if not item or not item.get("name") or not item.get("curInt"):
            return None

        # Price is split across two elements: whole (curInt, e.g. "12") and
        # fractional + currency (curFrac, e.g. "29 грн") - reassemble as a
        # single decimal rather than reusing the old-price string parser,
        # which expects a comma-decimal "50,90 грн" format instead.
        frac_match = re.match(r"(\d+)", item.get("curFrac") or "0")
        frac = frac_match.group(1) if frac_match else "0"
        try:
            price = float(item["curInt"]) + float(frac) / 100
        except ValueError:
            return None

        old_price = None
        if item.get("isPromo") and item.get("old"):
            old_price = self._parse_number(item["old"])

        href = item.get("href") or ""
        url = href if href.startswith("http") else f"{self.base_url}{href}"

        return ScrapedProduct(
            name=item["name"],
            price=price,
            old_price=old_price,
            url=url,
            source="Фора",
            category=category,
            image_url=item.get("img"),
        )

    def _parse_number(self, text: str) -> Optional[float]:
        match = PRICE_NUM_RE.search(text.replace("\xa0", " "))
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", "."))
        except ValueError:
            return None
