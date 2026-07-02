"""Unit tests for ProductService"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.product_service import ProductService


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    return MagicMock()


@pytest.fixture
def mock_collection():
    """Mock MongoDB collection"""
    return AsyncMock()


@pytest.fixture
def product_service(mock_db):
    """Create ProductService with mocked DB"""
    service = ProductService(mock_db)
    service.collection = AsyncMock()
    return service


class TestProductServiceDedup:
    """Test product deduplication logic"""

    def test_calculate_dedup_hash(self, product_service):
        """Test hash calculation"""
        hash1 = product_service._calculate_dedup_hash("Млеко 1L", "aroma")
        hash2 = product_service._calculate_dedup_hash("Млеко 1L", "aroma")
        hash3 = product_service._calculate_dedup_hash("Млеко 1L", "voli")

        assert hash1 == hash2  # Same input = same hash
        assert hash1 != hash3  # Different source = different hash
        assert len(hash1) == 32  # MD5 hash length

    def test_calculate_dedup_hash_case_insensitive(self, product_service):
        """Test hash is case-insensitive"""
        hash1 = product_service._calculate_dedup_hash("Млеко 1L", "aroma")
        hash2 = product_service._calculate_dedup_hash("МЛЕКО 1L", "AROMA")

        assert hash1 == hash2


class TestProductServicePriceAggregates:
    """Test price aggregation logic"""

    def test_update_price_aggregates_empty(self, product_service):
        """Test with no prices"""
        doc = {"prices": []}
        product_service._update_price_aggregates(doc)

        assert doc["current_prices"] == {}
        assert doc["min_price"] == float('inf')
        assert doc["max_price"] == 0
        assert doc["cheapest_store"] is None

    def test_update_price_aggregates_single(self, product_service):
        """Test with single price"""
        doc = {
            "prices": [
                {"store": "aroma", "price": 1.39}
            ]
        }
        product_service._update_price_aggregates(doc)

        assert doc["current_prices"] == {"aroma": 1.39}
        assert doc["min_price"] == 1.39
        assert doc["max_price"] == 1.39
        assert doc["cheapest_store"] == "aroma"

    def test_update_price_aggregates_multiple(self, product_service):
        """Test with multiple stores"""
        doc = {
            "prices": [
                {"store": "aroma", "price": 1.39},
                {"store": "voli", "price": 1.45},
                {"store": "hdl", "price": 1.35},
                {"store": "idea", "price": 1.50}
            ]
        }
        product_service._update_price_aggregates(doc)

        assert doc["current_prices"] == {
            "aroma": 1.39,
            "voli": 1.45,
            "hdl": 1.35,
            "idea": 1.50
        }
        assert doc["min_price"] == 1.35
        assert doc["max_price"] == 1.50
        assert doc["cheapest_store"] == "hdl"

    def test_update_price_aggregates_latest_per_store(self, product_service):
        """Test that latest price per store is used"""
        doc = {
            "prices": [
                {"store": "aroma", "price": 1.39, "timestamp": "2026-06-16T10:00:00"},
                {"store": "aroma", "price": 1.45, "timestamp": "2026-06-16T12:00:00"},
                {"store": "voli", "price": 1.40, "timestamp": "2026-06-16T10:00:00"}
            ]
        }
        product_service._update_price_aggregates(doc)

        # Should use latest aroma price
        assert doc["current_prices"]["aroma"] == 1.45
        assert doc["min_price"] == 1.40
        assert doc["cheapest_store"] == "voli"


class TestProductServiceCreate:
    """Test product creation"""

    @pytest.mark.asyncio
    async def test_create_product(self, product_service):
        """Test creating new product"""
        product_service.collection.insert_one = AsyncMock()
        product_service.collection.insert_one.return_value.inserted_id = "507f1f77bcf86cd799439011"

        data = {
            "name": "Млеко 1L",
            "source": "aroma",
            "description": "Свіжа молоко",
            "prices": [
                {"store": "aroma", "price": 1.39, "currency": "EUR", "timestamp": "2026-06-16T10:00:00"}
            ]
        }

        result = await product_service._create_product(data, "abc123")

        assert result == "507f1f77bcf86cd799439011"
        product_service.collection.insert_one.assert_called_once()

        # Verify document structure
        call_args = product_service.collection.insert_one.call_args
        inserted_doc = call_args[0][0]

        assert inserted_doc["name"] == "Млеко 1L"
        assert inserted_doc["dedup_hash"] == "abc123"
        assert inserted_doc["source"] == "aroma"
        assert inserted_doc["min_price"] == 1.39


class TestProductServiceUpdate:
    """Test product updates"""

    @pytest.mark.asyncio
    async def test_update_product_merge_prices(self, product_service):
        """Test that new prices are merged without duplicates"""
        from bson import ObjectId

        product_id = ObjectId()
        existing_doc = {
            "_id": product_id,
            "name": "Млеко 1L",
            "prices": [
                {"store": "aroma", "price": 1.39, "timestamp": "2026-06-16T10:00:00"}
            ],
            "current_prices": {},
            "min_price": 1.39,
            "max_price": 1.39
        }

        product_service.collection.find_one = AsyncMock(return_value=existing_doc)
        product_service.collection.update_one = AsyncMock()

        new_data = {
            "name": "Млеко 1L",
            "prices": [
                {"store": "voli", "price": 1.45, "timestamp": "2026-06-16T11:00:00"}
            ]
        }

        await product_service._update_product(product_id, new_data, "abc123")

        # Verify update was called
        product_service.collection.update_one.assert_called_once()
        call_args = product_service.collection.update_one.call_args

        # Check that prices were merged
        update_doc = call_args[0][1]["$set"]
        assert len(update_doc["prices"]) == 2  # Both prices should be there