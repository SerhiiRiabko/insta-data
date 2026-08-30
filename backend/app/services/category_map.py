"""
Maps cijene.me's own (Montenegrin) product categories to the Ukrainian
product-group taxonomy used in the app's UI.

cijene.me returns 10 categories (see props.categories on the home page).
Most map 1:1, except "Voće i povrće" (Fruit & vegetables), which cijene.me
keeps as a single category - we split it into separate "Овочі"/"Фрукти"
groups using a keyword list of common Montenegrin/Serbian produce names,
since that's the language product names actually come in. Names that don't
match either list fall back into a combined group rather than guessing.
"""

from typing import Optional

# cijene.me category name (as returned by categories_by_id, any case) -> our label.
CIJENE_CATEGORY_LABELS = {
    "osnovne namirnice": "Бакалія",
    "meso i riba": "М'ясо і риба",
    "mliječni proizvodi": "Молочка",
    "mlijecni proizvodi": "Молочка",  # ASCII fallback, no "č"/"ć"
    "slatkiši i grickalice": "Солодощі та снеки",
    "slatkisi i grickalice": "Солодощі та снеки",
    "mješovita pića": "Напої",
    "mjesovita pica": "Напої",
    "lična higijena": "Особиста гігієна",
    "licna higijena": "Особиста гігієна",
    "kućna hemija": "Побутова хімія",
    "kucna hemija": "Побутова хімія",
    "baby program": "Дитячі товари",
    "akcijske cijene": "Акції",
}

# The two variants of the combined cijene.me category we split ourselves.
_PRODUCE_CATEGORY_NAMES = {"voće i povrće", "voce i povrce"}

VEGETABLE_KEYWORDS = [
    "paradajz", "krastavac", "krastavci", "paprika", "luk", "krompir",
    "šargarepa", "sargarepa", "mrkva", "kupus", "spanać", "spanac",
    "tikvica", "patlidžan", "patlidzan", "batat", "cvekla", "celer",
    "salata", "brokoli", "karfiol", "grašak", "grasak", "pasulj",
    "boranija", "povrće", "povrce", "bundeva", "rotkvica", "praziluk",
]

FRUIT_KEYWORDS = [
    "jabuk", "kruš", "krus", "banana", "pomorandž", "pomorandz",
    "narandž", "narandz", "limun", "grejp", "grožđ", "grozdj", "groždj",
    "jagod", "malina", "borovnic", "breskv", "kajsij", "šljiv", "sljiv",
    "lubenic", "dinj", "ananas", "kivi", "mandarin", "voće", "voce",
    "grejpfrut", "nar ",
]

# Ukrainian equivalent, used by scrapers whose own site groups produce into
# one combined "fruits & vegetables" bucket (e.g. Novus's category is
# literally named that) instead of splitting it like the others do -
# splitting client-side here keeps the category consistent with
# Сільпо/Varus/Фора, which is what actually lets cross-store matching work
# (category is part of the product-matching key - see product_matcher.py).
VEGETABLE_KEYWORDS_UA = [
    "помідор", "томат", "огірок", "огірк", "перец", "перец", "цибул",
    "картопл", "морков", "капуст", "буряк", "часник", "кабачок", "гарбуз",
    "баклажан", "редис", "селера", "спарж", "кукурудза", "горох", "квасол",
    "зелен", "петрушк", "кріп", "салат", "шпинат", "броколі", "цвітн",
]

FRUIT_KEYWORDS_UA = [
    "яблук", "груш", "банан", "апельсин", "мандарин", "лимон", "грейпфрут",
    "виноград", "полуниц", "малин", "чорниц", "лохин", "персик", "абрикос",
    "слив", "кавун", "дин", "ананас", "ківі", "гранат", "інжир", "хурм",
    "авокадо", "манго", "фрукт",
]


def split_ua_produce_category(name: str, fallback: str = "Фрукти та овочі") -> str:
    """Classify one Ukrainian produce item as "Овочі" or "Фрукти" by keyword,
    falling back to the combined label when neither list matches (rather
    than guessing) - see VEGETABLE_KEYWORDS_UA/FRUIT_KEYWORDS_UA above."""
    name_lower = name.lower()
    if any(kw in name_lower for kw in VEGETABLE_KEYWORDS_UA):
        return "Овочі"
    if any(kw in name_lower for kw in FRUIT_KEYWORDS_UA):
        return "Фрукти"
    return fallback


def classify_group_category(raw_category: Optional[str], product_name: str) -> str:
    """
    Turn a scraper-supplied category into one of our Ukrainian product-group
    labels (e.g. "Овочі", "Фрукти").

    Montenegro's cijene.me categories come in Serbian/Montenegrin and get
    mapped below via CIJENE_CATEGORY_LABELS. The Ukrainian scrapers
    (АТБ/Сільпо/Varus) already assign our own Ukrainian labels directly (see
    e.g. atb_scraper.py CATEGORIES) - anything that isn't a recognized
    Montenegrin category key passes straight through instead of collapsing
    into "Інше", which used to happen to every single Ukrainian category.

    Note: by the time this runs, ProductMatcherService has already
    lowercased+title-cased the raw category - Python's str.title()
    capitalizes every letter after an apostrophe too (м'ясо -> М'Ясо, not
    М'ясо), which is why category labels containing "'" (М'ясо) look odd in
    CATEGORY_ORDER below; that's the actual value that arrives here.
    """
    if not raw_category:
        return "Інше"

    key = raw_category.strip().lower()

    if key in _PRODUCE_CATEGORY_NAMES:
        name_lower = product_name.lower()
        if any(kw in name_lower for kw in VEGETABLE_KEYWORDS):
            return "Овочі"
        if any(kw in name_lower for kw in FRUIT_KEYWORDS):
            return "Фрукти"
        return "Фрукти та овочі"  # couldn't tell which - keep combined rather than guess

    if key in CIJENE_CATEGORY_LABELS:
        return CIJENE_CATEGORY_LABELS[key]

    return raw_category.strip()


# Display order for the grouped response - matches the numbering the product
# owner asked for, with anything unmapped ("Інше") always last.
CATEGORY_ORDER = [
    "Овочі",
    "Фрукти",
    "Фрукти та овочі",
    "Молочка",
    "Сири",
    "Хлібобулочні вироби",
    "Бакалія",
    "Консервація",
    "Заморожені продукти",
    "Дитячі товари",
    "М'ясо і риба",
    "Солодощі та снеки",
    "Напої",
    "Особиста гігієна",
    "Побутова хімія",
    "Акції",
    "Інше",
]


def category_sort_key(name: str) -> int:
    try:
        return CATEGORY_ORDER.index(name)
    except ValueError:
        return len(CATEGORY_ORDER)