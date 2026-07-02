"""Product search and filtering service."""

import logging
from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SearchService:
    """Search products with full-text search and caching."""

    def __init__(self, mongo_db: AsyncIOMotorDatabase, redis_client=None):
        self.db = mongo_db
        self.redis = redis_client
        self.collection = mongo_db['products']
        self.cache_ttl = 300  # 5 minutes

    async def search(
        self,
        query: str,
        source: Optional[str] = None,
        limit: int = 20,
        use_cache: bool = True
    ) -> list[dict]:
        """
        Search products by name/description.

        Args:
            query: Search query
            source: Filter by source (instagram, aroma, voli, hdl, idea) or None for all
            limit: Max results
            use_cache: Use Redis cache

        Returns:
            List of matching products
        """
        # Check cache first
        cache_key = f"cache:search:{query}:{source or 'all'}"
        if use_cache and self.redis:
            cached = await self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Cache hit for: {query}")
                return cached

        # Build query
        search_filter = {"$text": {"$search": query}}
        if source:
            search_filter["source"] = source

        try:
            cursor = self.collection.find(
                search_filter,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)

            results = await cursor.to_list(length=limit)

            # Cache results
            if self.redis:
                await self._set_cache(cache_key, results)

            logger.info(f"Found {len(results)} products for: {query}")
            return results

        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            return []

    async def filter_by_price(
        self,
        min_price: float = 0,
        max_price: float = 9999,
        source: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Find products within price range.

        Args:
            min_price: Minimum price (EUR)
            max_price: Maximum price (EUR)
            source: Optional source filter
            limit: Max results

        Returns:
            List of products within price range
        """
        query = {
            "min_price": {"$gte": min_price},
            "max_price": {"$lte": max_price}
        }

        if source:
            query["source"] = source

        try:
            cursor = self.collection.find(query).limit(limit)
            results = await cursor.to_list(length=limit)
            logger.info(f"Found {len(results)} products in price range {min_price}-{max_price}")
            return results
        except Exception as e:
            logger.error(f"Price filter failed: {e}")
            return []

    async def filter_by_cheapest_store(
        self,
        store: str,
        limit: int = 100
    ) -> list[dict]:
        """
        Find products where specified store has lowest price.

        Args:
            store: Store name (aroma, voli, hdl, idea)
            limit: Max results

        Returns:
            Products where specified store is cheapest
        """
        try:
            cursor = self.collection.find(
                {"cheapest_store": store}
            ).limit(limit)

            results = await cursor.to_list(length=limit)
            return results
        except Exception as e:
            logger.error(f"Failed to filter by cheapest store: {e}")
            return []

    async def get_trending(self, hours: int = 24, limit: int = 20) -> list[dict]:
        """
        Get recently updated products (trending).

        Args:
            hours: How many hours back to search
            limit: Max results

        Returns:
            Recently updated products
        """
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        try:
            cursor = self.collection.find(
                {"updated_at": {"$gte": cutoff}}
            ).sort([("updated_at", -1)]).limit(limit)

            results = await cursor.to_list(length=limit)
            return results
        except Exception as e:
            logger.error(f"Failed to get trending products: {e}")
            return []

    async def get_price_history(self, product_id: str) -> Optional[dict]:
        """Get product with full price history."""
        from bson import ObjectId

        try:
            return await self.collection.find_one({"_id": ObjectId(product_id)})
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            return None

    async def get_by_source(self, source: str, limit: int = 100) -> list[dict]:
        """Get all products from specific source."""
        try:
            cursor = self.collection.find(
                {"source": source}
            ).sort([("updated_at", -1)]).limit(limit)

            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to get products from {source}: {e}")
            return []

    async def get_statistics(self) -> dict:
        """Get search/product statistics."""
        try:
            total = await self.collection.count_documents({})

            # Count by source
            sources = {}
            for source_name in ["instagram", "aroma", "voli", "hdl", "idea"]:
                count = await self.collection.count_documents({"source": source_name})
                sources[source_name] = count

            # Price ranges
            expensive = await self.collection.find_one(
                sort=[("max_price", -1)]
            )
            cheapest = await self.collection.find_one(
                sort=[("min_price", 1)]
            )

            return {
                "total_products": total,
                "by_source": sources,
                "most_expensive": expensive.get("max_price") if expensive else None,
                "cheapest": cheapest.get("min_price") if cheapest else None
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    async def _get_from_cache(self, key: str) -> Optional[list]:
        """Get results from Redis cache."""
        if not self.redis:
            return None

        try:
            import json
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug(f"Cache retrieve failed: {e}")

        return None

    async def _set_cache(self, key: str, data: list) -> None:
        """Save results to Redis cache."""
        if not self.redis:
            return

        try:
            import json
            await self.redis.setex(
                key,
                self.cache_ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.debug(f"Cache write failed: {e}")

    async def clear_cache(self, pattern: str = "cache:search:*") -> int:
        """Clear cache entries matching pattern."""
        if not self.redis:
            return 0

        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0