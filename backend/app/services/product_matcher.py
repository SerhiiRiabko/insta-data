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
        # АТБ writes plural "Томати" for most of its listings ("Томати
        # тепличні", "Томати рожеві") while other stores/synonyms above
        # settle on singular "томат" - without this, produce core-name
        # matching (first word only, see _simplify_core_name) treats
        # "Томати" and "Томат" as two different words and never merges them.
        (re.compile(r'томат\w*', re.IGNORECASE), 'томат'),
        (re.compile(r'сьомг\w*', re.IGNORECASE), 'лосось'),
        # Produce singular/plural (found live: АТБ writes "Огірки"/
        # "Кабачки"/"Баклажани", Сільпо/Varus write "Огірок"/"Кабачок"/
        # "Баклажан" - since _simplify_core_name reduces a produce name to
        # just its first word, an unnormalized plural never matches the
        # singular form used elsewhere). Ukrainian о/і "fleeting vowel"
        # alternation (огірок -> огірки, кабачок -> кабачки) means a plain
        # suffix strip can't derive one from the other, so these are
        # explicit pairs, same as томат/лосось above - added as they're
        # found rather than attempting general Ukrainian morphology.
        (re.compile(r'\bогірк(?:и|ів|а)\b', re.IGNORECASE), 'огірок'),
        (re.compile(r'\bкабачк(?:и|ів|а)\b', re.IGNORECASE), 'кабачок'),
        (re.compile(r'\bбаклажан(?:и|ів|а)\b', re.IGNORECASE), 'баклажан'),
        (re.compile(r'\bбуряк(?:и|ів|а)\b', re.IGNORECASE), 'буряк'),
        (re.compile(r'\bперц(?:і|ів|ю)\b', re.IGNORECASE), 'перець'),
        (re.compile(r'\bцибул(?:і|ь|ю)\b', re.IGNORECASE), 'цибуля'),
        (re.compile(r'\bморкв(?:и|і|ю)\b', re.IGNORECASE), 'морква'),
        (re.compile(r'\bкартопл(?:і|ь|ю)\b', re.IGNORECASE), 'картопля'),
        (re.compile(r'\bкапуст(?:и|і|у)\b', re.IGNORECASE), 'капуста'),
        (re.compile(r'\bяблук(?:а|ах)\b', re.IGNORECASE), 'яблуко'),
        (re.compile(r'\bгруш(?:і|ок|у)\b', re.IGNORECASE), 'груша'),
        (re.compile(r'\bкавун(?:и|ів|а)\b', re.IGNORECASE), 'кавун'),
        (re.compile(r'\bдин(?:і|ю)\b', re.IGNORECASE), 'диня'),
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
        # More cut-name plurals/cases (found in АТБ's listings, e.g.
        # "Крильця курячі" / "Гомілки курячі") - MEAT_CORE_WORDS below only
        # does exact-word matching, so without normalizing these to one
        # singular form first, the plural spelling never matches it.
        (re.compile(r'\bгомілк(?:а|и|у|ою|ах)\b', re.IGNORECASE), 'гомілка'),
        (re.compile(r'\bстегн(?:о|а|ах|ами)\b', re.IGNORECASE), 'стегно'),
        (re.compile(r'\bкрил(?:о|а|ьця|ець|ах)\b', re.IGNORECASE), 'крило'),
        (re.compile(r'\bчетвертин(?:а|и|ах)\b', re.IGNORECASE), 'четвертина'),
        (re.compile(r'\bтушк(?:а|и|ах|ою)\b', re.IGNORECASE), 'тушка'),
    ]

    # Words that describe how a product is sold/packaged, not what it is -
    # safe to drop entirely rather than substitute, since keeping them just
    # adds noise that blocks otherwise-identical names from matching (e.g.
    # "Яблуко Гала" vs "Яблуко Гала вагове" - same product either way).
    #
    # "напій"/"безалкогольний"/the Pepsi-brand line: user asked "чому пепсі
    # тільки в одному магазині" - every store phrases the same plain Pepsi
    # differently ("Напій газований Pepsi" / "Напій Pepsi сильногазований" /
    # "Напій Pepsi Пепсі-Кола безалкогольний сильногазований"), so none of
    # them shared an identical remaining word set even with order-
    # insensitive matching. These two never distinguish one drink from
    # another regardless of product type, so they're always dropped.
    FILLER_WORDS_RE = re.compile(
        r'\b(ваговий|вагова|вагове|вагові|фасований|фасована|фасоване|фасовані'
        r'|напій|напої|безалкогольний|безалкогольна|безалкогольне|безалкогольні'
        # Cyrillic brand name repeated alongside the Latin one that's
        # already in virtually every real listing ("Напій Pepsi Пепсі-
        # Кола безалкогольний...") - dropped as pure redundant repetition
        # rather than substituted (substituting would create a *second*
        # "pepsi" token instead of matching the single one everyone else
        # has).
        r'|пепсі-?кол\w*|пепсі\w*)\b',
        re.IGNORECASE,
    )

    # Carbonation words ("газований"/"сильногазований"/...) are NOT always
    # noise the way the words above are: for bottled water specifically,
    # still-vs-sparkling is a real, often price-different distinction (e.g.
    # "Вода Моршинська негазована" vs "...сильногазована" are genuinely
    # different SKUs) - stripping it there would wrongly merge them. For
    # everything else (soda, juice) it's just redundant ("сильногазований"
    # for a cola tells you nothing another cola listing doesn't already
    # imply), and different stores don't even use the same intensity word
    # for what's the same product, so it blocks matching instead of
    # describing a real difference. Only stripped when "вод" isn't in the
    # name (see _strip_filler_words) - a crude but effective proxy for
    # "is this water".
    CARBONATION_WORDS_RE = re.compile(
        r'\b(газований|газована|газоване|газовані'
        r'|сильногазований|сильногазована|сильногазоване|сильногазовані'
        r'|слабогазований|слабогазована|слабогазоване|слабогазовані'
        r'|негазований|негазована|негазоване|негазовані)\b',
        re.IGNORECASE,
    )

    # For Овочі/Фрукти/М'ясо і риба, the user explicitly asked to match on
    # the core product name only and ignore extra descriptive words (variety,
    # brand, "фермерське", origin, etc.) - a deliberate trade-off toward more
    # cross-store comparisons at the cost of conflating e.g. different apple
    # varieties into one row. Produce listings consistently lead with the
    # base noun ("Яблуко Гала", "Кавун Вогник"), so the first word alone is
    # the core name.
    PRODUCE_CATEGORIES = {'овочі', 'фрукти', 'фрукти та овочі'}

    # Meat/fish names don't follow one consistent word order across stores
    # ("Ребро яловиче" vs "Свинний фермерський биток" - cut can lead or
    # trail), so instead of taking the first N words, keep only the tokens
    # that are recognized cut/animal-type/fish vocabulary (after
    # NAME_SYNONYMS root normalization above) and drop everything else
    # (brand, "фермерське", "домашнє", quality-grade words, etc).
    MEAT_CATEGORIES = {"м'ясо і риба"}
    MEAT_CORE_WORDS = {
        # animal / poultry / fish types
        'яловичина', 'свинина', 'телятина', 'курятина', 'індичатина',
        'кролик', 'качка', 'гуска', 'лосось', 'оселедець', 'скумбрія',
        'тріска', 'минтай', 'судак', 'короп', 'тунець', 'дорадо', 'сібас',
        'креветки', 'мідії', 'кальмари', 'риба',
        # cuts / parts
        'ребро', 'грудинка', 'філе', 'стегно', 'гомілка', 'вирізка',
        'лопатка', 'окіст', 'шия', 'ошийок', 'спинка', 'крило', 'четвертина',
        'тушка', 'антрекот', 'биток', 'язик', 'печінка', 'серце', 'нирки',
        'фарш', 'стейк', 'корейка', 'рулька', 'підчеревина', 'шинка',
        'балик',
        # deli / sausages (their own category slugs feed into М'ясо і риба)
        'ковбаса', 'ковбаски', 'сосиски', 'сардельки', 'бекон', 'буженина',
        'паштет',
    }

    def _simplify_core_name(self, name: str, category: str) -> str:
        """Reduce a produce/meat name to just its core word(s) - see
        PRODUCE_CATEGORIES/MEAT_CATEGORIES above for why and how."""
        cat = (category or '').strip().lower()
        tokens = name.split()
        if not tokens:
            return name

        if cat in self.PRODUCE_CATEGORIES:
            return tokens[0]

        if cat in self.MEAT_CATEGORIES:
            core = [t for t in tokens if t.lower() in self.MEAT_CORE_WORDS]
            # Falls back to the untouched name when nothing recognized,
            # rather than the alternative of returning an empty string.
            return ' '.join(core) if core else name

        return name

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
        canonical_name = self._simplify_core_name(canonical_name, category)

        # Infer category from name if not provided
        if not category or category == 'other':
            inferred_cat = self._infer_category(canonical_name)
            category = inferred_cat or 'Other'

        # Eggs get shelved under "Молочка" by both the scrapers (Novus's own
        # "dairy-and-eggs" category) and by hand when collecting Сільпо/АТБ
        # data manually, matching how the physical stores group them - but
        # the user explicitly asked for eggs as their own category rather
        # than folded into dairy, so split them out here (before the key is
        # built, so eggs don't accidentally share a key with dairy) - same
        # pattern as the produce Овочі/Фрукти split.
        if category == "молочка" and re.search(r'\bяйц\w*|\bяєчн\w*', canonical_name, re.IGNORECASE):
            category = "яйця"

        # Generate canonical key for grouping
        canonical_key = self._generate_canonical_key(canonical_name, category)

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
        resulting double spaces. Carbonation words are only dropped for
        non-water products - see CARBONATION_WORDS_RE."""
        name = self.FILLER_WORDS_RE.sub('', name)
        if 'вод' not in name.lower():
            name = self.CARBONATION_WORDS_RE.sub('', name)
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
