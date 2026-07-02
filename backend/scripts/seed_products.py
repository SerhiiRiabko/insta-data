"""
Seed script for MongoDB - populate with initial 8 products

Usage:
    python scripts/seed_products.py

This script:
1. Connects to MongoDB (from config)
2. Clears existing products collection
3. Inserts 8 products with prices for 4 stores (Aroma, Voli, HDL, IDEA)
4. Calculates min_price and cheapest_store
5. Verifies insertion
"""

import asyncio
import logging
import hashlib
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock product data (same as frontend)
MOCK_PRODUCTS = [
    {
        "name": "Молоко / Молоко / Milk",
        "unit": "1 л",
        "description": "Fresh milk 1L",
        "source": "mock_seed",
        "prices": [1.49, 1.45, 1.52, 1.39],  # [Aroma, Voli, HDL, IDEA]
    },
    {
        "name": "Хлеб / Хліб / Bread",
        "unit": "500 г",
        "description": "Whole grain bread 500g",
        "source": "mock_seed",
        "prices": [0.89, 0.95, 0.85, 0.92],
    },
    {
        "name": "Яйца / Яйця / Eggs",
        "unit": "10 шт",
        "description": "Chicken eggs 10 pieces",
        "source": "mock_seed",
        "prices": [2.49, 2.39, 2.55, 2.45],
    },
    {
        "name": "Сыр Гауда / Сир Гауда / Gouda cheese",
        "unit": "1 кг",
        "description": "Aged Gouda cheese 1kg",
        "source": "mock_seed",
        "prices": [8.90, 9.20, 8.45, 8.99],
    },
    {
        "name": "Бананы / Банани / Bananas",
        "unit": "1 кг",
        "description": "Fresh bananas 1kg",
        "source": "mock_seed",
        "prices": [1.29, 1.19, 1.35, 1.25],
    },
    {
        "name": "Кофе молотый / Кава мелена / Ground coffee",
        "unit": "250 г",
        "description": "Ground coffee 250g",
        "source": "mock_seed",
        "prices": [4.49, 4.29, 4.59, 4.19],
    },
    {
        "name": "Оливковое масло / Оливкова олія / Olive oil",
        "unit": "1 л",
        "description": "Extra virgin olive oil 1L",
        "source": "mock_seed",
        "prices": [6.99, 7.49, 6.79, 7.10],
    },
    {
        "name": "Вода / Вода / Water",
        "unit": "1,5 л",
        "description": "Mineral water 1.5L",
        "source": "mock_seed",
        "prices": [0.55, 0.59, 0.49, 0.52],
    },
]

STORES = ["Aroma", "Voli", "HDL", "IDEA"]


def calculate_cheapest(prices):
    """Calculate min price and cheapest store index"""
    valid_prices = [(p, i) for i, p in enumerate(prices) if p is not None]
    if not valid_prices:
        return None, None

    min_price = min(p for p, _ in valid_prices)
    cheapest_idx = next(i for p, i in valid_prices if p == min_price)
    return min_price, cheapest_idx


def generate_dedup_hash(name, source):
    """Generate MD5 hash for deduplication"""
    key = f"{name}_{source}".lower()
    return hashlib.md5(key.encode()).hexdigest()


async def seed_products():
    """Main seed function"""

    # Connect to MongoDB
    logger.info(f"🔄 Connecting to MongoDB: {settings.mongodb_url}")
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]
    products_collection = db.products

    try:
        # Ping connection
        await db.command("ping")
        logger.info("✅ MongoDB connected")

        # Clear existing products
        result = await products_collection.delete_many({})
        logger.info(f"🗑️  Cleared {result.deleted_count} existing products")

        # Insert seed products
        products_to_insert = []
        now = datetime.utcnow()

        for i, product in enumerate(MOCK_PRODUCTS):
            min_price, cheapest_idx = calculate_cheapest(product["prices"])
            cheapest_store = STORES[cheapest_idx] if cheapest_idx is not None else None

            doc = {
                "name": product["name"],
                "unit": product["unit"],
                "description": product.get("description"),
                "source": product["source"],
                "category": None,
                "image_url": None,

                # Prices
                "prices": [
                    {
                        "store": STORES[j],
                        "price": price,
                        "currency": "EUR",
                        "timestamp": now,
                    }
                    for j, price in enumerate(product["prices"])
                ],
                "current_prices": {
                    STORES[j]: price
                    for j, price in enumerate(product["prices"])
                },
                "min_price": min_price,
                "max_price": max(p for p in product["prices"] if p is not None),
                "cheapest_store": cheapest_store,

                # Metadata
                "dedup_hash": generate_dedup_hash(product["name"], product["source"]),
                "created_at": now,
                "updated_at": now,
            }

            products_to_insert.append(doc)
            logger.info(
                f"  [{i+1}/8] {product['name'][:30]:<30} | "
                f"€{min_price:.2f} ({cheapest_store})"
            )

        # Bulk insert
        result = await products_collection.insert_many(products_to_insert)
        logger.info(f"✅ Inserted {len(result.inserted_ids)} products")

        # Verify insertion
        count = await products_collection.count_documents({})
        logger.info(f"📊 Total products in DB: {count}")

        # Show sample product
        sample = await products_collection.find_one({})
        if sample:
            logger.info(f"📋 Sample product:")
            logger.info(f"   Name: {sample['name']}")
            logger.info(f"   Prices: {sample['current_prices']}")
            logger.info(f"   Cheapest: €{sample['min_price']:.2f} ({sample['cheapest_store']})")

        logger.info("✅ Seeding completed successfully!")

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        raise
    finally:
        client.close()
        logger.info("🔌 MongoDB disconnected")


if __name__ == "__main__":
    asyncio.run(seed_products())
