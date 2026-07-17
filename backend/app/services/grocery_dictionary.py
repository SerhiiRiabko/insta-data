"""
Word-level Montenegrin/Serbian -> ukr/rus/eng grocery-term dictionary.

Product names are scraped as "<generic item> <brand> <variant/descriptor>"
(e.g. "Mlijeko Imlek Moja kravica 2.8%" - "mlijeko" is the generic word,
everything else is brand/variant). This module translates only the generic
item words (and a handful of common descriptive adjectives) token-by-token,
leaving anything it doesn't recognise - brand names, model numbers, percents,
regional/variety names - untouched. That's deliberate: a brand name should
never be translated, and an unrecognised token is far more likely to be a
brand than a word missing from the dictionary.

This is the primary translator (no API key, no network call, deterministic)
- see translation_service.py for how it composes with the optional Groq AI
fallback for locales/words it doesn't cover.
"""

from typing import Optional

_DIACRITIC_MAP = str.maketrans({
    "č": "c", "ć": "c", "š": "s", "ž": "z", "đ": "dj",
    "Č": "c", "Ć": "c", "Š": "s", "Ž": "z", "Đ": "dj",
})

_STRIP_CHARS = ".,:;()\"'"


def _normalize(token: str) -> str:
    """Lowercase, strip surrounding punctuation, strip diacritics - so both
    'mliječni' and 'mlijecni' (ASCII-fallback spelling) hit the same key."""
    return token.strip(_STRIP_CHARS).lower().translate(_DIACRITIC_MAP)


