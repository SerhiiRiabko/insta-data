"""
Product Matching Engine for cross-store product grouping.
Groups products by fuzzy name matching and normalizes data.
"""

import hashlib
import re
from typing import Dict, List, Optional, Tuple
from fuzzywuzzy import fuzz
from app.models.product import Product


class ProductMatcherService:
    """
    Matches products across different stores using fuzzy string matching.
    Handles name normalization, unit standardization, and grouping.
    """

    # Unit conversions for standardization
    UNIT_MAPPING = {
        'l': 'L', 'lt': 'L', 'литр': 'L', 'литра': 'L',
        'ml': 'ml', 'мл': 'ml', 'мілілітр': 'ml',
        'g': 'g', 'gr': 'g', 'грам': 'g', 'грама': 'g',
        'kg': 'kg', 'кг': 'kg', 'кілограм': 'kg',
        'oz': 'oz', 'ounce': 'oz',
        'lb': 'lb', 'lbs': 'lb', 'фунт': 'lb',
        'pcs': 'pcs', 'шт': 'pcs', 'штук': 'pcs',
    }

    # Common brands/prefixes to extract
    BRAND_PATTERNS = {
        r'\b(kiš|киш)\b': 'Kiš',
        r'\b(danone|данон)\b': 'Danone',
        r'\b(aroma|арома)\b': 'Aroma',
        r'\b(zdravo|здраво)\b': 'Zdravo',
        r'\b(podgorica|подгориця)\b': 'Podgorica',
    }

    # Category keywords
    CATEGORY_KEYWORDS = {
        'dairy': ['milk', 'yogurt', 'cheese', 'butter', 'cream', 'sour',
                  'молоко', 'йогурт', 'сир', 'масло', 'крем', 'кисла'],
        'vegetables': ['tomato', 'cucumber', 'pepper', 'onion', 'garlic',
                       'помідор', 'огірок', 'перець', 'цибуля', 'часник'],
        'fruits': ['apple', 'banana', 'orange', 'grape', 'berry',
                   'яблуко', 'банан', 'апельсин', 'виноград', 'ягода'],
        'beverages': ['water', 'juice', 'tea', 'coffee', 'cola',
                      'вода', 'сік', 'чай', 'кава', 'кола'],
        'oils': ['oil', 'olive', 'sunflower', 'corn',
                 'масло', 'оливка', 'соняшник', 'кукурудза'],
        'bakery': ['bread', 'flour', 'pasta', 'rice',
                   'хліб', 'борошно', 'макарони', 'рис'],
    }

    def __init__(self, fuzzy_threshold: int = 85):
        """
        Initialize matcher with fuzzy matching threshold.

        Args:
            fuzzy_threshold: Similarity score (0-100) above which products match
        """
        self.fuzzy_threshold = fuzzy_threshold

    def group_products(self, products: List[Dict]) -> List[Dict]:
        """
        Group products across stores by matching names.

        Args:
            products: List of product dicts from database

        Returns:
            List of ProductGroup dicts with grouped prices
        """
        if not products:
            return []

        # Normalize all products
        normalized = [self._normalize_product(p) for p in products]

        # Group by canonical name
        groups = {}
        for product in normalized:
            canonical_key = product['canonical_key']

            if canonical_key not in groups:
                groups[canonical_key] = {
                    'id': self._generate_group_id(product['canonical_name'], product['category']),
                    'canonical_name': product['canonical_name'],
                    'category': product['category'],
                    'unit': product['unit'],
                    'products': [],
                    'prices_by_store': {},
                }

            groups[canonical_key]['products'].append(product)

            # Add price for this store
            if 'current_prices' in product and product.get('source'):
                prices = product['current_prices']
                if isinstance(prices, dict):
                    for store, price in prices.items():
                        groups[canonical_key]['prices_by_store'][store] = price
                elif isinstance(prices, (int, float)):
                    groups[canonical_key]['prices_by_store'][product['source']] = prices

        # Calculate aggregates for each group
        result = []
        for group in groups.values():
            if group['prices_by_store']:
                prices = [p for p in group['prices_by_store'].values() if p > 0]
                if prices:
                    group['min_price'] = min(prices)
                    group['max_price'] = max(prices)
                    group['cheapest_store'] = min(
                        group['prices_by_store'],
                        key=group['prices_by_store'].get
                    )

            result.append(group)

        # Sort by name
        result.sort(key=lambda x: x['canonical_name'])
        return result

    def _normalize_product(self, product: Dict) -> Dict:
        """Normalize a single product for matching."""
        name = product.get('name', '').strip()
        source = product.get('source', '').lower()
        category = product.get('category', 'Other').lower()

        # Extract canonical name and unit
        canonical_name, unit = self._extract_name_and_unit(name)

        # Generate canonical key for grouping
        canonical_key = self._generate_canonical_key(canonical_name, category)

        # Infer category from name if not provided
        if not category or category == 'other':
            inferred_cat = self._infer_category(canonical_name)
            category = inferred_cat or 'Other'

        return {
            **product,
            'canonical_name': canonical_name,
            'canonical_key': canonical_key,
            'unit': unit,
            'category': category.title(),
            'source': source,
        }

    def _extract_name_and_unit(self, name: str) -> Tuple[str, str]:
        """
        Extract product name and unit from full name string.

        Examples:
            "Milk 1L" → ("Milk", "1L")
            "Йогурт 500g" → ("Йогурт", "500g")
        """
        name = name.strip()

        # Match unit pattern: number + unit
        unit_pattern = r'\b(\d+(?:\.\d+)?)\s*([a-z]+)\b'
        match = re.search(unit_pattern, name, re.IGNORECASE)

        if match:
            number = match.group(1)
            unit = match.group(2).lower()
            unit = self.UNIT_MAPPING.get(unit, unit)

            # Remove unit from name
            clean_name = re.sub(unit_pattern, '', name, flags=re.IGNORECASE).strip()
            return clean_name, f"{number}{unit}"

        return name, "1x"

    def _generate_canonical_key(self, name: str, category: str) -> str:
        """
        Generate a canonical key for grouping products.
        Combines normalized name and category.
        """
        # Remove special characters and extra spaces
        clean_name = re.sub(r'[^\w\s]', '', name.lower())
        clean_name = re.sub(r'\s+', '_', clean_name).strip('_')
        clean_cat = re.sub(r'\s+', '_', category.lower()).strip('_')

        return f"{clean_name}_{clean_cat}"

    def _generate_group_id(self, name: str, category: str) -> str:
        """Generate a unique ID for product group using MD5 hash."""
        combined = f"{name.lower().strip()}:{category.lower().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _infer_category(self, name: str) -> Optional[str]:
        """Infer product category from name keywords."""
        name_lower = name.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category

        return None

    def match_products(self, product1: Dict, product2: Dict) -> Tuple[bool, int]:
        """
        Check if two products match using fuzzy matching.

        Returns:
            (is_match: bool, score: int)
        """
        name1 = product1.get('canonical_name', '').lower()
        name2 = product2.get('canonical_name', '').lower()

        if not name1 or not name2:
            return False, 0

        # Use token_sort_ratio to handle word order differences
        score = fuzz.token_sort_ratio(name1, name2)

        # Also check category
        cat1 = product1.get('category', '').lower()
        cat2 = product2.get('category', '').lower()

        # Adjust score if categories don't match
        if cat1 and cat2 and cat1 != cat2:
            score = max(0, score - 15)

        is_match = score >= self.fuzzy_threshold
        return is_match, score
