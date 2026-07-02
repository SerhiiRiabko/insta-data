"""
Mock HDL.me Scraper - за тестување без интернета
Враќа 14 тест-производи од HDL магазин

HDL структура:
- Product listing page
- EUR цены (1.xx, 2.xx, 3.xx формати)
- Kategoriите од секција
"""

import logging
from typing import List
from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class HDLMockScraper(BaseScraper):
    """Mock version of HDL scraper for testing without internet"""

    def __init__(self):
        super().__init__(
            name="HDL.me (MOCK)",
            base_url="https://www.hdl.me",
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
        """Returns mock HDL products for testing"""
        products = [
            ScrapedProduct(
                name="Млеко полнозрнесто 1L",
                price=1.69,
                url="https://www.hdl.me/proizvodi/mleko",
                source="HDL",
                category="Dairy",
                description="Full-fat milk 1L",
            ),
            ScrapedProduct(
                name="Јогурт Активна Камілька 125g",
                price=0.49,
                url="https://www.hdl.me/proizvodi/jogurt-aktivna",
                source="HDL",
                category="Dairy",
                description="Active yogurt",
            ),
            ScrapedProduct(
                name="Маслина миксирана 450g",
                price=3.79,
                url="https://www.hdl.me/proizvodi/maslina-miksirana",
                source="HDL",
                category="Vegetables",
                description="Mixed olives",
            ),
            ScrapedProduct(
                name="Портокал свеж kg",
                price=1.39,
                url="https://www.hdl.me/proizvodi/portakal",
                source="HDL",
                category="Fruits",
                description="Fresh orange per kg",
            ),
            ScrapedProduct(
                name="Сир Гаревина 350g",
                price=4.49,
                url="https://www.hdl.me/proizvodi/sir-garevina",
                source="HDL",
                category="Dairy",
                description="Garevina cheese",
            ),
            ScrapedProduct(
                name="Морков свеж kg",
                price=0.89,
                url="https://www.hdl.me/proizvodi/morkov",
                source="HDL",
                category="Vegetables",
                description="Fresh carrots per kg",
            ),
            ScrapedProduct(
                name="Печени пиперки 250g",
                price=1.29,
                url="https://www.hdl.me/proizvodi/peceni-piperki",
                source="HDL",
                category="Vegetables",
                description="Roasted peppers",
            ),
            ScrapedProduct(
                name="Маст за печење Прима 1L",
                price=2.99,
                url="https://www.hdl.me/proizvodi/mast-prima",
                source="HDL",
                category="Oils",
                description="Cooking lard",
            ),
            ScrapedProduct(
                name="Јаја со браќо 10x",
                price=2.09,
                url="https://www.hdl.me/proizvodi/jaja-braco",
                source="HDL",
                category="Dairy",
                description="Brother eggs 10 pack",
            ),
            ScrapedProduct(
                name="Слатко кајмак 200g",
                price=3.19,
                url="https://www.hdl.me/proizvodi/kajmak-slatko",
                source="HDL",
                category="Dairy",
                description="Sweet cream",
            ),
            ScrapedProduct(
                name="Паста Милина 500g",
                price=1.49,
                url="https://www.hdl.me/proizvodi/pasta-milina",
                source="HDL",
                category="Pantry",
                description="Milina pasta",
            ),
            ScrapedProduct(
                name="Супа од јачменика 60g",
                price=0.59,
                url="https://www.hdl.me/proizvodi/supa-jacmenika",
                source="HDL",
                category="Pantry",
                description="Barley soup",
            ),
            ScrapedProduct(
                name="Вода газирана 1.5L",
                price=0.79,
                url="https://www.hdl.me/proizvodi/voda-gaziirana",
                source="HDL",
                category="Beverages",
                description="Sparkling water",
            ),
            ScrapedProduct(
                name="Чај Липа и мед 50g",
                price=1.09,
                url="https://www.hdl.me/proizvodi/caj-lipa",
                source="HDL",
                category="Beverages",
                description="Linden and honey tea",
            ),
        ]

        logger.info(f"[{self.name}] Mock: returning {len(products)} products")
        return products
