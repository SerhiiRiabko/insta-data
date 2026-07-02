"""
Mock IDEA.me Scraper - за тестување без интернета
Враќа 11 тест-производи од IDEA магазин

IDEA структура:
- Product grid layout
- EUR цены (1.xx, 2.xx формати)
- Категориите од секција
"""

import logging
from typing import List
from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class IDEAMockScraper(BaseScraper):
    """Mock version of IDEA scraper for testing without internet"""

    def __init__(self):
        super().__init__(
            name="IDEA.me (MOCK)",
            base_url="https://www.idea.me",
            max_retries=1,
            timeout=1,
        )

    async def scrape_with_playwright(self) -> List[ScrapedProduct]:
        """Mock implementation"""
        return self._get_mock_products()

    async def scrape_with_beautifulsoup(self) -> List[ScrapedProduct]:
        """Mock implementation"""
        return self._get_mock_products()

    def _get_mock_products(self) -> List[ScrapedProduct]:
        """Returns mock IDEA products for testing"""
        products = [
            ScrapedProduct(
                name="Млеко 2.8% мастина 1L",
                price=1.49,
                url="https://www.idea.me/mleko-2-8",
                source="IDEA",
                category="Dairy",
                description="2.8% fat milk",
            ),
            ScrapedProduct(
                name="Сирене белина 500g",
                price=3.99,
                url="https://www.idea.me/sirenje-belina",
                source="IDEA",
                category="Dairy",
                description="White cheese",
            ),
            ScrapedProduct(
                name="Маслина зелена Каламата 370g",
                price=2.99,
                url="https://www.idea.me/maslina-kalamata",
                source="IDEA",
                category="Vegetables",
                description="Green Kalamata olives",
            ),
            ScrapedProduct(
                name="Банана свежа kg",
                price=0.99,
                url="https://www.idea.me/banane",
                source="IDEA",
                category="Fruits",
                description="Fresh bananas per kg",
            ),
            ScrapedProduct(
                name="Кетчуп Синол 500g",
                price=1.29,
                url="https://www.idea.me/ketchup-sinol",
                source="IDEA",
                category="Pantry",
                description="Sinol ketchup",
            ),
            ScrapedProduct(
                name="Маслиново масло Каливас 500ml",
                price=6.99,
                url="https://www.idea.me/maslo-kalivAS",
                source="IDEA",
                category="Oils",
                description="Kalivás olive oil",
            ),
            ScrapedProduct(
                name="Јаја белувала 10x",
                price=2.29,
                url="https://www.idea.me/jaja-beluvala",
                source="IDEA",
                category="Dairy",
                description="Bleached eggs 10 pack",
            ),
            ScrapedProduct(
                name="Млинари брашно 1kg",
                price=1.19,
                url="https://www.idea.me/brasno-mlinari",
                source="IDEA",
                category="Pantry",
                description="Mlinari flour",
            ),
            ScrapedProduct(
                name="Шећер детелина 1kg",
                price=0.99,
                url="https://www.idea.me/secer-detelijna",
                source="IDEA",
                category="Pantry",
                description="Clover sugar",
            ),
            ScrapedProduct(
                name="Млеко Премиум 3.5L",
                price=4.49,
                url="https://www.idea.me/mleko-premium-35",
                source="IDEA",
                category="Dairy",
                description="Premium milk 3.5L",
            ),
            ScrapedProduct(
                name="Хлеб целосен 600g",
                price=0.89,
                url="https://www.idea.me/hleb-celosen",
                source="IDEA",
                category="Bakery",
                description="Whole wheat bread",
            ),
        ]

        logger.info(f"[{self.name}] Mock: returning {len(products)} products")
        return products
