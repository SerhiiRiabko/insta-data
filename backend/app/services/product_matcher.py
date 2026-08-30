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

    # Ukrainian grocery synonyms - different stores genuinely use different
    # words for the same generic item (confirmed by browsing live category
    # pages: АТБ/Фора say "томат(и)", Novus/Varus say "помідор", Сільпо says
    # "томат"; АТБ/Varus/Сільпо all carry "лосось" AND "сьомга" as if
    # distinct). Matching is name-equality-based (see _generate_canonical_key
    # below), so without this, the exact same vegetable/fish silently never
    # matched across stores just because of which word a given retailer's
    # copywriter happened to use. Normalizes every form to ONE canonical word
    # (arbitrary pick - not "the correct" term) before matching; each pattern
    # is matched by root, not exact word, to cover Ukrainian case endings
    # (помідор/помідори/помідора/...).
    NAME_SYNONYMS = [
        (re.compile(r'помідор\w*', re.IGNORECASE), 'томат'),
        (re.compile(r'сьомг\w*', re.IGNORECASE), 'лосось'),
        # Meat-cut vocabulary (found by manually browsing Varus/Сільпо/Novus
        # meat pages): the exact same cut is grammatically inflected
        # differently store to store ("Ребро яловиче охолоджене" vs "Ребра
        # яловичі охолоджені") - root-based substitution to one canonical
        # form per concept, same pattern as томат/лосось above. Chilled vs
        # frozen is a real, price-relevant distinction, so they're
        # normalized to two DIFFERENT canonical forms, not merged together.
        # Word-bounded to "ребро/ребра/ребер/реберця/реберце" specifically -
        # a bare r'ребр\w*' would also catch unrelated words like
        # "ребристий" (ridge-cut, e.g. chips) and wrongly rename them.
        (re.compile(r'\bребр(?:о|а|ер|ц\w*)\b', re.IGNORECASE), 'ребро'),
        (re.compile(r'грудин\w*', re.IGNORECASE), 'грудинка'),
        (re.compile(r'ялович\w*', re.IGNORECASE), 'яловичина'),
        (re.compile(r'теляч\w*', re.IGNORECASE), 'телятина'),
        (re.compile(r'свин\w*', re.IGNORECASE), 'свинина'),
        (re.compile(r'охолодж\w*', re.IGNORECASE), 'охолоджений'),
        (re.compile(r'заморож\w*', re.IGNORECASE), 'заморожений'),
        (re.compile(r'копчен\w*', re.IGNORECASE), 'копчений'),
    ]

    # Words that describe how a product is sold/packaged, not what it is -
    # safe to drop entirely rather than substitute, since keeping them just
    # adds noise that blocks otherwise-identical names from matching (e.g.
    # "Яблуко Гала" vs "Яблуко Гала вагове" - same product either way).
    FILLER_WORDS_RE = re.compile(
        r'\b(ваговий|вагова|вагове|вагові|фасований|фасована|фасоване|фасовані)\b',
        re.IGNORECASE,
    )

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
                    'promo_by_store': {},
                }

            groups[canonical_key]['products'].append(product)

            # Add price for this store
            if 'current_prices' in product and product.get('source'):
                prices = product['current_prices']
                if isinstance(prices, dict):
                    for store, price in prices.items():
                        groups[canonical_key]['prices_by_store'][store] = price
                        groups[canonical_key]['promo_by_store'][store] = bool(product.get('is_promo'))
                elif isinstance(prices, (int, float)):
                    groups[canonical_key]['prices_by_store'][product['source']] = prices
                    groups[canonical_key]['promo_by_store'][product['source']] = bool(product.get('is_promo'))

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
        canonical_name, unit = self._extract_name_and_unit(
            self._strip_filler_words(self._apply_synonyms(name))
        )

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
            # Capitalize only the first character, not str.title(): title()
            # capitalizes every letter after a non-letter too, which mangles
            # categories with an apostrophe ("м'ясо" -> "М'Ясо" instead of
            # "М'ясо").
            'category': category[:1].upper() + category[1:] if category else category,
            'source': source,
        }

    # Trailing Ukrainian weight/volume unit, with or without a leading number
    # ("Картопля біла, кг" has no number - Fora prices it per kg without
    # putting the number in the title; "Молоко ... 900 г" does). The ASCII
    # unit_pattern below never matches Cyrillic letters at all, so without
    # this, every Ukrainian scraper's name kept its raw unit suffix attached
    # verbatim - and since two stores rarely format that suffix identically
    # (", кг" vs "900 г" vs no suffix at all when weight is a separate
    # field), otherwise-identical product names silently failed to match.
    CYRILLIC_TRAILING_UNIT_RE = re.compile(
        r'\s*,?\s*(за\s+)?\d*[.,]?\d*\s*(кг|г|л|мл|шт|уп|пак|пач)\.?\s*$',
        re.IGNORECASE,
    )

    def _apply_synonyms(self, name: str) -> str:
        """Replace known Ukrainian synonym words (see NAME_SYNONYMS) with one
        canonical form, root-based so case endings don't matter."""
        for pattern, canonical in self.NAME_SYNONYMS:
            name = pattern.sub(canonical, name)
        return name

    def _strip_filler_words(self, name: str) -> str:
        """Drop sale-format words (see FILLER_WORDS_RE) and collapse the
        resulting double spaces."""
        name = self.FILLER_WORDS_RE.sub('', name)
        return re.sub(r'\s+', ' ', name).strip()

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
            clean_name = self.CYRILLIC_TRAILING_UNIT_RE.sub('', clean_name).strip()
            return clean_name, f"{number}{unit}"

        clean_name = self.CYRILLIC_TRAILING_UNIT_RE.sub('', name).strip()
        if clean_name and clean_name != name:
            return clean_name, "1x"

        return name, "1x"

    def _generate_canonical_key(self, name: str, category: str) -> str:
        """
        Generate a canonical key for grouping products.
        Combines normalized name and category.

        Tokens are sorted before joining, so word order doesn't matter -
        different stores phrase the same product differently ("Вода
        мінеральна Моршинська негазована" vs "Мінеральна вода Моршинська
        негазована"), and without this they'd never match despite being
        the exact same words.
        """
        # Remove special characters and extra spaces
        clean_name = re.sub(r'[^\w\s]', '', name.lower())
        tokens = sorted(clean_name.split())
        clean_name = '_'.join(tokens)
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
