"""Product CRUD operations and deduplication."""

import hashlib
import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from app.models import Product, ProductCreate
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProductService:
    """Manage products in MongoDB with deduplication."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection: AsyncIOMotorCollection = db['products']

    async def ensure_indexes(self) -> None:
        """Create necessary indexes on products collection."""
        try:
            # Deduplication index
            await self.collection.create_index(
                "dedup_hash",
                unique=True,
                name="dedup_hash_unique"
            )

            # Full-text search
            await self.collection.create_index(
                [("name", "text"), ("description", "text")],
                name="name_description_text"
            )

            # Source filtering
            await self.collection.create_index("source", name="source_index")

            # Recency sorting
            await self.collection.create_index(
                [("updated_at", -1)],
                name="updated_at_index"
            )

            # Price range filtering
            await self.collection.create_index(
                [("min_price", 1), ("max_price", 1)],
                name="price_range_index"
            )

            logger.info("Indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def _calculate_dedup_hash(self, name: str, source: str) -> str:
        """
        Calculate deduplication hash.

        Args:
            name: Product name
            source: Data source (instagram, aroma, voli, etc)

        Returns:
            MD5 hash of normalized name + source
        """
        combined = f"{name.lower().strip()}:{source.lower()}".encode('utf-8')
        return hashlib.md5(combined).hexdigest()

    async def save_product(self, data: dict) -> Optional[str]:
        """
        Save or update product with automatic deduplication.

        Args:
            data: Product data (must include 'name' and 'source')

        Returns:
            Product ID (string) or None if failed
        """
        try:
            name = data.get("name", "").strip()
            source = data.get("source", "").strip()

            if not name or not source:
                logger.error("Product name and source are required")
                return None

            dedup_hash = self._calculate_dedup_hash(name, source)

            # Check if product already exists
            existing = await self.collection.find_one({"dedup_hash": dedup_hash})

            if existing:
                # Update existing product
                return await self._update_product(existing["_id"], data, dedup_hash)
            else:
                # Create new product
                return await self._create_product(data, dedup_hash)

        except Exception as e:
            logger.error(f"Error saving product: {e}")
            return None

    async def _create_product(self, data: dict, dedup_hash: str) -> str:
        """Create new product in database."""
        now = datetime.utcnow()

        product_doc = {
            "name": data.get("name"),
            "description": data.get("description"),
            "category": data.get("category"),
            "image_url": data.get("image_url"),
            "source": data.get("source"),
            "dedup_hash": dedup_hash,
            "prices": data.get("prices", []),
            "current_prices": {},
            "min_price": float('inf'),
            "max_price": 0,
            "cheapest_store": None,
            "created_at": now,
            "updated_at": now
        }

        # Update price aggregates
        self._update_price_aggregates(product_doc)

        result = await self.collection.insert_one(product_doc)
        logger.info(f"Created product: {result.inserted_id}")
        return str(result.inserted_id)

    async def _update_product(self, product_id: ObjectId, data: dict, dedup_hash: str) -> str:
        """Update existing product with new price data."""
        try:
            # Get current product
            current = await self.collection.find_one({"_id": product_id})

            # Merge prices (avoid duplicates)
            new_prices = data.get("prices", [])
            existing_prices = current.get("prices", [])

            # Keep track of unique price observations
            merged_prices = list(existing_prices)
            for new_price in new_prices:
                # Check if price already exists (same store, price, timestamp)
                is_duplicate = any(
                    p.get("store") == new_price.get("store") and
                    p.get("price") == new_price.get("price") and
                    p.get("timestamp") == new_price.get("timestamp")
                    for p in merged_prices
                )
                if not is_duplicate:
                    merged_prices.append(new_price)

            # Update document
            update_doc = {
                "name": data.get("name", current["name"]),
                "description": data.get("description") or current.get("description"),
                "category": data.get("category") or current.get("category"),
                "image_url": data.get("image_url") or current.get("image_url"),
                "prices": merged_prices,
                "updated_at": datetime.utcnow()
            }

            # Create temp doc for price calculation
            temp_doc = {**current, **update_doc}
            self._update_price_aggregates(temp_doc)

            # Apply aggregates
            update_doc["current_prices"] = temp_doc["current_prices"]
            update_doc["min_price"] = temp_doc["min_price"]
            update_doc["max_price"] = temp_doc["max_price"]
            update_doc["cheapest_store"] = temp_doc["cheapest_store"]

            await self.collection.update_one(
                {"_id": product_id},
                {"$set": update_doc}
            )

            logger.info(f"Updated product: {product_id}")
            return str(product_id)

        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return str(product_id)

    def _update_price_aggregates(self, product_doc: dict) -> None:
        """Update price aggregates in product document."""
        prices = product_doc.get("prices", [])

        if not prices:
            product_doc["current_prices"] = {}
            product_doc["min_price"] = float('inf')
            product_doc["max_price"] = 0
            product_doc["cheapest_store"] = None
            return

        # Get latest price per store
        store_prices = {}
        for price in prices:
            store = price.get("store")
            if store:
                store_prices[store] = price.get("price")

        product_doc["current_prices"] = store_prices

        # Calculate min/max
        if store_prices:
            prices_list = list(store_prices.values())
            product_doc["min_price"] = min(prices_list)
            product_doc["max_price"] = max(prices_list)
            product_doc["cheapest_store"] = min(store_prices, key=store_prices.get)
        else:
            product_doc["min_price"] = float('inf')
            product_doc["max_price"] = 0
            product_doc["cheapest_store"] = None

    async def find_by_name(self, query: str, limit: int = 20) -> list[dict]:
        """
        Full-text search for products by name.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of products
        """
        try:
            cursor = self.collection.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)

            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def find_by_dedup_hash(self, dedup_hash: str) -> Optional[dict]:
        """Find product by deduplication hash."""
        return await self.collection.find_one({"dedup_hash": dedup_hash})

    async def find_by_source(self, source: str, limit: int = 100) -> list[dict]:
        """Find all products from specific source."""
        cursor = self.collection.find({"source": source}).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_by_price_range(
        self,
        min_price: float = 0,
        max_price: float = 9999,
        limit: int = 100
    ) -> list[dict]:
        """Find products within price range."""
        cursor = self.collection.find({
            "min_price": {"$gte": min_price},
            "max_price": {"$lte": max_price}
        }).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_by_id(self, product_id: str) -> Optional[dict]:
        """Get product by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(product_id)})
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            return None

    async def delete_by_id(self, product_id: str) -> bool:
        """Delete product by ID."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(product_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            return False