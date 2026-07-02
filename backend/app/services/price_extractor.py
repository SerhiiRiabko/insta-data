"""Extract prices from images using Tesseract OCR."""

import asyncio
import io
import logging
import re
from typing import Optional
import httpx
from PIL import Image
import pytesseract
from app.core.config import settings

logger = logging.getLogger(__name__)

# Regex patterns for price extraction
PRICE_PATTERNS = {
    # EUR formats: 1,50€ or €1.50
    "eur": r"(?:€|EUR)\s*([0-9]{1,5}[.,][0-9]{2})|([0-9]{1,5}[.,][0-9]{2})\s*(?:€|EUR)",
    # Alternative: 1.50 EUR or 1,50 EUR
    "eur_alt": r"([0-9]{1,5}[.,][0-9]{2})\s*(?:€|EUR)",
    # Generic: any number with 2 decimals
    "generic": r"(?:^|\s|:)([0-9]{1,5}[.,][0-9]{2})(?:\s|€|$)",
}

# Product keywords to identify product names
PRODUCT_KEYWORDS = {
    "dairy": ["млеко", "йогурт", "масло", "сир", "cream", "milk", "yogurt", "cheese"],
    "bakery": ["хліб", "хлеб", "булка", "булочка", "bread", "bun", "pastry"],
    "meat": ["месо", "мясо", "колбаса", "сосиска", "meat", "sausage", "bacon"],
    "beverages": ["вода", "сок", "напиток", "water", "juice", "drink"],
}


class PriceExtractor:
    """Extract prices from product images using OCR."""

    def __init__(self):
        self.tesseract_cmd = getattr(settings, 'TESSERACT_CMD', None)
        if self.tesseract_cmd:
            pytesseract.pytesseract.pytesseract_cmd = self.tesseract_cmd

    async def extract_from_image_url(self, url: str) -> Optional[dict]:
        """
        Download image from URL and extract prices.

        Args:
            url: Image URL

        Returns:
            Dict with extracted data or None
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                image_bytes = response.content

            image = Image.open(io.BytesIO(image_bytes))
            return await self.extract_from_image(image)

        except Exception as e:
            logger.error(f"Failed to download/process image {url}: {e}")
            return None

    async def extract_from_image(self, image: Image.Image) -> Optional[dict]:
        """
        Extract text and prices from PIL Image.

        Args:
            image: PIL Image object

        Returns:
            Dict with extracted prices and metadata
        """
        try:
            # Preprocess image for better OCR
            image = self._preprocess_image(image)

            # Run OCR
            text = await asyncio.to_thread(pytesseract.image_to_string, image, lang="ukr+rus+eng")

            if not text.strip():
                logger.warning("OCR returned empty text")
                return None

            # Extract prices
            prices = self._extract_prices(text)
            if not prices:
                logger.debug(f"No prices found in OCR text: {text[:100]}")
                return None

            # Extract product info
            product_name = self._extract_product_name(text)
            category = self._categorize_product(product_name, text)

            return {
                "product_name": product_name,
                "category": category,
                "prices": prices,
                "raw_text": text[:1000],  # Store first 1000 chars for debugging
                "confidence": self._calculate_confidence(prices, text)
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return None

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy."""
        try:
            # Resize if too small
            if image.width < 200 or image.height < 200:
                image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)

            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')

            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image

    def _extract_prices(self, text: str) -> list[dict]:
        """
        Extract EUR prices from OCR text.

        Returns:
            List of dicts: {"value": float, "currency": "EUR", "raw": str}
        """
        prices = []
        seen = set()

        for pattern_name, pattern in PRICE_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                # Extract price value from groups
                price_str = None
                for group in match.groups():
                    if group:
                        price_str = group
                        break

                if not price_str:
                    continue

                try:
                    # Normalize: replace comma with dot
                    price_str_normalized = price_str.replace(",", ".")
                    price_value = float(price_str_normalized)

                    # Sanity check: price between 0.01 and 9999.99 EUR
                    if 0.01 <= price_value <= 9999.99:
                        if price_str not in seen:
                            prices.append({
                                "value": round(price_value, 2),
                                "currency": "EUR",
                                "raw": price_str
                            })
                            seen.add(price_str)
                except ValueError:
                    continue

        return prices

    def _extract_product_name(self, text: str) -> str:
        """Extract product name from OCR text."""
        lines = text.strip().split('\n')

        # Try to find product name in first few lines
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 3 and len(line) < 200:
                # Check if line contains keywords
                for keywords in PRODUCT_KEYWORDS.values():
                    if any(kw.lower() in line.lower() for kw in keywords):
                        return line

        # Fallback: first non-empty line
        for line in lines:
            line = line.strip()
            if 3 < len(line) < 200 and not line[0].isdigit():
                return line

        return "Unknown Product"

    def _categorize_product(self, name: str, text: str) -> Optional[str]:
        """Categorize product based on name and context."""
        combined = (name + " " + text).lower()

        for category, keywords in PRODUCT_KEYWORDS.items():
            if any(kw.lower() in combined for kw in keywords):
                return category

        return None

    def _calculate_confidence(self, prices: list[dict], text: str) -> float:
        """
        Estimate OCR confidence (0-1).

        Higher if: more prices found, longer text
        """
        if not prices:
            return 0.0

        # Base confidence on number of prices
        price_confidence = min(len(prices) / 2, 1.0)  # Max at 2+ prices
        text_length = min(len(text) / 500, 1.0)  # Max at 500+ chars

        return (price_confidence + text_length) / 2