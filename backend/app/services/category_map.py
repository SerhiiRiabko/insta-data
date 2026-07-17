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


def classify_group_category(raw_category: Optional[str], product_name: str) -> str:
    """
    Turn a cijene.me category (e.g. "Voće i povrće") plus a product name into
    one of our Ukrainian product-group labels (e.g. "Овочі", "Фрукти").
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

    return CIJENE_CATEGORY_LABELS.get(key, "Інше")


# Display order for the grouped response - matches the numbering the product
# owner asked for, with anything unmapped ("Інше") always last.
CATEGORY_ORDER = [
    "Овочі",
    "Фрукти",
    "Фрукти та овочі",
    "Молочка",
    "Бакалія",
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