"""
Mock Voli.me Scraper - для тестування без інтернету
Видає 12 тестових продуктів від Voli магазину

Структура Voli:
- Product grid (мережа продуктів)
- Price in EUR (1.xx, 2.xx формати)
- Category from section
"""

import logging
from typing import List
from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class VoliMockScraper(BaseScraper):
    """Mock version of Voli scraper for testing without internet"""

    def __init__(self):
        super().__init__(
            name="Voli.me (MOCK)",
            base_url="https://www.voli.me",
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
        """Returns mock Voli products for testing"""
        products = [
            ScrapedProduct(
                name="Млеко целосне 1L",
                price=1.59,
                url="https://www.voli.me/proizvodi/mleko-1l",
                source="Voli",
                category="Dairy",
                description="Whole milk 1L",
            ),
            ScrapedProduct(
                name="Кефир пијача 500ml",
                price=2.49,
                url="https://www.voli.me/proizvodi/kefir-500ml",
                source="Voli",
                category="Dairy",
                description="Kefir drink",
            ),
            ScrapedProduct(
                name="Маслина црна Вршачка 500g",
                price=4.29,
                url="https://www.voli.me/proizvodi/maslina-crna",
                source="Voli",
                category="Vegetables",
                description="Black olives Vrsac",
            ),
            ScrapedProduct(
                name="Крај јабука свеже kg",
                price=1.49,
                url="https://www.voli.me/proizvodi/jabuka",
                source="Voli",
                category="Fruits",
                description="Fresh apples per kg",
            ),
            ScrapedProduct(
                name="Сир Смјентана 250g",
                price=5.29,
                url="https://www.voli.me/proizvodi/sir-smetana",
                source="Voli",
                category="Dairy",
                description="Sour cream cheese",
            ),
            ScrapedProduct(
                name="Компiр бели kg",
                price=0.79,
                url="https://www.voli.me/proizvodi/kompir",
                source="Voli",
                category="Vegetables",
                description="White potatoes per kg",
            ),
            ScrapedProduct(
                name="Салата зелена пакет",
                price=1.19,
                url="https://www.voli.me/proizvodi/salata",
                source="Voli",
                category="Vegetables",
                description="Green salad pack",
            ),
            ScrapedProduct(
                name="Парадајз конзервиран 400g",
                price=0.99,
                url="https://www.voli.me/proizvodi/paradajz-konz",
                source="Voli",
                category="Pantry",
                description="Canned tomatoes",
            ),
            ScrapedProduct(
                name="Јаја од слободне животиње 10x",
                price=2.19,
                url="https://www.voli.me/proizvodi/jaja-slobodna",
                source="Voli",
                category="Dairy",
                description="Free-range eggs 10 pack",
            ),
            ScrapedProduct(
                name="Масло бутер Валтер 250g",
                price=3.99,
                url="https://www.voli.me/proizvodi/maslo-valter",
                source="Voli",
                category="Dairy",
                description="Valter butter",
            ),
            ScrapedProduct(
                name="Пиринач Паризан 1kg",
                price=2.39,
                url="https://www.voli.me/proizvodi/pirinac-partizan",
                source="Voli",
                category="Pantry",
                description="Partizan rice",
            ),
            ScrapedProduct(
                name="Кафе на зrнца Макс 500g",
                price=7.49,
                url="https://www.voli.me/proizvodi/kafe-max",
                source="Voli",
                category="Beverages",
                description="Max coffee beans",
            ),
        ]

        logger.info(f"[{self.name}] Mock: returning {len(products)} products")
        return products