# normalized (diacritic-stripped, lowercase) token -> {locale: translation}
GROCERY_TERMS: dict[str, dict[str, str]] = {
    # --- dairy ---
    "mlijeko": {"ukr": "Молоко", "rus": "Молоко", "eng": "Milk"},
    "mleko": {"ukr": "Молоко", "rus": "Молоко", "eng": "Milk"},
    "milk": {"ukr": "Молоко", "rus": "Молоко", "eng": "Milk"},
    "sir": {"ukr": "Сир", "rus": "Сыр", "eng": "Cheese"},
    "cheese": {"ukr": "Сир", "rus": "Сыр", "eng": "Cheese"},
    "jogurt": {"ukr": "Йогурт", "rus": "Йогурт", "eng": "Yogurt"},
    "yogurt": {"ukr": "Йогурт", "rus": "Йогурт", "eng": "Yogurt"},
    "maslac": {"ukr": "Вершкове масло", "rus": "Сливочное масло", "eng": "Butter"},
    "butter": {"ukr": "Вершкове масло", "rus": "Сливочное масло", "eng": "Butter"},
    "pavlaka": {"ukr": "Вершки", "rus": "Сливки", "eng": "Cream"},
    "kajmak": {"ukr": "Каймак", "rus": "Каймак", "eng": "Kaymak"},
    "kefir": {"ukr": "Кефір", "rus": "Кефир", "eng": "Kefir"},
    "ajran": {"ukr": "Айран", "rus": "Айран", "eng": "Ayran"},
    "puding": {"ukr": "Пудинг", "rus": "Пудинг", "eng": "Pudding"},
    "cokolada": {"ukr": "Шоколад", "rus": "Шоколад", "eng": "Chocolate"},
    "cokoladno": {"ukr": "Шоколадне", "rus": "Шоколадное", "eng": "Chocolate"},
    "kisjelo": {"ukr": "Кисле", "rus": "Кислое", "eng": "Sour"},
    "kisjela": {"ukr": "Кисла", "rus": "Кислая", "eng": "Sour"},
    "kisjeli": {"ukr": "Кислий", "rus": "Кислый", "eng": "Sour"},
    "edamer": {"ukr": "Едамер", "rus": "Эдамер", "eng": "Edam"},
    "gauda": {"ukr": "Гауда", "rus": "Гауда", "eng": "Gouda"},
    "mocarela": {"ukr": "Моцарела", "rus": "Моцарелла", "eng": "Mozzarella"},
    "feta": {"ukr": "Фета", "rus": "Фета", "eng": "Feta"},
    "punomasni": {"ukr": "Жирний", "rus": "Жирный", "eng": "Full-fat"},

    # --- bakery / staples ---
    "hljeb": {"ukr": "Хліб", "rus": "Хлеб", "eng": "Bread"},
    "bread": {"ukr": "Хліб", "rus": "Хлеб", "eng": "Bread"},
    "brasno": {"ukr": "Борошно", "rus": "Мука", "eng": "Flour"},
    "psenicno": {"ukr": "Пшеничне", "rus": "Пшеничная", "eng": "Wheat"},
    "integralni": {"ukr": "Цільнозерновий", "rus": "Цельнозерновой", "eng": "Wholegrain"},
    "whole": {"ukr": "Цільнозерновий", "rus": "Цельнозерновой", "eng": "Whole"},
    "grain": {"ukr": "Зерно", "rus": "Зерно", "eng": "Grain"},
    "tost": {"ukr": "Тост", "rus": "Тост", "eng": "Toast"},
    "makaroni": {"ukr": "Макарони", "rus": "Макароны", "eng": "Macaroni"},
    "farfalloni": {"ukr": "Фарфалле", "rus": "Фарфалле", "eng": "Farfalle"},
    "fusilli": {"ukr": "Фузилі", "rus": "Фузилли", "eng": "Fusilli"},
    "pirinac": {"ukr": "Рис", "rus": "Рис", "eng": "Rice"},
    "secer": {"ukr": "Цукор", "rus": "Сахар", "eng": "Sugar"},
    "sugar": {"ukr": "Цукор", "rus": "Сахар", "eng": "Sugar"},
    "vanilin": {"ukr": "Ванільний", "rus": "Ванильный", "eng": "Vanilla"},
    "kocka": {"ukr": "Кубик", "rus": "Кубик", "eng": "Cube"},
    "kristal": {"ukr": "Кристалічний", "rus": "Кристаллический", "eng": "Crystal"},
    "so": {"ukr": "Сіль", "rus": "Соль", "eng": "Salt"},
    "kuhinjska": {"ukr": "Кухонна", "rus": "Кухонная", "eng": "Kitchen"},
    "ulje": {"ukr": "Олія", "rus": "Масло", "eng": "Oil"},
    "oil": {"ukr": "Олія", "rus": "Масло", "eng": "Oil"},
    "maslinovo": {"ukr": "Оливкова", "rus": "Оливковое", "eng": "Olive"},
    "olive": {"ukr": "Оливкова", "rus": "Оливковое", "eng": "Olive"},
    "suncokretovo": {"ukr": "Соняшникова", "rus": "Подсолнечное", "eng": "Sunflower"},
    "ekstra": {"ukr": "Екстра", "rus": "Экстра", "eng": "Extra"},
    "extra": {"ukr": "Екстра", "rus": "Экстра", "eng": "Extra"},
    "djevicansko": {"ukr": "Дівоча", "rus": "Девственное", "eng": "Virgin"},
    "kecap": {"ukr": "Кетчуп", "rus": "Кетчуп", "eng": "Ketchup"},
    "majonez": {"ukr": "Майонез", "rus": "Майонез", "eng": "Mayonnaise"},
    "margarin": {"ukr": "Маргарин", "rus": "Маргарин", "eng": "Margarine"},
    "sos": {"ukr": "Соус", "rus": "Соус", "eng": "Sauce"},
    "supa": {"ukr": "Суп", "rus": "Суп", "eng": "Soup"},
    "zacin": {"ukr": "Приправа", "rus": "Приправа", "eng": "Seasoning"},
    "prasak": {"ukr": "Порошок", "rus": "Порошок", "eng": "Powder"},
    "pecivo": {"ukr": "Випічка", "rus": "Выпечка", "eng": "Baking"},
    "ajvar": {"ukr": "Айвар", "rus": "Айвар", "eng": "Ajvar"},
    "kore": {"ukr": "Коржі", "rus": "Коржи", "eng": "Pastry sheets"},
    "pitu": {"ukr": "Пиріг", "rus": "Пирог", "eng": "Pie"},
    "basilico": {"ukr": "Базилік", "rus": "Базилик", "eng": "Basil"},
    "pesto": {"ukr": "Песто", "rus": "Песто", "eng": "Pesto"},
    "blagi": {"ukr": "М'який", "rus": "Мягкий", "eng": "Mild"},
    "delikates": {"ukr": "Делікатесний", "rus": "Деликатесный", "eng": "Deluxe"},
    "stoni": {"ukr": "Столовий", "rus": "Столовый", "eng": "Table"},
    "mljevena": {"ukr": "Мелена", "rus": "Молотая", "eng": "Ground"},
    "mljeveno": {"ukr": "Мелене", "rus": "Молотое", "eng": "Ground"},
    "dugo": {"ukr": "Довге", "rus": "Длинное", "eng": "Long"},
    "okruglo": {"ukr": "Кругле", "rus": "Круглое", "eng": "Round"},
    "zrno": {"ukr": "Зерно", "rus": "Зерно", "eng": "Grain"},
    "posna": {"ukr": "Пісна", "rus": "Постная", "eng": "Meatless"},

    # --- meat / fish ---
    "meso": {"ukr": "М'ясо", "rus": "Мясо", "eng": "Meat"},
    "pile": {"ukr": "Курча", "rus": "Цыплёнок", "eng": "Chicken"},
    "pileci": {"ukr": "Курячий", "rus": "Куриный", "eng": "Chicken"},
    "pileca": {"ukr": "Куряча", "rus": "Куриная", "eng": "Chicken"},
    "svinjski": {"ukr": "Свинячий", "rus": "Свиной", "eng": "Pork"},
    "govedja": {"ukr": "Яловичина", "rus": "Говядина", "eng": "Beef"},
    "govedji": {"ukr": "Яловичий", "rus": "Говяжий", "eng": "Beef"},
    "junecki": {"ukr": "Яловичина", "rus": "Говядина", "eng": "Beef"},
    "juneci": {"ukr": "Яловичина", "rus": "Говядина", "eng": "Beef"},
    "juneca": {"ukr": "Яловичина", "rus": "Говядина", "eng": "Beef"},
    "junece": {"ukr": "Яловичина", "rus": "Говядина", "eng": "Beef"},
    "riba": {"ukr": "Риба", "rus": "Рыба", "eng": "Fish"},
    "tuna": {"ukr": "Тунець", "rus": "Тунец", "eng": "Tuna"},
    "file": {"ukr": "Філе", "rus": "Филе", "eng": "Fillet"},
    "filet": {"ukr": "Філе", "rus": "Филе", "eng": "Fillet"},
    "kobasica": {"ukr": "Ковбаса", "rus": "Колбаса", "eng": "Sausage"},
    "pasteta": {"ukr": "Паштет", "rus": "Паштет", "eng": "Pate"},
    "sunka": {"ukr": "Шинка", "rus": "Ветчина", "eng": "Ham"},
    "sudzuk": {"ukr": "Суджук", "rus": "Суджук", "eng": "Sujuk"},
    "mortadela": {"ukr": "Мортадела", "rus": "Мортаделла", "eng": "Mortadella"},
    "maslinama": {"ukr": "Оливками", "rus": "Оливками", "eng": "Olives"},
    "masline": {"ukr": "Оливки", "rus": "Оливки", "eng": "Olives"},
    "gulas": {"ukr": "Гуляш", "rus": "Гуляш", "eng": "Goulash"},
    "plecka": {"ukr": "Лопатка", "rus": "Лопатка", "eng": "Shoulder"},
    "but": {"ukr": "Стегно", "rus": "Бедро", "eng": "Leg"},
    "vrat": {"ukr": "Шия", "rus": "Шея", "eng": "Neck"},
    "prsuta": {"ukr": "Прошуто", "rus": "Прошутто", "eng": "Prosciutto"},
    "skusa": {"ukr": "Скумбрія", "rus": "Скумбрия", "eng": "Mackerel"},
    "cajna": {"ukr": "Чайна", "rus": "Чайная", "eng": "Tea"},
    "miesano": {"ukr": "Змішане", "rus": "Смешанное", "eng": "Mixed"},
    "mijesano": {"ukr": "Змішане", "rus": "Смешанное", "eng": "Mixed"},

    # --- vegetables ---
    "paradajz": {"ukr": "Помідор", "rus": "Помидор", "eng": "Tomato"},
    "tomatoes": {"ukr": "Помідори", "rus": "Помидоры", "eng": "Tomatoes"},
    "krastavac": {"ukr": "Огірок", "rus": "Огурец", "eng": "Cucumber"},
    "paprika": {"ukr": "Перець", "rus": "Перец", "eng": "Pepper"},
    "luk": {"ukr": "Цибуля", "rus": "Лук", "eng": "Onion"},
    "krompir": {"ukr": "Картопля", "rus": "Картофель", "eng": "Potato"},
    "kupus": {"ukr": "Капуста", "rus": "Капуста", "eng": "Cabbage"},
    "spanac": {"ukr": "Шпинат", "rus": "Шпинат", "eng": "Spinach"},
    "tikvica": {"ukr": "Кабачок", "rus": "Кабачок", "eng": "Zucchini"},
    "patlidzan": {"ukr": "Баклажан", "rus": "Баклажан", "eng": "Eggplant"},
    "cvekla": {"ukr": "Буряк", "rus": "Свёкла", "eng": "Beet"},
    "celer": {"ukr": "Селера", "rus": "Сельдерей", "eng": "Celery"},
    "salata": {"ukr": "Салат", "rus": "Салат", "eng": "Salad"},
    "brokoli": {"ukr": "Броколі", "rus": "Брокколи", "eng": "Broccoli"},
    "karfiol": {"ukr": "Цвітна капуста", "rus": "Цветная капуста", "eng": "Cauliflower"},
    "grasak": {"ukr": "Горошок", "rus": "Горошек", "eng": "Peas"},
    "pasulj": {"ukr": "Квасоля", "rus": "Фасоль", "eng": "Beans"},
    "boranija": {"ukr": "Стручкова квасоля", "rus": "Стручковая фасоль", "eng": "Green beans"},
    "povrce": {"ukr": "Овочі", "rus": "Овощи", "eng": "Vegetables"},
    "bundeva": {"ukr": "Гарбуз", "rus": "Тыква", "eng": "Pumpkin"},
    "rotkvica": {"ukr": "Редиска", "rus": "Редиска", "eng": "Radish"},
    "praziluk": {"ukr": "Порей", "rus": "Порей", "eng": "Leek"},
    "sargarepa": {"ukr": "Морква", "rus": "Морковь", "eng": "Carrot"},
    "djumbir": {"ukr": "Імбир", "rus": "Имбирь", "eng": "Ginger"},
    "batat": {"ukr": "Батат", "rus": "Батат", "eng": "Sweet potato"},

    # --- fruits ---
    "jabuka": {"ukr": "Яблуко", "rus": "Яблоко", "eng": "Apple"},
    "kruska": {"ukr": "Груша", "rus": "Груша", "eng": "Pear"},
    "banana": {"ukr": "Банан", "rus": "Банан", "eng": "Banana"},
    "bananas": {"ukr": "Банани", "rus": "Бананы", "eng": "Bananas"},
    "pomorandza": {"ukr": "Апельсин", "rus": "Апельсин", "eng": "Orange"},
    "narandza": {"ukr": "Апельсин", "rus": "Апельсин", "eng": "Orange"},
    "orange": {"ukr": "Апельсин", "rus": "Апельсин", "eng": "Orange"},
    "limun": {"ukr": "Лимон", "rus": "Лимон", "eng": "Lemon"},
    "grejp": {"ukr": "Грейпфрут", "rus": "Грейпфрут", "eng": "Grapefruit"},
    "grejpfrut": {"ukr": "Грейпфрут", "rus": "Грейпфрут", "eng": "Grapefruit"},
    "grozdje": {"ukr": "Виноград", "rus": "Виноград", "eng": "Grapes"},
    "jagoda": {"ukr": "Полуниця", "rus": "Клубника", "eng": "Strawberry"},
    "malina": {"ukr": "Малина", "rus": "Малина", "eng": "Raspberry"},
    "borovnica": {"ukr": "Чорниця", "rus": "Черника", "eng": "Blueberry"},
    "breskva": {"ukr": "Персик", "rus": "Персик", "eng": "Peach"},
    "kajsija": {"ukr": "Абрикос", "rus": "Абрикос", "eng": "Apricot"},
    "sljiva": {"ukr": "Слива", "rus": "Слива", "eng": "Plum"},
    "lubenica": {"ukr": "Кавун", "rus": "Арбуз", "eng": "Watermelon"},
    "dinja": {"ukr": "Диня", "rus": "Дыня", "eng": "Melon"},
    "ananas": {"ukr": "Ананас", "rus": "Ананас", "eng": "Pineapple"},
    "kivi": {"ukr": "Ківі", "rus": "Киви", "eng": "Kiwi"},
    "mandarina": {"ukr": "Мандарин", "rus": "Мандарин", "eng": "Mandarin"},
    "voce": {"ukr": "Фрукти", "rus": "Фрукты", "eng": "Fruit"},
    "tresnje": {"ukr": "Черешня", "rus": "Черешня", "eng": "Cherries"},

    # --- beverages ---
    "sok": {"ukr": "Сік", "rus": "Сок", "eng": "Juice"},
    "juice": {"ukr": "Сік", "rus": "Сок", "eng": "Juice"},
    "voda": {"ukr": "Вода", "rus": "Вода", "eng": "Water"},
    "water": {"ukr": "Вода", "rus": "Вода", "eng": "Water"},
    "mineralna": {"ukr": "Мінеральна", "rus": "Минеральная", "eng": "Mineral"},
    "sparkling": {"ukr": "Газована", "rus": "Газированная", "eng": "Sparkling"},
    "kafa": {"ukr": "Кава", "rus": "Кофе", "eng": "Coffee"},
    "coffee": {"ukr": "Кава", "rus": "Кофе", "eng": "Coffee"},
    "caj": {"ukr": "Чай", "rus": "Чай", "eng": "Tea"},
    "ledeni": {"ukr": "Холодний", "rus": "Холодный", "eng": "Iced"},
    "hladna": {"ukr": "Холодна", "rus": "Холодная", "eng": "Cold"},
    "instant": {"ukr": "Розчинна", "rus": "Растворимый", "eng": "Instant"},
    "pivo": {"ukr": "Пиво", "rus": "Пиво", "eng": "Beer"},
    "vino": {"ukr": "Вино", "rus": "Вино", "eng": "Wine"},
    "viski": {"ukr": "Віскі", "rus": "Виски", "eng": "Whiskey"},
    "sirup": {"ukr": "Сироп", "rus": "Сироп", "eng": "Syrup"},
    "multivitamin": {"ukr": "Мультивітамін", "rus": "Мультивитамин", "eng": "Multivitamin"},
    "svijetlo": {"ukr": "Світле", "rus": "Светлое", "eng": "Light"},

    # --- snacks / sweets ---
    "keks": {"ukr": "Печиво", "rus": "Печенье", "eng": "Biscuit"},
    "cips": {"ukr": "Чіпси", "rus": "Чипсы", "eng": "Chips"},
    "chips": {"ukr": "Чіпси", "rus": "Чипсы", "eng": "Chips"},
    "krem": {"ukr": "Крем", "rus": "Крем", "eng": "Cream"},
    "bombonjera": {"ukr": "Бонбоньєрка", "rus": "Бонбоньерка", "eng": "Box of chocolates"},
    "bonbonjera": {"ukr": "Бонбоньєрка", "rus": "Бонбоньерка", "eng": "Box of chocolates"},
    "napolitanke": {"ukr": "Наполітанки", "rus": "Наполитанки", "eng": "Wafers"},
    "dvopek": {"ukr": "Сухарики", "rus": "Сухарики", "eng": "Rusks"},
    "kikiriki": {"ukr": "Арахіс", "rus": "Арахис", "eng": "Peanuts"},
    "ljesnik": {"ukr": "Лісовий горіх", "rus": "Лесной орех", "eng": "Hazelnut"},
    "orah": {"ukr": "Горіх", "rus": "Орех", "eng": "Walnut"},
    "medenjaci": {"ukr": "Медяники", "rus": "Медовые пряники", "eng": "Gingerbread"},
    "marmelada": {"ukr": "Мармелад", "rus": "Мармелад", "eng": "Marmalade"},
    "pekmez": {"ukr": "Джем", "rus": "Джем", "eng": "Jam"},
    "sladoled": {"ukr": "Морозиво", "rus": "Мороженое", "eng": "Ice cream"},
    "stapici": {"ukr": "Палички", "rus": "Палочки", "eng": "Sticks"},
    "strudla": {"ukr": "Штрудель", "rus": "Штрудель", "eng": "Strudel"},
    "strudle": {"ukr": "Штрудель", "rus": "Штрудель", "eng": "Strudel"},
    "tortilja": {"ukr": "Тортилья", "rus": "Тортилья", "eng": "Tortilla"},
    "biskvit": {"ukr": "Бісквіт", "rus": "Бисквит", "eng": "Biscuit"},
    "kuglice": {"ukr": "Кульки", "rus": "Шарики", "eng": "Balls"},
    "meda": {"ukr": "Меду", "rus": "Мёда", "eng": "Honey"},
    "piskote": {"ukr": "Дамські пальчики", "rus": "Дамские пальчики", "eng": "Ladyfingers"},

    # --- hygiene / household ---
    "pelene": {"ukr": "Підгузки", "rus": "Подгузники", "eng": "Diapers"},
    "maramice": {"ukr": "Серветки", "rus": "Салфетки", "eng": "Wipes"},
    "vlazne": {"ukr": "Вологі", "rus": "Влажные", "eng": "Wet"},
    "sampon": {"ukr": "Шампунь", "rus": "Шампунь", "eng": "Shampoo"},
    "kosu": {"ukr": "Волосся", "rus": "Волосы", "eng": "Hair"},
    "sapun": {"ukr": "Мило", "rus": "Мыло", "eng": "Soap"},
    "ruke": {"ukr": "Руки", "rus": "Руки", "eng": "Hands"},
    "pasta": {"ukr": "Паста", "rus": "Паста", "eng": "Paste"},
    "zube": {"ukr": "Зуби", "rus": "Зубы", "eng": "Teeth"},
    "deterdzent": {"ukr": "Пральний порошок", "rus": "Стиральный порошок", "eng": "Detergent"},
    "omeksivac": {"ukr": "Пом'якшувач", "rus": "Кондиционер для белья", "eng": "Fabric softener"},
    "odmascivac": {"ukr": "Знежирювач", "rus": "Обезжириватель", "eng": "Degreaser"},
    "univerzalno": {"ukr": "Універсальний", "rus": "Универсальное", "eng": "Universal"},
    "sredstvo": {"ukr": "Засіб", "rus": "Средство", "eng": "Product"},
    "ciscenje": {"ukr": "Чищення", "rus": "Очистка", "eng": "Cleaning"},
    "papir": {"ukr": "Папір", "rus": "Бумага", "eng": "Paper"},
    "toalet": {"ukr": "Туалетний", "rus": "Туалетная", "eng": "Toilet"},
    "salvete": {"ukr": "Серветки", "rus": "Салфетки", "eng": "Napkins"},
    "ulosci": {"ukr": "Прокладки", "rus": "Прокладки", "eng": "Sanitary pads"},
    "kese": {"ukr": "Пакети", "rus": "Пакеты", "eng": "Bags"},
    "smece": {"ukr": "Сміття", "rus": "Мусор", "eng": "Garbage"},
    "tablete": {"ukr": "Таблетки", "rus": "Таблетки", "eng": "Tablets"},
    "sudje": {"ukr": "Посуд", "rus": "Посуда", "eng": "Dishes"},
    "ves": {"ukr": "Білизна", "rus": "Бельё", "eng": "Laundry"},
    "micelarna": {"ukr": "Міцелярна", "rus": "Мицеллярная", "eng": "Micellar"},
    "eggs": {"ukr": "Яйця", "rus": "Яйца", "eng": "Eggs"},
    "jaja": {"ukr": "Яйця", "rus": "Яйца", "eng": "Eggs"},
    "beans": {"ukr": "Боби", "rus": "Бобы", "eng": "Beans"},

    # --- common adjectives ---
    "bijeli": {"ukr": "Білий", "rus": "Белый", "eng": "White"},
    "bijela": {"ukr": "Біла", "rus": "Белая", "eng": "White"},
    "bijelo": {"ukr": "Біле", "rus": "Белое", "eng": "White"},
    "bijele": {"ukr": "Білі", "rus": "Белые", "eng": "White"},
    "crveni": {"ukr": "Червоний", "rus": "Красный", "eng": "Red"},
    "crvena": {"ukr": "Червона", "rus": "Красная", "eng": "Red"},
    "crno": {"ukr": "Чорне", "rus": "Чёрное", "eng": "Black"},
    "crni": {"ukr": "Чорний", "rus": "Чёрный", "eng": "Black"},
    "crna": {"ukr": "Чорна", "rus": "Чёрная", "eng": "Black"},
    "black": {"ukr": "Чорний", "rus": "Чёрный", "eng": "Black"},
    "zelena": {"ukr": "Зелена", "rus": "Зелёная", "eng": "Green"},
    "zeleni": {"ukr": "Зелений", "rus": "Зелёный", "eng": "Green"},
    "zuta": {"ukr": "Жовта", "rus": "Жёлтая", "eng": "Yellow"},
    "svieze": {"ukr": "Свіже", "rus": "Свежее", "eng": "Fresh"},
    "svjez": {"ukr": "Свіжий", "rus": "Свежий", "eng": "Fresh"},
    "svjezi": {"ukr": "Свіжий", "rus": "Свежий", "eng": "Fresh"},
    "svjeza": {"ukr": "Свіжа", "rus": "Свежая", "eng": "Fresh"},
    "fresh": {"ukr": "Свіжий", "rus": "Свежий", "eng": "Fresh"},
    "domaci": {"ukr": "Домашній", "rus": "Домашний", "eng": "Homemade"},
    "domaca": {"ukr": "Домашня", "rus": "Домашняя", "eng": "Homemade"},
    "ljuti": {"ukr": "Гострий", "rus": "Острый", "eng": "Spicy"},
    "gusti": {"ukr": "Густий", "rus": "Густой", "eng": "Thick"},
    "tecni": {"ukr": "Рідкий", "rus": "Жидкий", "eng": "Liquid"},
    "premium": {"ukr": "Преміум", "rus": "Премиум", "eng": "Premium"},
    "organic": {"ukr": "Органічний", "rus": "Органический", "eng": "Organic"},
    "organski": {"ukr": "Органічний", "rus": "Органический", "eng": "Organic"},
    "special": {"ukr": "Спеціальний", "rus": "Специальный", "eng": "Special"},
    "mini": {"ukr": "Міні", "rus": "Мини", "eng": "Mini"},
    "biljna": {"ukr": "Рослинна", "rus": "Растительная", "eng": "Plant-based"},
    "biljnom": {"ukr": "Рослинній", "rus": "Растительном", "eng": "Plant-based"},
    "zamrznuti": {"ukr": "Заморожений", "rus": "Замороженный", "eng": "Frozen"},
    "men": {"ukr": "Чоловічий", "rus": "Мужской", "eng": "Men"},
    "sensitive": {"ukr": "Чутлива", "rus": "Чувствительная", "eng": "Sensitive"},
    "shaving": {"ukr": "Для гоління", "rus": "Для бритья", "eng": "Shaving"},
    "foam": {"ukr": "Пінка", "rus": "Пена", "eng": "Foam"},
}


def translate_via_dictionary(name: str, target_locale: str) -> Optional[str]:
    """Translates the generic/descriptive words in `name` into
    `target_locale`, leaving anything not in the dictionary (brand names,
    model numbers, percentages, regional variety names) exactly as scraped.

    Returns None if not a single token in `name` matched the dictionary -
    callers should fall back to the source name (or an AI translator) in
    that case, since returning the untouched original wouldn't add value.
    """
    tokens = name.split()
    if not tokens:
        return None

    out_tokens = []
    matched_any = False

    for tok in tokens:
        key = _normalize(tok)
        entry = GROCERY_TERMS.get(key)
        if entry and target_locale in entry:
            out_tokens.append(entry[target_locale])
            matched_any = True
        else:
            out_tokens.append(tok)

    if not matched_any:
        return None

    return " ".join(out_tokens)