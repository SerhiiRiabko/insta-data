"""
ATB-Market scraper (atbmarket.com) - Ukraine.

Server-rendered HTML with very clean, semantic markup - product price is a
plain `<data value="53.50">` element, and a `product-price--sale` modifier
class on the price box marks a discounted item (with a second `<data>` for
the old price). No JSON API was found; this is the whole page's real markup,
not an API response.

Cloudflare: the site sits behind a Cloudflare managed challenge. Extensively
tested (see CLAUDE.md): plain Playwright (headless, headed, real Chrome
channel, navigator.webdriver patch, a full stealth init-script) and
patchright (a CDP-patched Playwright fork built specifically to evade this
kind of detection) all still get "Just a moment..." within ~3-15s -
consistent with a TLS/network-fingerprint-level check that no browser-JS-
level trick can pass, not a JS challenge.

What DOES pass: undetected-chromedriver (Selenium-based) in *headed* mode -
`--headless=new` still gets blocked, but a real (non-headless) Chrome
window clears the challenge in a few seconds every time tested. The
production VPS has no physical display, so this runs against a permanent
virtual one instead: `Xvfb :99` under supervisord (see xvfb.conf) with
`DISPLAY=:99` set on the backend service's environment. Selenium is
synchronous, so the whole call runs in a worker thread via
`asyncio.to_thread` to avoid blocking the event loop.

No pagination/infinite-scroll found on category pages (~25 items load and
stay at 25 regardless of scrolling) - ATB splits volume into subcategories
instead, which the CATEGORIES list below does not follow (kept to the same
11 top-level categories as before, for parity with the other 4 stores).
"""

import asyncio
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
    ("292-alkogol-i-tyutyun", "Алкоголь"),
]

NAME_RE = re.compile(r"^Купити\s+(.+?)\s+у\s+АТБ\s*Market$", re.IGNORECASE)

# undetected-chromedriver auto-detects the installed Chrome/Chromium's major
# version to fetch a matching chromedriver, but the snap-packaged chromium
# on this VPS reports a version its patcher can't parse reliably - pinning
# both explicitly avoids a silent mismatch.
CHROME_BINARY = "/usr/bin/chromium-browser"
CHROME_MAJOR_VERSION = 151


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
        """Despite the name (kept for BaseScraper's interface contract),
        this runs Selenium/undetected-chromedriver, not Playwright - see
        module docstring for why."""
        try:
            return await asyncio.to_thread(self._scrape_sync)
        except Exception as e:
            logger.error(f"[{self.name}] Selenium scrape failed: {e}")
            return []

    def _scrape_sync(self) -> List[ScrapedProduct]:
        import undetected_chromedriver as uc

        results: List[ScrapedProduct] = []
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1366,768")
        driver = uc.Chrome(
            options=options,
            browser_executable_path=CHROME_BINARY,
            version_main=CHROME_MAJOR_VERSION,
        )
        try:
            driver.set_page_load_timeout(self.timeout)
            for slug, category in self.categories:
                url = f"{self.base_url}/catalog/{slug}"
                try:
                    driver.get(url)
                    driver.implicitly_wait(0)
                    self._wait_for_products(driver, timeout=15)
                    cards = driver.find_elements("css selector", ".js-product-container")
                    items = [self._extract_card(card) for card in cards]
                except Exception as e:
                    logger.warning(f"[{self.name}] Failed to load {url}: {e}")
                    continue

                count = 0
                for item in items:
                    product = self._parse_item(item, category)
                    if product:
                        results.append(product)
                        count += 1
                logger.info(f"[{self.name}] {slug}: {count} products ({len(items)} raw cards)")
        finally:
            driver.quit()

        logger.info(f"[{self.name}] Selenium: {len(results)} products across {len(self.categories)} categories")
        return results

    @staticmethod
    def _wait_for_products(driver, timeout: int) -> None:
        import time
        from selenium.common.exceptions import NoSuchElementException

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                driver.find_element("css selector", ".js-product-container")
                return
            except NoSuchElementException:
                time.sleep(0.5)
        # Last attempt outside the loop - let the caller's except handle a
        # genuine failure (e.g. still on the Cloudflare interstitial).
        driver.find_element("css selector", ".js-product-container")

    @staticmethod
    def _extract_card(card) -> Optional[dict]:
        try:
            link = card.find_element("css selector", ".catalog-item__photo-link")
            price_box = card.find_element("css selector", ".catalog-item__product-price")
        except Exception:
            return None

        try:
            img = link.find_element("css selector", "img")
            alt = img.get_attribute("alt")
        except Exception:
            alt = None

        datas = [
            d.get_attribute("value")
            for d in price_box.find_elements("css selector", "data")
        ]

        return {
            "alt": alt,
            "href": link.get_attribute("href"),
            "isSale": "product-price--sale" in (price_box.get_attribute("class") or ""),
            "prices": datas,
        }

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
