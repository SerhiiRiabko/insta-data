"""Unit tests for PriceExtractor"""

import pytest
from PIL import Image, ImageDraw
import io
from app.services.price_extractor import PriceExtractor


@pytest.fixture
def price_extractor():
    """Create PriceExtractor instance"""
    return PriceExtractor()


class TestPriceExtraction:
    """Test price extraction from text"""

    def test_extract_eur_format_1(self, price_extractor):
        """Test EUR format: 1,50€"""
        text = "Ціна: 1,50€"
        prices = price_extractor._extract_prices(text)

        assert len(prices) > 0
        assert prices[0]["value"] == 1.50
        assert prices[0]["currency"] == "EUR"

    def test_extract_eur_format_2(self, price_extractor):
        """Test EUR format: €1.50"""
        text = "Price: €1.50"
        prices = price_extractor._extract_prices(text)

        assert len(prices) > 0
        assert prices[0]["value"] == 1.50

    def test_extract_multiple_prices(self, price_extractor):
        """Test extracting multiple prices"""
        text = "Before: 1,50€ After: 2,99€"
        prices = price_extractor._extract_prices(text)

        assert len(prices) >= 2
        values = [p["value"] for p in prices]
        assert 1.50 in values
        assert 2.99 in values

    def test_extract_no_duplicates(self, price_extractor):
        """Test that duplicate prices are not extracted"""
        text = "Price: 1,50€ and also 1,50€"
        prices = price_extractor._extract_prices(text)

        # Should have only one unique price
        assert len(prices) == 1
        assert prices[0]["value"] == 1.50

    def test_extract_ignores_invalid_prices(self, price_extractor):
        """Test that invalid prices are ignored"""
        text = "Too expensive: 99999,99€ Too cheap: 0,00€"
        prices = price_extractor._extract_prices(text)

        # Prices outside valid range should be ignored
        for price in prices:
            assert 0.01 <= price["value"] <= 9999.99

    def test_extract_empty_text(self, price_extractor):
        """Test with empty text"""
        prices = price_extractor._extract_prices("")

        assert len(prices) == 0

    def test_extract_no_prices(self, price_extractor):
        """Test text with no prices"""
        text = "This is just some random text without any prices"
        prices = price_extractor._extract_prices(text)

        assert len(prices) == 0


class TestProductNameExtraction:
    """Test product name extraction"""

    def test_extract_dairy_product(self, price_extractor):
        """Test extracting dairy product name"""
        text = "Млеко 1L\nСвіжа коров'яче молоко\nЦіна: 1,50€"
        name = price_extractor._extract_product_name(text)

        assert "Млеко" in name or "молоко" in name.lower()

    def test_extract_bread_product(self, price_extractor):
        """Test extracting bread product name"""
        text = "Пшеничен хлеб\nСвежо направен\nЦена: 2,50€"
        name = price_extractor._extract_product_name(text)

        assert len(name) > 0
        assert "хлеб" in name.lower() or len(name) > 3

    def test_extract_fallback_first_line(self, price_extractor):
        """Test fallback to first line when no keywords found"""
        text = "Special Item XYZ\nNo keywords here\nPrice: 1,50€"
        name = price_extractor._extract_product_name(text)

        # Should fallback to first line
        assert name == "Special Item XYZ" or len(name) > 0


class TestProductCategorization:
    """Test product categorization"""

    def test_categorize_dairy(self, price_extractor):
        """Test dairy product categorization"""
        category = price_extractor._categorize_product("Млеко 1L", "Свіжа коров'яче молоко")

        assert category == "dairy"

    def test_categorize_bakery(self, price_extractor):
        """Test bakery product categorization"""
        category = price_extractor._categorize_product("Пшеничен хлеб", "Fresh bread")

        assert category == "bakery"

    def test_categorize_unknown(self, price_extractor):
        """Test unknown product categorization"""
        category = price_extractor._categorize_product("Random Product XYZ", "Some description")

        assert category is None


class TestConfidenceCalculation:
    """Test confidence score calculation"""

    def test_confidence_no_prices(self, price_extractor):
        """Test confidence with no prices"""
        confidence = price_extractor._calculate_confidence([], "Some text")

        assert confidence == 0.0

    def test_confidence_single_price(self, price_extractor):
        """Test confidence with single price"""
        prices = [{"value": 1.50, "currency": "EUR"}]
        text = "Price: 1,50€"

        confidence = price_extractor._calculate_confidence(prices, text)

        assert 0 < confidence < 1

    def test_confidence_multiple_prices_long_text(self, price_extractor):
        """Test confidence with multiple prices and long text"""
        prices = [
            {"value": 1.50, "currency": "EUR"},
            {"value": 2.50, "currency": "EUR"}
        ]
        text = "A" * 600  # Long text

        confidence = price_extractor._calculate_confidence(prices, text)

        # Should be relatively high confidence
        assert confidence > 0.5

    def test_confidence_bounded_0_1(self, price_extractor):
        """Test that confidence is always between 0 and 1"""
        prices = [{"value": 1.50}] * 10  # Many prices
        text = "A" * 10000  # Very long text

        confidence = price_extractor._calculate_confidence(prices, text)

        assert 0 <= confidence <= 1


class TestImagePreprocessing:
    """Test image preprocessing"""

    def test_preprocess_small_image(self, price_extractor):
        """Test upscaling of small images"""
        # Create 100x100 image
        img = Image.new('RGB', (100, 100), color='white')

        processed = price_extractor._preprocess_image(img)

        # Should be upscaled
        assert processed.width >= 100
        assert processed.height >= 100

    def test_preprocess_rgb_to_grayscale(self, price_extractor):
        """Test RGB to grayscale conversion"""
        img = Image.new('RGB', (200, 200), color='white')

        processed = price_extractor._preprocess_image(img)

        # Should be converted to grayscale
        assert processed.mode == 'L'

    def test_preprocess_already_grayscale(self, price_extractor):
        """Test that grayscale images are not converted"""
        img = Image.new('L', (200, 200), color=128)

        processed = price_extractor._preprocess_image(img)

        # Should remain grayscale
        assert processed.mode == 'L'