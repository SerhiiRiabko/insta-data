"""User-facing Telegram copy (bot + messages the API sends), 4 languages.

The site has 6 locales; Montenegrin, Serbian and Bosnian share one Latin
"mne" text set in the bot (Telegram reports sr/bs/hr users the same way and
the copy differs by a letter or two). Admin-only messages are Ukrainian.
Counts are written as "товарів: 5" style to avoid plural rules.
"""

from typing import Optional

BOT_LANGS = ("ukr", "rus", "eng", "mne")

LANG_NAMES = {"ukr": "🇺🇦 Українська", "rus": "Русский", "eng": "🇬🇧 English", "mne": "🇲🇪 Crnogorski"}

COUNTRY_NAMES = {
    "UA": {"ukr": "🇺🇦 Україна", "rus": "🇺🇦 Украина", "eng": "🇺🇦 Ukraine", "mne": "🇺🇦 Ukrajina"},
    "ME": {"ukr": "🇲🇪 Чорногорія", "rus": "🇲🇪 Черногория", "eng": "🇲🇪 Montenegro", "mne": "🇲🇪 Crna Gora"},
}

PLAN_NAMES = {
    "free": {"ukr": "Безкоштовний", "rus": "Бесплатный", "eng": "Free", "mne": "Besplatni"},
    "compare": {"ukr": "Порівняння", "rus": "Сравнение", "eng": "Compare", "mne": "Poređenje"},
    "gold": {"ukr": "Gold", "rus": "Gold", "eng": "Gold", "mne": "Gold"},
}

