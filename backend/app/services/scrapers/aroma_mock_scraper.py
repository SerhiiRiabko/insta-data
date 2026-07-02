"""
Mock Aroma.me Scraper - для тестування без інтернету
Видає 15 тестових продуктів в форматі справжнього Aroma

Це допоміжна версія для розробки коли немає доступу до сайту.
"""

import logging
from typing import List
from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class AromaMockScraper(BaseScraper):
    """Mock version of Aroma scraper for testing without internet"""

    def __init__(self):
        super().__init__(
            name="Aroma (MOCK)",
            base_url="https://www.aroma.me",
            max_retries=1,
            timeout=1,
        )

    async def scrape_with_playwright(self) -> List[ScrapedProduct]:
        """Mock implementation"""
        logger.info(f"[{self.name}] scrape_with_playwright() called (mock)")
        products = self._get_mock_products()
        logger.info(f"[{self.name}] Returning {len(products)} mock products")
        return products

    async def scrape_with_beautifulsoup(self) -> List[ScrapedProduct]:
        """Mock implementation"""
        logger.info(f"[{self.name}] scrape_with_beautifulsoup() called (mock)")
        products = self._get_mock_products()
        logger.info(f"[{self.name}] Returning {len(products)} mock products")
        return products

    def _get_mock_products(self) -> List[ScrapedProduct]:
        """Returns mock Aroma products for testing"""
        products = [
            ScrapedProduct(
                name="Млеко свежее 1L",
                price=1.49,
                url="https://www.aroma.me/products/mleko-1l",
                source="Aroma",
                category="Dairy",
                description="Fresh milk 1L",
            ),
            ScrapedProduct(
                name="Јогурт Активне 500g",
                price=2.29,
                url="https://www.aroma.me/products/jogurt-aktivne",
                source="Aroma",
                category="Dairy",
                description="Active yogurt",
            ),
            ScrapedProduct(
                name="Маслине зелене 500g",
                price=3.49,
                url="https://www.aroma.me/products/maslina-zelena",
                source="Aroma",
                category="Vegetables",
                description="Green olives",
            ),
            ScrapedProduct(
                name="Лимон свеж kg",
                price=1.29,
                url="https://www.aroma.me/products/limun-svez",
                source="Aroma",
                category="Fruits",
                description="Fresh lemon per kg",
            ),
            ScrapedProduct(
                name="Сир Подгорица 300g",
                price=4.99,
                url="https://www.aroma.me/products/sir-podgorica",
                source="Aroma",
                category="Dairy",
                description="Podgorica cheese",
            ),
            ScrapedProduct(
                name="Хлеб Црвен 600g",
                price=0.99,
                url="https://www.aroma.me/products/hleb-crven",
                source="Aroma",
                category="Bakery",
                description="Red bread",
            ),
            ScrapedProduct(
                name="Јаја пакет 10x",
                price=1.99,
                url="https://www.aroma.me/products/jaja-10",
                source="Aroma",
                category="Dairy",
                description="Eggs 10 pack",
            ),
            ScrapedProduct(
                name="Помидор свеж kg",
                price=1.79,
                url="https://www.aroma.me/products/pomidor-svez",
                source="Aroma",
                category="Vegetables",
                description="Fresh tomato per kg",
            ),
            ScrapedProduct(
                name="Масло Гастра 1L",
                price=5.49,
                url="https://www.aroma.me/products/maslo-gastra",
                source="Aroma",
                category="Oils",
                description="Gastra oil",
            ),
            ScrapedProduct(
                name="Шећер Квалитета 1kg",
                price=0.89,
                url="https://www.aroma.me/products/secer-kval",
                source="Aroma",
                category="Pantry",
                description="Quality sugar",
            ),
            ScrapedProduct(
                name="Пиринач Узак зрнце 1kg",
                price=2.19,
                url="https://www.aroma.me/products/pirinac-uzak",
                source="Aroma",
                category="Pantry",
                description="Narrow grain rice",
            ),
            ScrapedProduct(
                name="Парадајз сок 1L",
                price=1.49,
                url="https://www.aroma.me/products/paradajz-sok",
                source="Aroma",
                category="Beverages",
                description="Tomato juice",
            ),
            ScrapedProduct(
                name="Вода Источна 1.5L",
                price=0.59,
                url="https://www.aroma.me/products/voda-izvor",
                source="Aroma",
                category="Beverages",
                description="Spring water",
            ),
            ScrapedProduct(
                name="Кафе Меча Crema 250g",
                price=6.99,
                url="https://www.aroma.me/products/kafe-meca",
                source="Aroma",
                category="Beverages",
                description="Mecha coffee beans",
            ),
            ScrapedProduct(
                name="Чај зелени пакетима 20x",
                price=1.29,
                url="https://www.aroma.me/products/caj-zeleni",
                source="Aroma",
                category="Beverages",
                description="Green tea bags",
            ),
        ]

        logger.info(f"[{self.name}] Mock: returning {len(products)} products")
        return products
