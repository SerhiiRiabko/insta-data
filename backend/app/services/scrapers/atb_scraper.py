"""
ATB-Market scraper (atbmarket.com) - Ukraine.

Server-rendered HTML with very clean, semantic markup - product price is a
plain `<data value="53.50">` element, and a `product-price--sale` modifier
class on the price box marks a discounted item (with a second `<data>` for
the old price). No JSON API was found; this is the whole page's real markup,
not an API response.

Cloudflare: the site sits behind a Cloudflare "managed challenge" ("Just a
moment..." interstitial). A plain HTTP client (aiohttp) cannot pass it - the
challenge requires executing real browser JS. Playwright's actual Chromium
engine clears it automatically within a couple of seconds with no extra
stealth tooling needed (verified manually), so this scraper is
Playwright-only; the BeautifulSoup fallback is a no-op.
"""

import logging
import re
from typing import List, Optional

from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)

# (url slug, our display category) - curated grocery categories, mirroring
# the spread of categories the Montenegro pipeline (cijene.me) covers.
CATEGORIES = [
    ("289-ovochi", "Овочі"),
    ("288-frukti-yagodi", "Фрукти"),
    ("398-moloko", "Молочка"),
    ("349-yogurti", "Молочка"),
    ("siri", "Сири"),
    ("maso", "М'ясо і риба"),
    ("riba", "М'ясо і риба"),
    ("331-khlib", "Хлібобулочні вироби"),
    ("307-napoi", "Напої"),
    ("299-konditers-ki-virobi", "Солодощі та снеки"),
    ("285-bakaliya", "Бакалія"),
]

NAME_RE = re.compile(r"^Купити\s+(.+?)\s+у\s+АТБ\s*Market$", re.IGNORECASE)


class AtbScraper(BaseScraper):
    """Scrapes real grocery prices from atbmarket.com (АТБ, Ukraine)."""

    def __init__(self, category_limit: Optional[int] = None):
        super().__init__(
            name="АТБ",
            base_url="https://www.atbmarket.com",
            max_retries=2,
            timeout=30,
        )
        # Cap how many categories get scraped per run - useful for quick
        # manual testing without waiting through all ~11 category pages.
        self.categories = CATEGORIES[:category_limit] if category_limit else CATEGORIES

    async def scrape_with_beautifulsoup(self) -> List[ScrapedProduct]:
        return []  # Cloudflare blocks plain HTTP - see module docstring.

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
                # Playwright leaves navigator.webdriver === true by default,
                # which is the one signal that made Cloudflare's managed
                # challenge hang indefinitely in testing (confirmed: with this
                # patch it clears in ~2-3s, without it it never clears headless).
                await page.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
                )
                for slug, category in self.categories:
                    url = f"{self.base_url}/catalog/{slug}"
                    try:
                        await page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                        # Cloudflare's managed challenge can take a few seconds to
                        # clear before the real page (and its products) render.
                        await page.wait_for_selector(".js-product-container", timeout=20000)
                        items = await page.eval_on_selector_all(
                            ".js-product-container",
                            """
                            (elements) => elements.map(el => {
                                const link = el.querySelector('.catalog-item__photo-link');
                                const priceBox = el.querySelector('.catalog-item__product-price');
                                if (!link || !priceBox) return null;
                                const img = link.querySelector('img');
                                const datas = Array.from(priceBox.querySelectorAll('data')).map(d => d.getAttribute('value'));
                                return {
                                    alt: img ? img.getAttribute('alt') : null,
                                    href: link.getAttribute('href'),
                                    isSale: priceBox.className.includes('product-price--sale'),
                                    prices: datas,
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
        if not item or not item.get("alt") or not item.get("prices"):
            return None

        match = NAME_RE.match(item["alt"].strip())
        name = match.group(1) if match else item["alt"].strip()

        try:
            prices = [float(p) for p in item["prices"] if p]
        except (TypeError, ValueError):
            return None
        if not prices:
            return None

        price = prices[0]
        old_price = prices[1] if item.get("isSale") and len(prices) > 1 else None

        href = item.get("href") or ""
        url = href if href.startswith("http") else f"{self.base_url}{href}"

        return ScrapedProduct(
            name=name,
            price=price,
            old_price=old_price,
            url=url,
            source="АТБ",
            category=category,
        )