TEXTS: dict[str, dict[str, str]] = {
    "welcome": {
        "ukr": "👋 Привіт! Я знаходжу ціни на продукти в супермаркетах.\n\nНапишіть назву товару, наприклад <b>молоко</b>, і оберіть магазин.",
        "rus": "👋 Привет! Я нахожу цены на продукты в супермаркетах.\n\nНапишите название товара, например <b>молоко</b>, и выберите магазин.",
        "eng": "👋 Hi! I find grocery prices in supermarkets.\n\nType a product name, e.g. <b>milk</b>, and pick a store.",
        "mne": "👋 Zdravo! Pronalazim cijene namirnica u supermarketima.\n\nNapišite naziv proizvoda, npr. <b>mlijeko</b>, i izaberite prodavnicu.",
    },
    "choose_country": {
        "ukr": "Оберіть країну, ціни якої шукати:",
        "rus": "Выберите страну, цены которой искать:",
        "eng": "Choose the country to search prices in:",
        "mne": "Izaberite zemlju za pretragu cijena:",
    },
    "country_set": {
        "ukr": "Країна: {country}. Тепер напишіть назву товару.",
        "rus": "Страна: {country}. Теперь напишите название товара.",
        "eng": "Country: {country}. Now type a product name.",
        "mne": "Zemlja: {country}. Sada napišite naziv proizvoda.",
    },
    "choose_lang": {
        "ukr": "Оберіть мову:",
        "rus": "Выберите язык:",
        "eng": "Choose a language:",
        "mne": "Izaberite jezik:",
    },
    "lang_set": {
        "ukr": "Мову змінено.",
        "rus": "Язык изменён.",
        "eng": "Language changed.",
        "mne": "Jezik je promijenjen.",
    },
    "help": {
        "ukr": "Напишіть назву товару — я покажу ціни.\n\n/country — країна\n/lang — мова\n/plan — тариф і оплата\n/lists — списки покупок (Gold)\n/site — увійти на сайт\n/paysupport — питання щодо оплати",
        "rus": "Напишите название товара — я покажу цены.\n\n/country — страна\n/lang — язык\n/plan — тариф и оплата\n/lists — списки покупок (Gold)\n/site — войти на сайт\n/paysupport — вопросы по оплате",
        "eng": "Type a product name and I'll show prices.\n\n/country — country\n/lang — language\n/plan — plan and payment\n/lists — shopping lists (Gold)\n/site — log in to the website\n/paysupport — payment questions",
        "mne": "Napišite naziv proizvoda i pokazaću cijene.\n\n/country — zemlja\n/lang — jezik\n/plan — paket i plaćanje\n/lists — liste za kupovinu (Gold)\n/site — prijava na sajt\n/paysupport — pitanja o plaćanju",
    },
    "no_results": {
        "ukr": "Нічого не знайдено за запитом «{q}». Спробуйте інше слово.",
        "rus": "Ничего не найдено по запросу «{q}». Попробуйте другое слово.",
        "eng": "Nothing found for “{q}”. Try another word.",
        "mne": "Ništa nije pronađeno za „{q}“. Pokušajte drugu riječ.",
    },
    "choose_store": {
        "ukr": "🔎 «{q}» — знайдено товарів: {n}.\nОберіть магазин:",
        "rus": "🔎 «{q}» — найдено товаров: {n}.\nВыберите магазин:",
        "eng": "🔎 “{q}” — products found: {n}.\nPick a store:",
        "mne": "🔎 „{q}“ — pronađeno proizvoda: {n}.\nIzaberite prodavnicu:",
    },
    "btn_unlock_compare": {
        "ukr": "🔓 Усі магазини одразу — {stars}⭐/міс",
        "rus": "🔓 Все магазины сразу — {stars}⭐/мес",
        "eng": "🔓 All stores at once — {stars}⭐/mo",
        "mne": "🔓 Sve prodavnice odjednom — {stars}⭐/mj",
    },
    "store_result": {
        "ukr": "🏪 <b>{store}</b> · «{q}»",
        "rus": "🏪 <b>{store}</b> · «{q}»",
        "eng": "🏪 <b>{store}</b> · “{q}”",
        "mne": "🏪 <b>{store}</b> · „{q}“",
    },
    "compare_result": {
        "ukr": "🔎 «{q}» — порівняння цін",
        "rus": "🔎 «{q}» — сравнение цен",
        "eng": "🔎 “{q}” — price comparison",
        "mne": "🔎 „{q}“ — poređenje cijena",
    },
    "more_results": {
        "ukr": "…і ще товарів: {n}. Уточніть запит, щоб звузити пошук.",
        "rus": "…и ещё товаров: {n}. Уточните запрос.",
        "eng": "…and {n} more. Refine the query to narrow it down.",
        "mne": "…i još proizvoda: {n}. Precizirajte upit.",
    },
    "free_footer": {
        "ukr": "Щоб подивитися інший магазин — напишіть товар ще раз.",
        "rus": "Чтобы посмотреть другой магазин — напишите товар ещё раз.",
        "eng": "To check another store, type the product again.",
        "mne": "Za drugu prodavnicu — ponovo napišite proizvod.",
    },
    "add_hint": {
        "ukr": "➕ Натисніть номер, щоб додати товар до списку.",
        "rus": "➕ Нажмите номер, чтобы добавить товар в список.",
        "eng": "➕ Tap a number to add the product to your list.",
        "mne": "➕ Pritisnite broj da dodate proizvod na listu.",
    },
    "query_expired": {
        "ukr": "Запит застарів — напишіть товар ще раз.",
        "rus": "Запрос устарел — напишите товар ещё раз.",
        "eng": "This search expired — type the product again.",
        "mne": "Pretraga je istekla — ponovo napišite proizvod.",
    },
    "added_to_list": {
        "ukr": "✅ Додано: {item}",
        "rus": "✅ Добавлено: {item}",
        "eng": "✅ Added: {item}",
        "mne": "✅ Dodato: {item}",
    },
    "already_in_list": {
        "ukr": "Цей товар уже є у списку.",
        "rus": "Этот товар уже в списке.",
        "eng": "This product is already on the list.",
        "mne": "Ovaj proizvod je već na listi.",
    },
    "gold_required": {
        "ukr": "🛒 Списки покупок і можливість ділитися ними доступні в тарифі <b>Gold</b> — {stars}⭐ або {eur} € на місяць.\n\n/plan — оформити",
        "rus": "🛒 Списки покупок и возможность делиться ими доступны в тарифе <b>Gold</b> — {stars}⭐ или {eur} € в месяц.\n\n/plan — оформить",
        "eng": "🛒 Shopping lists and sharing are part of <b>Gold</b> — {stars}⭐ or {eur} € a month.\n\n/plan — subscribe",
        "mne": "🛒 Liste za kupovinu i dijeljenje su dio paketa <b>Gold</b> — {stars}⭐ ili {eur} € mjesečno.\n\n/plan — pretplata",
    },
    "plan_status": {
        "ukr": "Ваш тариф: <b>{plan}</b>{until}",
        "rus": "Ваш тариф: <b>{plan}</b>{until}",
        "eng": "Your plan: <b>{plan}</b>{until}",
        "mne": "Vaš paket: <b>{plan}</b>{until}",
    },
    "plan_until": {"ukr": " · до {date}", "rus": " · до {date}", "eng": " · until {date}", "mne": " · do {date}"},
    "plan_forever": {"ukr": " · безстроково", "rus": " · бессрочно", "eng": " · no expiry", "mne": " · bez isteka"},
    "plans_offer": {
        "ukr": "<b>Порівняння</b> — ціни всіх магазинів поруч: {cs}⭐ або {ce} € на місяць.\n<b>Gold</b> — порівняння + списки покупок і шеринг: {gs}⭐ або {ge} € на місяць.\n\nТариф діє і в боті, і на сайті.",
        "rus": "<b>Сравнение</b> — цены всех магазинов рядом: {cs}⭐ или {ce} € в месяц.\n<b>Gold</b> — сравнение + списки покупок и шеринг: {gs}⭐ или {ge} € в месяц.\n\nТариф действует и в боте, и на сайте.",
        "eng": "<b>Compare</b> — every store's price side by side: {cs}⭐ or {ce} € a month.\n<b>Gold</b> — compare + shopping lists and sharing: {gs}⭐ or {ge} € a month.\n\nThe plan works both in the bot and on the website.",
        "mne": "<b>Poređenje</b> — cijene svih prodavnica uporedo: {cs}⭐ ili {ce} € mjesečno.\n<b>Gold</b> — poređenje + liste za kupovinu i dijeljenje: {gs}⭐ ili {ge} € mjesečno.\n\nPaket važi i u botu i na sajtu.",
    },
    "btn_stars": {
        "ukr": "⭐ {plan} — {stars}⭐/міс",
        "rus": "⭐ {plan} — {stars}⭐/мес",
        "eng": "⭐ {plan} — {stars}⭐/mo",
        "mne": "⭐ {plan} — {stars}⭐/mj",
    },
    "invoice_description": {
        "ukr": "Тариф «{plan}» у боті та на сайті Shop Price Online на 30 днів, з автопродовженням.",
        "rus": "Тариф «{plan}» в боте и на сайте Shop Price Online на 30 дней, с автопродлением.",
        "eng": "“{plan}” plan in the bot and on the Shop Price Online website for 30 days, renews automatically.",
        "mne": "Paket „{plan}“ u botu i na sajtu Shop Price Online na 30 dana, automatski se obnavlja.",
    },
    "payment_approved": {
        "ukr": "🎉 Оплату підтверджено! Тариф «{plan}» активний до {date}.",
        "rus": "🎉 Оплата подтверждена! Тариф «{plan}» активен до {date}.",
        "eng": "🎉 Payment confirmed! The “{plan}” plan is active until {date}.",
        "mne": "🎉 Uplata potvrđena! Paket „{plan}“ je aktivan do {date}.",
    },
    "payment_declined": {
        "ukr": "Запит на оплату тарифу «{plan}» відхилено. Якщо це помилка — напишіть @{support}.",
        "rus": "Запрос на оплату тарифа «{plan}» отклонён. Если это ошибка — напишите @{support}.",
        "eng": "The payment request for “{plan}” was declined. If that's a mistake, message @{support}.",
        "mne": "Zahtjev za plaćanje paketa „{plan}“ je odbijen. Ako je greška, pišite @{support}.",
    },
    "stars_thanks": {
        "ukr": "🎉 Дякуємо! Тариф «{plan}» активний до {date}.\nПідписка продовжується щомісяця — скасувати можна в налаштуваннях Telegram.",
        "rus": "🎉 Спасибо! Тариф «{plan}» активен до {date}.\nПодписка продлевается ежемесячно — отменить можно в настройках Telegram.",
        "eng": "🎉 Thank you! The “{plan}” plan is active until {date}.\nIt renews monthly — you can cancel any time in Telegram settings.",
        "mne": "🎉 Hvala! Paket „{plan}“ je aktivan do {date}.\nObnavlja se mjesečno — možete otkazati u podešavanjima Telegrama.",
    },
    "link_confirm": {
        "ukr": "Прив'язати цей Telegram до акаунта <b>{account}</b> на сайті?\n\n⚠️ Підтверджуйте, лише якщо ви самі щойно натиснули «Підключити Telegram» на сайті.",
        "rus": "Привязать этот Telegram к аккаунту <b>{account}</b> на сайте?\n\n⚠️ Подтверждайте, только если вы сами только что нажали «Подключить Telegram» на сайте.",
        "eng": "Link this Telegram to the website account <b>{account}</b>?\n\n⚠️ Only confirm if you just pressed “Connect Telegram” on the website yourself.",
        "mne": "Povezati ovaj Telegram sa nalogom <b>{account}</b> na sajtu?\n\n⚠️ Potvrdite samo ako ste upravo sami pritisnuli „Poveži Telegram“ na sajtu.",
    },
    "login_confirm": {
        "ukr": "Увійти на сайт Shop Price Online з цим Telegram?\n\n⚠️ Підтверджуйте, лише якщо ви самі щойно натиснули «Увійти через Telegram» на сайті.",
        "rus": "Войти на сайт Shop Price Online с этим Telegram?\n\n⚠️ Подтверждайте, только если вы сами только что нажали «Войти через Telegram» на сайте.",
        "eng": "Log in to the Shop Price Online website with this Telegram?\n\n⚠️ Only confirm if you just pressed “Log in with Telegram” on the website yourself.",
        "mne": "Prijaviti se na sajt Shop Price Online ovim Telegramom?\n\n⚠️ Potvrdite samo ako ste upravo sami pritisnuli „Prijava putem Telegrama“ na sajtu.",
    },
    "btn_confirm": {"ukr": "✅ Підтвердити", "rus": "✅ Подтвердить", "eng": "✅ Confirm", "mne": "✅ Potvrdi"},
    "btn_cancel": {"ukr": "✖️ Скасувати", "rus": "✖️ Отмена", "eng": "✖️ Cancel", "mne": "✖️ Otkaži"},
    "cancelled": {"ukr": "Скасовано.", "rus": "Отменено.", "eng": "Cancelled.", "mne": "Otkazano."},
    "link_done": {
        "ukr": "✅ Telegram прив'язано до акаунта {account}. Тариф і списки тепер спільні для бота й сайту.",
        "rus": "✅ Telegram привязан к аккаунту {account}. Тариф и списки теперь общие для бота и сайта.",
        "eng": "✅ Telegram is linked to {account}. Your plan and lists are now shared between the bot and the website.",
        "mne": "✅ Telegram je povezan sa nalogom {account}. Paket i liste su sada zajednički za bot i sajt.",
    },
    "link_elsewhere": {
        "ukr": "Цей Telegram уже прив'язаний до іншого акаунта на сайті.",
        "rus": "Этот Telegram уже привязан к другому аккаунту на сайте.",
        "eng": "This Telegram is already linked to another website account.",
        "mne": "Ovaj Telegram je već povezan sa drugim nalogom na sajtu.",
    },
    "login_done": {
        "ukr": "✅ Вхід підтверджено — поверніться в браузер.",
        "rus": "✅ Вход подтверждён — вернитесь в браузер.",
        "eng": "✅ Login confirmed — go back to your browser.",
        "mne": "✅ Prijava potvrđena — vratite se u pregledač.",
    },
    "token_invalid": {
        "ukr": "Посилання недійсне або застаріло. Спробуйте ще раз на сайті.",
        "rus": "Ссылка недействительна или устарела. Попробуйте ещё раз на сайте.",
        "eng": "This link is invalid or expired. Please try again on the website.",
        "mne": "Link nije važeći ili je istekao. Pokušajte ponovo na sajtu.",
    },
    "site_login": {
        "ukr": "Посилання для входу на сайт (одноразове, діє 10 хвилин):",
        "rus": "Ссылка для входа на сайт (одноразовая, действует 10 минут):",
        "eng": "Your website login link (single use, valid for 10 minutes):",
        "mne": "Link za prijavu na sajt (jednokratan, važi 10 minuta):",
    },
    "btn_open_site": {"ukr": "🌐 Відкрити сайт", "rus": "🌐 Открыть сайт", "eng": "🌐 Open website", "mne": "🌐 Otvori sajt"},
    "lists_empty": {
        "ukr": "У вас ще немає списків. Знайдіть товар і натисніть ➕ під результатом.",
        "rus": "У вас ещё нет списков. Найдите товар и нажмите ➕ под результатом.",
        "eng": "You have no lists yet. Search for a product and tap ➕ under the result.",
        "mne": "Još nemate lista. Pronađite proizvod i pritisnite ➕ ispod rezultata.",
    },
    "lists_title": {"ukr": "🛒 Ваші списки:", "rus": "🛒 Ваши списки:", "eng": "🛒 Your lists:", "mne": "🛒 Vaše liste:"},
    "list_untitled": {"ukr": "Мій список", "rus": "Мой список", "eng": "My list", "mne": "Moja lista"},
    "list_header": {
        "ukr": "🛒 <b>{name}</b> · куплено {done}/{n}",
        "rus": "🛒 <b>{name}</b> · куплено {done}/{n}",
        "eng": "🛒 <b>{name}</b> · bought {done}/{n}",
        "mne": "🛒 <b>{name}</b> · kupljeno {done}/{n}",
    },
    "list_total": {
        "ukr": "Найдешевше разом: <b>{total}</b>",
        "rus": "Дешевле всего вместе: <b>{total}</b>",
        "eng": "Cheapest total: <b>{total}</b>",
        "mne": "Najjeftinije ukupno: <b>{total}</b>",
    },
    "list_empty": {"ukr": "Список порожній.", "rus": "Список пуст.", "eng": "The list is empty.", "mne": "Lista je prazna."},
    "btn_share_list": {"ukr": "📤 Поділитися в чат", "rus": "📤 Поделиться в чат", "eng": "📤 Share to a chat", "mne": "📤 Podijeli u čet"},
    "btn_list_site": {"ukr": "🌐 На сайті", "rus": "🌐 На сайте", "eng": "🌐 On the website", "mne": "🌐 Na sajtu"},
    "list_received": {
        "ukr": "📩 {sender} ділиться з вами списком покупок:",
        "rus": "📩 {sender} делится с вами списком покупок:",
        "eng": "📩 {sender} shared a shopping list with you:",
        "mne": "📩 {sender} dijeli sa vama listu za kupovinu:",
    },
    "inline_need_gold": {
        "ukr": "Ділитися списками можна з тарифом Gold",
        "rus": "Делиться списками можно с тарифом Gold",
        "eng": "Sharing lists requires the Gold plan",
        "mne": "Dijeljenje lista zahtijeva Gold paket",
    },
    "inline_open_bot": {"ukr": "Відкрити бота", "rus": "Открыть бота", "eng": "Open the bot", "mne": "Otvori bot"},
    "btn_invite": {"ukr": "👥 Запросити", "rus": "👥 Пригласить", "eng": "👥 Invite", "mne": "👥 Pozovi"},
    "btn_leave": {"ukr": "🚪 Вийти зі списку", "rus": "🚪 Выйти из списка", "eng": "🚪 Leave the list", "mne": "🚪 Napusti listu"},
    "btn_open_in_bot": {"ukr": "🤖 Відкрити в боті", "rus": "🤖 Открыть в боте", "eng": "🤖 Open in the bot", "mne": "🤖 Otvori u botu"},
    "btn_send_invite": {"ukr": "📤 Надіслати запрошення", "rus": "📤 Отправить приглашение", "eng": "📤 Send the invitation", "mne": "📤 Pošalji pozivnicu"},
    "invite_text": {
        "ukr": "Надішліть це запрошення людині, з якою хочете вести список <b>{name}</b>. Посилання одноразове й діє 7 днів:\n{url}\n\nАбо поділіться списком у будь-якому чаті кнопкою «📤 Поділитися в чат» — його побачать усі учасники чату.",
        "rus": "Отправьте это приглашение человеку, с которым хотите вести список <b>{name}</b>. Ссылка одноразовая и действует 7 дней:\n{url}\n\nИли поделитесь списком в любом чате кнопкой «📤 Поделиться в чат» — его увидят все участники чата.",
        "eng": "Send this invitation to the person you want to share <b>{name}</b> with. The link works once and for 7 days:\n{url}\n\nOr post the list into any chat with “📤 Share to a chat” — everyone in that chat can open it.",
        "mne": "Pošaljite ovu pozivnicu osobi sa kojom želite da vodite listu <b>{name}</b>. Link je jednokratan i važi 7 dana:\n{url}\n\nIli podijelite listu u bilo kom četu dugmetom „📤 Podijeli u čet“ — vidjeće je svi u četu.",
    },
    "invite_share_text": {
        "ukr": "Приєднуйтесь до мого списку покупок «{name}» — відмічайте, що вже купили:",
        "rus": "Присоединяйтесь к моему списку покупок «{name}» — отмечайте, что уже купили:",
        "eng": "Join my shopping list “{name}” — tick off what you’ve bought:",
        "mne": "Pridružite se mojoj listi za kupovinu „{name}“ — označite šta ste kupili:",
    },
    "join_done": {
        "ukr": "✅ Вас додано до списку від {owner}. Він тепер є в /lists і на сайті, коли ви увійдете через Telegram.",
        "rus": "✅ Вас добавили в список от {owner}. Он теперь есть в /lists и на сайте, когда вы войдёте через Telegram.",
        "eng": "✅ You've joined {owner}'s list. It's in /lists now, and on the website once you log in with Telegram.",
        "mne": "✅ Pridružili ste se listi korisnika {owner}. Sada je u /lists i na sajtu kada se prijavite putem Telegrama.",
    },
    "member_joined": {
        "ukr": "👥 {member} приєднався до списку «{name}».",
        "rus": "👥 {member} присоединился к списку «{name}».",
        "eng": "👥 {member} joined your list “{name}”.",
        "mne": "👥 {member} se pridružio listi „{name}“.",
    },
    "invite_invalid": {
        "ukr": "Запрошення недійсне, уже використане або застаріло. Попросіть власника списку надіслати нове.",
        "rus": "Приглашение недействительно, уже использовано или устарело. Попросите владельца списка отправить новое.",
        "eng": "This invitation is invalid, already used or expired. Ask the list's owner for a new one.",
        "mne": "Pozivnica nije važeća, već je iskorišćena ili je istekla. Zamolite vlasnika liste za novu.",
    },
    "list_private": {
        "ukr": "🔒 Це приватний список. Його бачать лише власник і ті, з ким він поділився.",
        "rus": "🔒 Это приватный список. Его видят только владелец и те, с кем он поделился.",
        "eng": "🔒 This list is private — only its owner and the people they shared it with can see it.",
        "mne": "🔒 Ovo je privatna lista — vide je samo vlasnik i oni sa kojima ju je podijelio.",
    },
    "left_list": {"ukr": "Ви вийшли зі списку.", "rus": "Вы вышли из списка.", "eng": "You left the list.", "mne": "Napustili ste listu."},
    "list_shared_by": {"ukr": "від {owner}", "rus": "от {owner}", "eng": "by {owner}", "mne": "od {owner}"},
    "active_list_hint": {
        "ukr": "<i>➕ з пошуку додаватиме товари в цей список.</i>",
        "rus": "<i>➕ из поиска будет добавлять товары в этот список.</i>",
        "eng": "<i>➕ in search results now adds products to this list.</i>",
        "mne": "<i>➕ iz pretrage sada dodaje proizvode na ovu listu.</i>",
    },
    "added_to_named_list": {
        "ukr": "✅ {item} → «{list}»",
        "rus": "✅ {item} → «{list}»",
        "eng": "✅ {item} → “{list}”",
        "mne": "✅ {item} → „{list}“",
    },
    "list_readonly": {
        "ukr": "Додавати товари в цей список зараз не можна: у власника закінчився тариф Gold.",
        "rus": "Добавлять товары в этот список сейчас нельзя: у владельца закончился тариф Gold.",
        "eng": "Products can't be added to this list right now: the owner's Gold plan has ended.",
        "mne": "Na ovu listu se trenutno ne mogu dodavati proizvodi: vlasniku je istekao Gold paket.",
    },
    "paysupport": {
        "ukr": "З питань оплати, повернення коштів чи підписки пишіть @{support}.\nЗірки, витрачені на підписку, можна повернути протягом 7 днів, якщо тариф не використовувався.",
        "rus": "По вопросам оплаты, возврата средств или подписки пишите @{support}.\nЗвёзды, потраченные на подписку, можно вернуть в течение 7 дней, если тариф не использовался.",
        "eng": "For payment, refund or subscription questions, message @{support}.\nStars spent on a subscription can be refunded within 7 days if the plan wasn't used.",
        "mne": "Za pitanja o plaćanju, povraćaju ili pretplati pišite @{support}.\nZvjezdice potrošene na pretplatu mogu se vratiti u roku od 7 dana ako paket nije korišćen.",
    },
    "set_country_first": {
        "ukr": "Спершу оберіть країну.",
        "rus": "Сначала выберите страну.",
        "eng": "Choose a country first.",
        "mne": "Prvo izaberite zemlju.",
    },
}


def bot_lang(lang: Optional[str]) -> str:
    """Site locale (6) or bot locale (4) -> bot locale."""
    if lang in ("srb", "bos"):
        return "mne"
    return lang if lang in BOT_LANGS else "eng"


def t(lang: Optional[str], key: str, **kwargs) -> str:
    entry = TEXTS[key]
    text = entry.get(bot_lang(lang)) or entry["eng"]
    return text.format(**kwargs) if kwargs else text


def plan_name(lang: Optional[str], plan: str) -> str:
    return PLAN_NAMES[plan][bot_lang(lang)]


def country_name(lang: Optional[str], country: str) -> str:
    return COUNTRY_NAMES[country][bot_lang(lang)]


def format_date(value) -> str:
    return value.strftime("%d.%m.%Y")


def format_price(price: Optional[float], country: str) -> str:
    if price is None:
        return "—"
    amount = f"{price:.2f}".replace(".", ",")
    return f"{amount} ₴" if country == "UA" else f"€{amount}"
