"""
Mock Instagram Scraper - симулює витяг цін з Instagram постів
Видає 15 соціальних постів з цінами (мок інстаграм акаунтів магазинів)

Типова структура:
- Текст: "Млеко 1L - 1.49€ Купи сейчас!"
- Hashtagи: #Aroma #Dairy #DailyDeal
- Дата: вчера/сьогодні
- URL: instagram.com/post/12345

Кожен пост публікує Instagram-акаунт КОНКРЕТНОГО магазину (Aroma/Voli/HDL/IDEA),
а не сам Instagram як окремий продавець - тож ціна атрибутується реальному
магазину (`source` = ім'я магазину), а не фейковому 5-му джерелу "Instagram".
Інакше ці рядки не з'єднуються з жодним реальним товаром cijene.me (fuzzy-match
не проходить поріг 85%) і "найдешевша ціна" тривіально показує "Instagram" -
джерело, яке ніхто не може реально купити.
"""

import logging
from typing import List
from datetime import datetime, timedelta
from app.services.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class InstagramMockScraper(BaseScraper):
    """Mock version of Instagram scraper for testing without real API"""

    def __init__(self):
        super().__init__(
            name="Instagram (MOCK)",
            base_url="https://instagram.com",
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
        """Returns mock Instagram products (social posts with prices), attributed
        to the real store whose account posted them - see module docstring."""
        products = [
            ScrapedProduct(
                name="Premium Mleko Aroma",
                price=1.89,
                url="https://instagram.com/p/AromaticDeals2306/",
                source="Aroma",
                category="Dairy",
                description="Млеко 1L Premium - HOJE 1.89€! #AromaDeals",
            ),
            ScrapedProduct(
                name="Organic Yogurt Voli",
                price=2.79,
                url="https://instagram.com/p/VoliOrganic2306/",
                source="Voli",
                category="Dairy",
                description="Органски јогурт 500g - Само 2.79€ #VoliFamily",
            ),
            ScrapedProduct(
                name="Fresh Olives HDL Black",
                price=3.49,
                url="https://instagram.com/p/HDLFresh2306/",
                source="HDL",
                category="Vegetables",
                description="Маслине черни 450g - 3.49€ #HDLFresh",
            ),
            ScrapedProduct(
                name="IDEA Premium Cheese",
                price=4.99,
                url="https://instagram.com/p/IDEAPremium2306/",
                source="IDEA",
                category="Dairy",
                description="Сирење Премиум 350g - ПРОМОЦИЈА 4.99€ #IDEAQuality",
            ),
            ScrapedProduct(
                name="Aroma Fresh Tomatoes",
                price=1.29,
                url="https://instagram.com/p/AromaFresh2306/",
                source="Aroma",
                category="Vegetables",
                description="Помидори свежи kg - 1.29€ #AromaFresh",
            ),
            ScrapedProduct(
                name="Voli Butter Premium",
                price=3.99,
                url="https://instagram.com/p/VoliButter2306/",
                source="Voli",
                category="Dairy",
                description="Маслица премиум 250g - 3.99€ #VoliBest",
            ),
            ScrapedProduct(
                name="HDL Olive Oil Extra",
                price=5.99,
                url="https://instagram.com/p/HDLOliveOil2306/",
                source="HDL",
                category="Oils",
                description="Маслиново масло Екстра - 5.99€ #HDLGourmet",
            ),
            ScrapedProduct(
                name="IDEA Fresh Bananas",
                price=0.99,
                url="https://instagram.com/p/IDEAFresh2306/",
                source="IDEA",
                category="Fruits",
                description="Банани свежи kg - 0.99€ #IDEAFresh",
            ),
            ScrapedProduct(
                name="Aroma Eggs Free Range",
                price=2.49,
                url="https://instagram.com/p/AromaEggs2306/",
                source="Aroma",
                category="Dairy",
                description="Јаја Слободни 10x - 2.49€ #AromaAnimal",
            ),
            ScrapedProduct(
                name="Voli Pasta Premium",
                price=1.79,
                url="https://instagram.com/p/VoliPasta2306/",
                source="Voli",
                category="Pantry",
                description="Паста Тальятеле 500g - 1.79€ #VoliItalian",
            ),
            ScrapedProduct(
                name="HDL Bread Whole Grain",
                price=0.89,
                url="https://instagram.com/p/HDLBread2306/",
                source="HDL",
                category="Bakery",
                description="Хлеб целозрнесто 600g - 0.89€ #HDLBakery",
            ),
            ScrapedProduct(
                name="IDEA Orange Juice",
                price=1.49,
                url="https://instagram.com/p/IDEAJuice2306/",
                source="IDEA",
                category="Beverages",
                description="Портокалов сок 1L - 1.49€ #IDEAHealthy",
            ),
            ScrapedProduct(
                name="Aroma Coffee Beans",
                price=6.99,
                url="https://instagram.com/p/AromaCoffee2306/",
                source="Aroma",
                category="Beverages",
                description="Кафе зрна Премиум 500g - 6.99€ #AromaQuality",
            ),
            ScrapedProduct(
                name="Voli Water Sparkling",
                price=0.79,
                url="https://instagram.com/p/VoliWater2306/",
                source="Voli",
                category="Beverages",
                description="Вода газирана 1.5L - 0.79€ #VoliRefresh",
            ),
            ScrapedProduct(
                name="HDL Sugar Special",
                price=0.99,
                url="https://instagram.com/p/HDLSugar2306/",
                source="HDL",
                category="Pantry",
                description="Шећер Специјална 1kg - 0.99€ #HDLSweetness",
            ),
        ]

        logger.info(f"[{self.name}] Mock: returning {len(products)} Instagram posts")
        return products
