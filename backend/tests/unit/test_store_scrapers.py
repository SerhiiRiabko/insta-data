"""Unit tests for store scrapers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.store_scrapers import StoreScraper, AromaScraper, VoliScraper, HDLScraper, IDEAScraper


class TestStoreScraperBase:
    """Test StoreScraper base class."""

    def test_scraper_initialization(self):
        """Test scraper initialization."""
        # Can't instantiate abstract class, so test with concrete scraper
        scraper = AromaScraper()

        assert scraper.store_name == "aroma"
        assert scraper.base_url == "https://www.aroma.me"
        assert scraper.timeout > 0
        assert scraper.retry_attempts > 0

    def test_normalize_price_basic(self):
        """Test price normalization."""
        scraper = AromaScraper()

        # Test various formats
        assert scraper.normalize_price("1.50") == 1.50
        assert scraper.normalize_price("1,50") == 1.50
        assert scraper.normalize_price("€1.50") == 1.50
        assert scraper.normalize_price("1.50€") == 1.50
        assert scraper.normalize_price("1.50 EUR") == 1.50

    def test_normalize_price_edge_cases(self):
        """Test price edge cases."""
        scraper = AromaScraper()

        assert scraper.normalize_price("") is None
        assert scraper.normalize_price("invalid") is None
        assert scraper.normalize_price(None) is None

    def test_normalize_product_data_valid(self):
        """Test product data normalization."""
        scraper = AromaScraper()

        raw = {
            "name": "Млеко 1L",
            "price": "1.50 EUR",
            "image_url": "https://example.com/image.jpg",
            "description": "Fresh milk"
        }

        result = scraper.normalize_product_data(raw)

        assert result is not None
        assert result["name"] == "Млеко 1L"
        assert result["prices"][0]["price"] == 1.50
        assert result["source"] == "aroma"

    def test_normalize_product_data_missing_fields(self):
        """Test product data with missing required fields."""
        scraper = AromaScraper()

        # Missing price
        raw = {"name": "Product"}
        assert scraper.normalize_product_data(raw) is None

        # Missing name
        raw = {"price": "1.50"}
        assert scraper.normalize_product_data(raw) is None


class TestAromaScraper:
    """Test Aroma store scraper."""

    @pytest.mark.asyncio
    async def test_aroma_initialization(self):
        """Test Aroma scraper initialization."""
        scraper = AromaScraper()

        assert scraper.store_name == "aroma"
        assert "aroma.me" in scraper.base_url

    def test_aroma_extract_from_nextjs(self):
        """Test extracting products from Next.js data."""
        scraper = AromaScraper()

        data = {
            "props": {
                "pageProps": {
                    "products": [
                        {
                            "name": "Млеко 1L",
                            "price": 1.50,
                            "image_url": "https://example.com/milk.jpg"
                        }
                    ]
                }
            }
        }

        products = []
        scraper._extract_from_nextjs(data, products)

        # Should find at least one product
        assert len(products) > 0


class TestVoliScraper:
    """Test Voli store scraper."""

    def test_voli_initialization(self):
        """Test Voli scraper initialization."""
        scraper = VoliScraper()

        assert scraper.store_name == "voli"
        assert "voli.me" in scraper.base_url


class TestHDLScraper:
    """Test HDL store scraper."""

    def test_hdl_initialization(self):
        """Test HDL scraper initialization."""
        scraper = HDLScraper()

        assert scraper.store_name == "hdl"
        assert "hdl.me" in scraper.base_url

    def test_hdl_extract_products(self):
        """Test extracting products from HDL data."""
        scraper = HDLScraper()

        data = {
            "catalog": [
                {
                    "name": "Млеко 1L",
                    "price": 1.50,
                    "image_url": "https://example.com/milk.jpg"
                }
            ]
        }

        products = []
        scraper._extract_products(data, products)

        assert len(products) > 0


class TestIDEAScraper:
    """Test IDEA store scraper."""

    def test_idea_initialization(self):
        """Test IDEA scraper initialization."""
        scraper = IDEAScraper()

        assert scraper.store_name == "idea"
        assert "idea.me" in scraper.base_url


class TestScraperCommon:
    """Test functionality common to all scrapers."""

    @pytest.mark.asyncio
    async def test_browser_initialization(self):
        """Test browser initialization (mocked)."""
        scraper = AromaScraper()

        with patch('app.services.store_scrapers.async_playwright') as mock_playwright:
            mock_context = AsyncMock()
            mock_playwright.return_value.__aenter__.return_value = mock_context
            mock_context.chromium.launch = AsyncMock()

            await scraper.init_browser()

            mock_context.chromium.launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_browser_closing(self):
        """Test browser closing."""
        scraper = AromaScraper()
        scraper.browser = AsyncMock()

        await scraper.close_browser()

        scraper.browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_with_requests(self):
        """Test fetching with httpx (no JS)."""
        scraper = AromaScraper()

        with patch('app.services.store_scrapers.httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.text = "<html>Test</html>"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            html = await scraper._fetch_with_requests("https://test.com")

            assert html == "<html>Test</html>"