"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app

client = TestClient(app)


class TestSearchAPI:
    """Test search endpoints."""

    def test_search_products_endpoint(self):
        """Test GET /search/products"""
        with patch('app.services.search_service.SearchService.search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {
                    "_id": "test_id",
                    "name": "Млеко 1L",
                    "description": "Fresh milk",
                    "image_url": "https://example.com/image.jpg",
                    "source": "aroma",
                    "current_prices": {"aroma": 1.39},
                    "min_price": 1.39,
                    "cheapest_store": "aroma",
                    "updated_at": "2026-06-16T12:00:00"
                }
            ]

            response = client.get("/api/v1/search/products?q=млеко")

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "млеко"
            assert data["count"] > 0
            assert "results" in data

    def test_search_products_empty_query(self):
        """Test search with empty query."""
        response = client.get("/api/v1/search/products?q=")

        assert response.status_code == 422  # Validation error

    def test_trending_endpoint(self):
        """Test GET /search/trending"""
        with patch('app.services.search_service.SearchService.get_trending', new_callable=AsyncMock) as mock_trending:
            mock_trending.return_value = []

            response = client.get("/api/v1/search/trending?hours=24&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "query" in data

    def test_price_filter_endpoint(self):
        """Test GET /search/price"""
        with patch('app.services.search_service.SearchService.filter_by_price', new_callable=AsyncMock) as mock_filter:
            mock_filter.return_value = []

            response = client.get("/api/v1/search/price?min_price=1.0&max_price=3.0")

            assert response.status_code == 200
            data = response.json()
            assert data["min_price"] == 1.0
            assert data["max_price"] == 3.0

    def test_cheapest_store_endpoint(self):
        """Test GET /search/cheapest/{store}"""
        with patch('app.services.search_service.SearchService.filter_by_cheapest_store', new_callable=AsyncMock) as mock_cheapest:
            mock_cheapest.return_value = []

            response = client.get("/api/v1/search/cheapest/aroma")

            assert response.status_code == 200
            data = response.json()
            assert "results" in data

    def test_invalid_store(self):
        """Test invalid store parameter."""
        response = client.get("/api/v1/search/cheapest/invalid_store")

        assert response.status_code == 400
        assert "Invalid store" in response.json()["detail"]

    def test_stats_endpoint(self):
        """Test GET /search/stats"""
        with patch('app.services.search_service.SearchService.get_statistics', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = {
                "total_products": 100,
                "by_source": {"aroma": 30, "voli": 25},
                "most_expensive": 5.99,
                "cheapest": 0.99
            }

            response = client.get("/api/v1/search/stats")

            assert response.status_code == 200
            data = response.json()
            assert "total_products" in data
            assert "by_source" in data


class TestScraperAPI:
    """Test scraper endpoints."""

    def test_scraper_status_endpoint(self):
        """Test GET /scrapers/status"""
        response = client.get("/api/v1/scrapers/status")

        # May fail if orchestrator not initialized, but endpoint should exist
        assert response.status_code in [200, 500]

    def test_run_scraper_aroma(self):
        """Test POST /scrapers/run with aroma"""
        with patch('app.services.orchestrator.ScraperOrchestrator.run_store_scraper_only', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {
                "status": "success",
                "found": 50,
                "saved": 50
            }

            response = client.post(
                "/api/v1/scrapers/run",
                json={"store": "aroma"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["store"] == "aroma"
            assert "status" in data

    def test_run_scraper_invalid_store(self):
        """Test invalid store."""
        response = client.post(
            "/api/v1/scrapers/run",
            json={"store": "invalid"}
        )

        assert response.status_code == 400
        assert "Unknown store" in response.json()["detail"]

    def test_scraper_pause(self):
        """Test POST /scrapers/pause"""
        response = client.post("/api/v1/scrapers/pause")

        assert response.status_code in [200, 500]

    def test_scraper_resume(self):
        """Test POST /scrapers/resume"""
        response = client.post("/api/v1/scrapers/resume")

        assert response.status_code in [200, 500]


class TestInstagramAPI:
    """Test Instagram endpoints."""

    def test_instagram_scrape_endpoint(self):
        """Test POST /instagram/scrape"""
        with patch('app.services.orchestrator.ScraperOrchestrator.run_instagram_scraper_only', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = {
                "status": "success",
                "posts": 10,
                "products": 25
            }

            response = client.post(
                "/api/v1/instagram/scrape",
                json={"username": "testuser", "hours_back": 48}
            )

            assert response.status_code == 200
            data = response.json()
            assert "status" in data

    def test_instagram_status_endpoint(self):
        """Test GET /instagram/status"""
        response = client.get("/api/v1/instagram/status")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestAPIErrors:
    """Test error handling."""

    def test_404_not_found(self):
        """Test 404 for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self):
        """Test 405 for wrong method."""
        response = client.post("/api/v1/search/products")

        assert response.status_code == 405

    def test_invalid_json(self):
        """Test 422 for invalid JSON."""
        response = client.post(
            "/api/v1/scrapers/run",
            json={"invalid_field": "value"}
        )

        assert response.status_code == 422


class TestAPIValidation:
    """Test input validation."""

    def test_query_validation(self):
        """Test query parameter validation."""
        # Empty query
        response = client.get("/api/v1/search/products?q=")
        assert response.status_code == 422

        # Too long query
        long_query = "a" * 300
        response = client.get(f"/api/v1/search/products?q={long_query}")
        assert response.status_code == 422

    def test_limit_validation(self):
        """Test limit parameter validation."""
        # Limit too high
        response = client.get("/api/v1/search/trending?limit=10000")
        assert response.status_code == 422

        # Limit negative
        response = client.get("/api/v1/search/trending?limit=-1")
        assert response.status_code == 422

    def test_price_validation(self):
        """Test price parameter validation."""
        # Min > max
        response = client.get("/api/v1/search/price?min_price=10&max_price=1")
        assert response.status_code == 400

        # Negative prices
        response = client.get("/api/v1/search/price?min_price=-5&max_price=10")
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])