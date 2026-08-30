"""
Silpo scraper (silpo.ua) - Ukraine.

Server-rendered (Angular Universal - `_ngcontent-serverapp-*` markers in the
DOM) - but a plain aiohttp GET gets HTTP 403 even with realistic
Accept/Accept-Language headers, while a real Playwright-driven browser loads
the page fine every time. Most likely a TLS/JA3 fingerprint check rather than
a header check (no Cloudflare interstitial page is shown, unlike АТБ) -
either way, Playwright is what actually works, so that's what this uses.

Each product card's link has a rich, human-readable `aria-label` with all the
pricing info baked in - two formats observed:
  - On promo:    "<name>, <weight>, стара ціна <old> гривень, знижка <pct>%, нова ціна <new> гривень"
  - Regular:     "<name>; <weight>; <price> грн"
Parsing the aria-label is simpler and more robust than reverse-engineering
Silpo's internal `sf-ecom-api.silpo.ua` branch-scoped JSON API, which returns
category metadata but not a confirmed product-listing shape.
"""

import logging
import re
from typing import List, Optional

from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)

CATEGORIES = [
    ("ovochi-4808", "Овочі"),
    ("frukty-4791", "Фрукти"),
    ("moloko-vershky-237", "Молочка"),
    ("yogurty-deserty-235", "Молочка"),
    ("syry-1468", "Сири"),
    ("m-iaso-4411", "М'ясо і риба"),
    ("ryba-4430", "М'ясо і риба"),
    # m-iaso-4411 only surfaces its first ~60 items on load (mostly promo
    # items) - pork/beef cuts like ribs live further down and were missed
    # entirely. Found via site nav.
    ("svynyna-4413", "М'ясо і риба"),
    ("yalovychyna-ta-teliatyna-4414", "М'ясо і риба"),
    ("khlibobulochni-vyroby-5122", "Хлібобулочні вироби"),
    ("napoi-52", "Напої"),
    ("solodoshchi-498", "Солодощі та снеки"),
    # Whole grocery aisles that weren't covered at all before (found via
    # site nav) - pantry staples, canned goods, frozen food, deli meats, eggs.
    ("bakaliia-i-konservy-4870", "Бакалія"),
    ("zamorozhena-produktsiia-264", "Заморожені продукти"),
    ("kovbasni-vyroby-i-m-iasni-delikatesy-4731", "М'ясо і риба"),
    ("yaitsia-528", "Молочка"),
    ("alkogol-22", "Алкоголь"),
]

# "Ім'я, 500г, стара ціна 199 гривень, знижка 30%, нова ціна 139.3 гривень"
PROMO_RE = re.compile(
    r"^(?P<name>.+?),\s*(?P<weight>[^,]+),\s*"
    r"стара ціна\s+(?P<old>[\d.,]+)\s*гривень?,\s*"
    r"знижка\s+\d+%,\s*"
    r"нова ціна\s+(?P<new>[\d.,]+)\s*гривень?$",
    re.IGNORECASE,
)
# "Ім'я; 500г; 61.49 грн"
REGULAR_RE = re.compile(
    r"^(?P<name>.+?);\s*(?P<weight>[^;]+);\s*(?P<price>[\d.,]+)\s*грн\.?$",
    re.IGNORECASE,
)

# Category pages paginate via ?page=N (confirmed live, up to 14 pages on
# some categories) - capped to bound total scrape time. See varus_scraper.py
# for the same pattern/reasoning.
MAX_PAGES_PER_CATEGORY = 2
MIN_ITEMS_FOR_NEXT_PAGE = 20

# Categories genuinely sold by weight (as opposed to a fixed-SKU package) -
# see the per-100g note in _parse_item.
WEIGHED_CATEGORIES = {"Овочі", "Фрукти", "М'ясо і риба"}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class SilpoScraper(BaseScraper):
    """Scrapes real grocery prices from silpo.ua (Ukraine)."""

    def __init__(self, category_limit: Optional[int] = None):
        super().__init__(
            name="Сільпо",
            base_url="https://silpo.ua",
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
                        url = f"{self.base_url}/category/{slug}" + (f"?page={page_num}" if page_num > 1 else "")
                        try:
                            if page.is_closed():
                                # A previous navigation crashed the page - without
                                # this every remaining category would silently
                                # fail too.
                                page = await browser.new_page(user_agent=USER_AGENT)
                            await page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                            await page.wait_for_selector("a.product-card__link[aria-label]", timeout=15000)
                            labels = await page.eval_on_selector_all(
                                "a.product-card__link[aria-label]",
                                """
                                (elements) => elements.map(el => ({
                                    label: el.getAttribute('aria-label'),
                                    href: el.getAttribute('href'),
                                    img: el.querySelector('img') ? el.querySelector('img').getAttribute('src') : null,
                                }))
                                """,
                            )
                        except Exception as e:
                            logger.warning(f"[{self.name}] Failed to load {url}: {e}")
                            break

                        if not labels:
                            break  # past the last page

                        for item in labels:
                            product = self._parse_item(item, category)
                            if product:
                                results.append(product)
                        category_count += len(labels)

                        if len(labels) < MIN_ITEMS_FOR_NEXT_PAGE:
                            break  # short page - unlikely to be more after it
                    logger.info(f"[{self.name}] {slug}: {category_count} raw items")
            finally:
                await browser.close()

        logger.info(f"[{self.name}] Playwright: {len(results)} products across {len(self.categories)} categories")
        return results

    def _parse_item(self, item: dict, category: str) -> Optional[ScrapedProduct]:
        label = (item.get("label") or "").strip()
        if not label:
            return None

        match = PROMO_RE.match(label)
        if match:
            try:
                price = float(match.group("new").replace(",", "."))
                old_price = float(match.group("old").replace(",", "."))
            except ValueError:
                return None
            name = match.group("name").strip()
            weight = match.group("weight").strip()
        else:
            match = REGULAR_RE.match(label)
            if not match:
                return None
            try:
                price = float(match.group("price").replace(",", "."))
            except ValueError:
                return None
            old_price = None
            name = match.group("name").strip()
            weight = match.group("weight").strip()

        # Weighed produce/meat is priced as a "per 100g" reference (e.g.
        # "Кавун; 100г; 2.00 грн" - 2 грн for a whole watermelon makes no
        # sense, but 20 грн/kg does) - the same convention found on Varus,
        # just without Varus's explicit "за 100 г" wording. Packaged goods
        # in other categories also show a "весг" weight but that's the
        # real package size with a real whole-package price (e.g. "Молоко
        # ..., 900г, ... 44.99 гривень" - genuinely ~45 грн for the carton),
        # so this only applies to the categories that are actually sold by
        # weight, not to every product whose weight happens to say "100г".
        if category in WEIGHED_CATEGORIES and re.match(r'^100\s*г$', weight, re.IGNORECASE):
            price *= 10
            if old_price is not None:
                old_price *= 10
            weight = "1 кг"

        href = item.get("href") or ""
        url = href if href.startswith("http") else f"{self.base_url}{href}"
        image_url = item.get("img")

        return ScrapedProduct(
            name=name,
            price=price,
            old_price=old_price,
            url=url,
            source="Сільпо",
            category=category,
            image_url=image_url,
            unit=weight,
        )
