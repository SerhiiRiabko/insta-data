"""Unit tests for SearchService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from app.services.search_service import SearchService


@pytest.fixture
def mock_mongo_db():
    """Mock MongoDB database."""
    return MagicMock()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return AsyncMock()


@pytest.fixture
def search_service(mock_mongo_db, mock_redis):
    """Create SearchService with mocks."""
    service = SearchService(mock_mongo_db, mock_redis)
    service.collection = AsyncMock()
    return service


class TestSearchService:
    """Test search functionality."""

    @pytest.mark.asyncio
    async def test_search_with_cache_hit(self, search_service, mock_redis):
        """Test search with Redis cache hit."""
        cached_results = [
            {"_id": "1", "name": "Product 1"}
        ]

        with pytest.mock.patch.object(
            search_service, '_get_from_cache',
            return_value=cached_results
        ):
            results = await search_service.search("test", use_cache=True)

            assert results == cached_results

    @pytest.mark.asyncio
    async def test_search_no_cache_hit(self, search_service):
        """Test search without cache hit."""
        products = [
            {"_id": "1", "name": "Млеко 1L", "price": 1.50},
            {"_id": "2", "name": "Йогурт", "price": 2.00}
        ]

        search_service.collection.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
            return_value=products
        )

        with pytest.mock.patch.object(search_service, '_get_from_cache', return_value=None):
            with pytest.mock.patch.object(search_service, '_set_cache'):
                results = await search_service.search("млеко", use_cache=True)

                assert len(results) == 2
                assert results[0]["name"] == "Млеко 1L"

    @pytest.mark.asyncio
    async def test_search_with_source_filter(self, search_service):
        """Test search with source filter."""
        products = [
            {"_id": "1", "name": "Product 1", "source": "aroma"}
        ]

        search_service.collection.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
            return_value=products
        )

        with pytest.mock.patch.object(search_service, '_get_from_cache', return_value=None):
            with pytest.mock.patch.object(search_service, '_set_cache'):
                results = await search_service.search("product", source="aroma")

                # Verify find was called with source filter
                call_args = search_service.collection.find.call_args
                query = call_args[0][0]
                assert query.get("source") == "aroma"


class TestPriceFiltering:
    """Test price-based filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_price_range(self, search_service):
        """Test filtering by price range."""
        products = [
            {"_id": "1", "name": "Cheap", "min_price": 1.00, "max_price": 1.50},
            {"_id": "2", "name": "Expensive", "min_price": 5.00, "max_price": 6.00}
        ]

        search_service.collection.find.return_value.limit.return_value.to_list = AsyncMock(
            return_value=products
        )

        results = await search_service.filter_by_price(1.00, 6.00)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_filter_by_cheapest_store(self, search_service):
        """Test filtering by cheapest store."""
        products = [
            {"_id": "1", "name": "Product 1", "cheapest_store": "aroma"},
            {"_id": "2", "name": "Product 2", "cheapest_store": "aroma"}
        ]

        search_service.collection.find.return_value.limit.return_value.to_list = AsyncMock(
            return_value=products
        )

        results = await search_service.filter_by_cheapest_store("aroma")

        assert len(results) == 2
        for product in results:
            assert product["cheapest_store"] == "aroma"


class TestTrendingAndStats:
    """Test trending products and statistics."""

    @pytest.mark.asyncio
    async def test_get_trending(self, search_service):
        """Test getting trending products."""
        now = datetime.utcnow()
        products = [
            {"_id": "1", "name": "New Product", "updated_at": now},
            {"_id": "2", "name": "Recent Product", "updated_at": now - timedelta(hours=1)}
        ]

        search_service.collection.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
            return_value=products
        )

        results = await search_service.get_trending(hours=24)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_statistics(self, search_service):
        """Test getting statistics."""
        search_service.collection.count_documents = AsyncMock(return_value=100)
        search_service.collection.find_one = AsyncMock(return_value={"max_price": 10.0})

        stats = await search_service.get_statistics()

        assert stats["total_products"] == 100
        assert "by_source" in stats


class TestCaching:
    """Test Redis caching."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self, search_service, mock_redis):
        """Test setting and getting cache."""
        import json

        test_data = [{"id": "1", "name": "Test"}]

        # Mock Redis get
        mock_redis.get = AsyncMock(return_value=json.dumps(test_data))

        cached = await search_service._get_from_cache("test_key")

        assert cached == test_data

    @pytest.mark.asyncio
    async def test_cache_miss(self, search_service, mock_redis):
        """Test cache miss."""
        mock_redis.get = AsyncMock(return_value=None)

        cached = await search_service._get_from_cache("nonexistent")

        assert cached is None

    @pytest.mark.asyncio
    async def test_clear_cache(self, search_service, mock_redis):
        """Test clearing cache."""
        mock_redis.keys = AsyncMock(return_value=["key1", "key2"])
        mock_redis.delete = AsyncMock(return_value=2)

        cleared = await search_service.clear_cache("pattern:*")

        assert cleared == 2