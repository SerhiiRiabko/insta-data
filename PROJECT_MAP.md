# Insta-Data (Monte-Shop-Price) — Project Map

## ✅ v0.1.0 — Phase 1 завершена (2026-07-07)

Landing page (Variant A) + backend API + **реальний** скрейпінг цін через cijene.me (Aroma/Voli/HDL/IDEA) + MongoDB-персист з історією цін. Деталі — розділ [«Phase 1 Complete — v0.1.0»](#-phase-1-complete--v010-детальний-звіт-2026-07-07) внизу файлу.

**Статус:** Phase 1 ✅ (Landing Page) → Phase 2 ✅ (Backend + Data Seeding) → Phase 3 ✅ (Live real-data scraping через cijene.me + MongoDB-персист)

> ⚠️ Ця мапа довго містила вигадані/суперечливі дані (файл був закомічений одним махом 2026-07-02 з датою "2026-06-23"). Секції нижче виправлені за фактичним кодом станом на 2026-07-07.

---

## 📋 Реалізовано (Fase 1)

### Frontend — Landing Page

- ⚠️ **Design brief містить 3 варіації (A, B, C)**, але **в коді реалізована тільки Variant A** ("Photo-forward" — full-width hero + floating matrix). Variant B (split layout) і Variant C (immersive Kotor Bay band + mint section) існують лише як референс у `Landing page design brief/design_handoff_monte_shop_price_landing/*.dc.html` — вони НЕ перенесені в React. `LandingPageDesignBrief.tsx` містить лише одну функцію-компонент `VariationA`.
  - Три різні роути (`app/landing/page.tsx`, `app/[lang]/landing/page.tsx`, `app/[lang]/page.tsx`) рендерять цей самий один компонент — це не 3 варіації, а 3 точки входу на ту саму сторінку.

- ✅ **Price matrix (`PriceMatrixLanding.tsx`)**:
  - **HTML `<table>`** структура, inline CSS
  - **8 товарів** (молоко, хліб, яйця, сир Гауда, банани, кава, оливкова олія, вода) — точно за design brief, НЕ 10
  - **4 стовпці магазинів** (Aroma, Voli, HDL, IDEA) — 5-й стовпець Instagram, доданий у Phase 3, пізніше прибраний (2026-07-09, див. п.13 нижче): Instagram-мок дані виявились не окремим джерелом, а фейковими постами конкретних магазинів, тож атрибутовані реальному магазину замість окремої колонки
  - **Виділення найдешевшого** — зелене фонування (#d8f3e3) + accent border-left
  - **Null prices** — відображаються як "—" для недоступних товарів
  - Горизонтальні/вертикальні лінії між рядками/колонками

- ✅ **Модальні вікна (`ProductsModal.tsx`, `StoresModal.tsx`, `AboutModal.tsx`)** — повністю реалізовані компоненти (пошук/фільтрація, реальні URL магазинів aromamarketi.me / voli.me / digitalniletak.me / idea.co.me), НЕ просто "scaffolded" заглушки. Дрібні недоробки: кнопка "+ Add to list" у `ProductsModal` без `onClick`; довідники магазинів ще не включають Instagram як джерело.

- ✅ **Localization (i18n) — два стеки об'єднано в один (Phase 4.6, 2026-07-14):**
  - URL-локаль тепер єдине джерело істини: `lib/productMatrix.ts` експортує `type Lang = 'ukr'|'rus'|'mne'|'srb'|'bos'|'eng'` (6 локалей, збігається з next-intl кодами один-в-один), `LandingPageDesignBrief.tsx` читає її через `useParams()` і перемикач мов робить `router.push()` для зміни URL-сегмента замість локального `useState`. Перемикач — тепер `<select>` на 6 значень, а не 3 кнопки-пігулки (6 пігулок ламали б mobile-фікс з Phase 4.0).
  - Додано 6-у локаль `eng` (паралель до старого `en`) — `i18n.ts`, `next-intl.config.ts`, `locales/eng.json`.
  - Усі компоненти, що приймали `lang` як prop (`StoresModal`, `AboutModal`, `AuthModal`, `ShoppingListModal`, `ShoppingListView`, `PriceMatrixLanding`, `PriceCardsMobile`) імпортують спільний `Lang` замість локального `'ru'|'uk'|'en'`; хардкоджені `TRANSLATIONS`-об'єкти розширені з 3 до 6 мов. Bridge-функції в `ListPageClient.tsx` та `ShoppingListModal.tsx` видалені — `lang` **дорівнює** URL-локалі, мапінг більше не потрібен.
  - Деталі й повна верифікація: `PHASE_4_PLAN.md` → Phase 4.6.
  - ⚠️ Досі неживе (не рендериться, не видалено — окрема, нижчого пріоритету робота): дерево `Header.tsx`, `SearchBar.tsx`, `TabSwitcher.tsx`, `PriceMatrix.tsx`, `ProductCard.tsx`, `TrendingProducts.tsx`, яке коректно використовує `useTranslations()` з next-intl, але ніде не імпортується — мертвий код іншого (темного/смарагдового) дизайну з `DESIGN_EXTRACT.md`.

- ✅ **Tailwind CSS + Google Fonts**
  - Plus Jakarta Sans (UI text)
  - Space Grotesk (prices/numbers)
  - Brand color tokens (#0b6e4f accent, #0f3d2e deep, #edf6f1 mint, etc.)

- ✅ **Responsive дизайн**
  - Mobile-first approach
  - Padding/spacing adjustments для всіх екранів
  - Таблиця НЕ скролиться горизонтально (`overflow-x-auto` прибрано, замість цього `tableLayout: fixed`) — протилежне тому, що написано в design brief (там таблиця мала `overflow-x:auto`)

---

## 🎨 Design Decisions — Variant C

| Аспект | Реалізація |
|--------|-----------|
| **Background** | Kotor Bay фото + linear-gradient overlay (125deg, rgba(6,78,59,0.3-0.2)) |
| **Header Band** | Темнозелений (rgba(6,78,59,0.88)) immersive hero |
| **Table Section** | Mint фон (brand-mint/80) з backdrop-blur-lg |
| **Table Container** | Сірий фон 30% opacity (bg-gray-500/30) + white box (bg-white/99) |
| **Price Cells** | Inline CSS (32px font, explicit borders, inline left accent line) |
| **Cheapest Highlight** | Зелене фонування (#d8f3e3) + 6px accent border-left |
| **Store Chips** | Horizontal (flex row) з кольоровими бейджами (A, V, H, I) |

---

## 📁 File Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── [lang]/
│   │   │   └── landing/
│   │   │       ├── page.tsx          ← Landing page wrapper
│   │   │       └── layout.tsx        ← Layout for [lang] route
│   │   ├── layout.tsx                ← Global layout
│   │   └── globals.css               ← Global styles + Google Fonts
│   │
│   ├── components/
│   │   ├── PriceMatrixLanding.tsx    ← HTML <table> component (prices grid)
│   │   └── LandingPageDesignBrief.tsx← 3 design variations (A, B, C)
│   │
│   ├── i18n.ts                       ← i18n config (next-intl)
│   └── ...
│
├── tailwind.config.ts                ← Brand colors, fonts
├── next.config.js
├── package.json
└── .env.local
```

---

## 🔄 Component Details

### **PriceMatrixLanding.tsx**
**Призначення:** Tabular price comparison grid

**Props:**
- `products: Product[]` — Array of products with prices per store
- `stores: Store[]` — Array of 4 stores (Aroma, Voli, HDL, IDEA)
- `lang: 'ru' | 'uk' | 'en'` — Current language
- `accent?: string` — Brand accent color (default: #0b6e4f)

**Функціональність:**
- HTML `<table>` з bordar-collapse
- Inline CSS styles (для гарантованого рендерингу)
- Вертикальні лінії (border-right: 4px)
- Горизонтальні лінії (border-bottom: 4px)
- Cheapest price highlight (зелено + accent border)
- Null price handling (відображається як "—")
- Format prices за мовою (EUR comma vs. period)

---

### **LandingPageDesignBrief.tsx**
**Призначення:** landing page (Variant A) + мова/варіант селектор — див. виправлений опис у розділі «Реалізовано» вище (в коді існує лише `VariationA`, B/C — не перенесені).

**Mock Data (дефолтний стан до фетчу):**
- 8 товарів (`MOCK_PRODUCTS`, точний список нижче)
- 4 магазини (`MOCK_STORES` у фронтенді й бекенді: Aroma/Voli/HDL/IDEA) — раніше бекенд додавав 5-й (Instagram), прибрано 2026-07-09 (мок-дані з Instagram атрибутовані реальному магазину замість окремої колонки)
- Деякі товари недоступні не у всіх магазинах (null prices)

---

## 📝 Mock Data (fallback, коли бекенд недоступний)

### Products (8 items — MOCK_PRODUCTS, ідентичний в `LandingPageDesignBrief.tsx`, `backend/.../products.py` і `seed_products.py`)
- Молоко / Молоко / Milk — 1 л
- Хлеб / Хліб / Bread — 500 г
- Яйца / Яйця / Eggs — 10 шт
- Сыр Гауда / Сир Гауда / Gouda cheese — 1 кг
- Бананы / Банани / Bananas — 1 кг
- Кофе молотый / Кава мелена / Ground coffee — 250 г
- Оливковое масло / Оливкова олія / Olive oil — 1 л
- Вода / Вода / Water — 1,5 л

### Stores (4, усі — реальні ціни з cijene.me)
| Store | Badge | Color | Джерело |
|-------|-------|-------|---------|
| Aroma | A | #e11d48 (red) | cijene.me (реальні ціни) |
| Voli | V | #2563eb (blue) | cijene.me (реальні ціни) |
| HDL | H | #d97706 (orange) | cijene.me (реальні ціни, vendor slug `lakovic`) |
| IDEA | I | #0891b2 (cyan) | cijene.me (реальні ціни) |

> До 2026-07-09 був ще mock-стовпець «Instagram» — прибраний, бо його 15 фейкових «постів» не з'єднувались з жодним реальним товаром і тривіально ставали «найдешевшою ціною». Тепер ці мок-ціни атрибутовані реальному магазину, якого стосується пост (див. п.13 в «Phase 1 Complete» нижче).

---

---

## 🔧 IMPLEMENTATION ROADMAP — Фази розробки (2026-06-23 →)

### **Phase 2A: Modal Pages & Navigation** (1 неділя)
**Мета:** Реалізувати 3 сторінки при клікові на кнопки навігації

| Кнопка | Функціонал | Компонент |
|--------|-----------|-----------|
| **Товари** | Список товарів, згрупований за категоріями (Овочі/Фрукти/Молочка/Бакалія/...) | `ProductsModal.tsx` |
| **Магазини** | Таблиця магазинів + посилання на сайти | `StoresModal.tsx` |
| **Про проект** | Інформація по проекту, технічний стек | `AboutModal.tsx` |

**Технічно:**
- [ ] Створити модалі/сторінки за маршрутами (`/uk/products`, `/uk/stores`, `/uk/about`)
- [ ] Додати навігацію в header (3 кнопки → модалі)
- [ ] Mock data (товари, магазини з URL сайтів)

---

### **Phase 2B: Real Data Integration** ✅ ЗРОБЛЕНО (2026-07-07) — інакше, ніж планувалось

Замість окремого скрейпера на кожен магазин, знайшли **cijene.me** — офіційний портал порівняння цін по Чорногорії (Laravel + Inertia.js), який вже агрегує ціни всіх 4 магазинів. Один скрейпер (`backend/app/services/scrapers/cijene_scraper.py`) замінює всі 4 заплановані:

- **Як це працює:** сайт віддає дані не через HTML-парсинг, а як вбудований Inertia `data-page` JSON прямо в HTML — жодного Playwright/рендерингу браузера не потрібно, просто `aiohttp` GET + пагінація через `X-Inertia` заголовки (16 сторінок, ~790 store-priced товарів по Podgorica)
- З кожного товару беремо: повну назву, фото (`https://cijene.me/storage/{photo}`), і найдешевшу ціну по кожному з 4 магазинів (мапінг vendor slug → бренд: `aroma→Aroma, voli→Voli, lakovic→HDL, idea→IDEA` — так, у cijene.me внутрішній slug HDL це `lakovic`)
- `ProductMatcherService` (`backend/app/services/product_matcher.py`, fuzzy-matching на `fuzzywuzzy`) групує товари з різних магазинів під одну назву
- ~~Написати скрейпери для кожного сайту~~ → замінено одним агрегатором
- ✅ Нормалізація цін (EUR, decimal places) — робить cijene.me
- ✅ Дедуплікація/групування — `ProductMatcherService.group_products()`
- ✅ Зберігання у MongoDB — `_persist_live_products()` в `products.py` (upsert + bounded `price_history` на 30 знімків), запускається як фонова задача (fire-and-forget), щоб недоступна БД не гальмувала відповідь користувачу

---

### **Phase 2C: Shopping List Feature** (2 тижні)
**Мета:** Додати функціонал вибору товарів і порівняння магазинів

**Сценарій:**
1. **Вибір товарів** — checkbox/кард додати товар до списку покупок
2. **Обрати магазини** — toggles для вибору 1-4 магазинів
3. **Динамічна таблиця** — тільки обрані магазини + ціни
4. **Підсумок** — сума по кожному магазину + мінімум
5. **Червоні товари** — якщо товару нема в обраних магазинах

**Компоненти:**
- `ShoppingListModal.tsx` — модаль зі списком товарів
- `MagazineSelector.tsx` — вибір магазинів (toggles)
- `ShoppingListTable.tsx` — таблиця з динамічними колонками
- `ShoppingListSummary.tsx` — підсумок по магазинах

**Технічно:**
- [ ] State management (Redux/Zustand) для: selected items, selected stores
- [ ] Обчислення суми по магазинам
- [ ] Фільтрація товарів за наявністю в обраних магазинах
- [ ] Локальне збереження (localStorage)

---

### **Phase 3: Advanced Features** (後future)
- [ ] Збереження списків (БД)
- [ ] Email-уведомлення (price drops)
- [ ] Історія цін (графіки)
- [ ] Рекомендації (AI)

---

## 🚀 Наступні кроки (Phase 2+)

### Нижче — детальне розбиття у секції IMPLEMENTATION ROADMAP ↑

---

## 🛠️ Технічний стек

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15 + React 19 + TypeScript |
| **Styling** | Tailwind CSS 4 |
| **Localization** | next-intl підключений, але не з'єднаний з рендером (див. ⚠️ вище) — реально мова керується локальним `useState` |
| **Fonts** | Google Fonts (Plus Jakarta Sans, Space Grotesk) |
| **Backend** | ✅ FastAPI (`backend/`) — products/search endpoints, instagram/legacy-scrapers роутери опціональні (instagrapi конфліктує з pydantic v2) |
| **Scraping** | ✅ `cijene_scraper.py` (aiohttp + Inertia JSON, реальні дані 4 магазинів) + `instagram_mock_scraper.py` (мок) |
| **Database** | MongoDB (products + price_history, best-effort persist) — PostgreSQL підключений, але поки не використовується для даних |
| **Local dev server** | Backend localhost:8001 (uvicorn), Frontend localhost:3001 (Next.js) — порт 3000/8000 з `PORTS.md` часто зайнятий іншими проєктами на цій машині |

---

## 🔗 Важливі посилання

- **Landing Page (реально працює):** http://localhost:3001/ukr (backend на http://localhost:8001)
  - Валідні URL-префікси — тільки `/ukr`, `/rus`, `/mne` (next-intl locales); `/ru`, `/uk`, `/en` з попередніх версій цього файлу — **не існують**, і сама мова на сторінці однаково керується внутрішнім `useState`, не URL
- **API Docs:** http://localhost:8001/docs (Swagger, генерується FastAPI автоматично)
- **Figma Design:** (TBD)

---

## 📊 Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Landing page (Variant A) | ✅ | B/C — тільки в дизайн-брифі, не в коді |
| Мобільна версія (390px) | ✅ | `PriceCardsMobile.tsx` — картки замість таблиці, чіп-стрічка магазинів, ☰-меню; перемикання `hidden md:block`/`md:hidden` |
| Tailwind CSS pipeline | ✅ | Виправлено 2026-07-10 — раніше НЕ компілювався взагалі (відсутній `postcss.config`) |
| Price Matrix Table | ✅ | HTML table + inline CSS, фото-іконка, плашки-групи по категоріях, sticky-шапка магазинів, 4 реальні магазини (Instagram-стовпець прибрано 2026-07-09) |
| Store Chips (Horizontal) | ✅ | Color-coded badges |
| i18n (RU/UK/EN) | ⚠️ | Працює через локальний state; next-intl-роутинг підключений, але не з'єднаний |
| Responsive Layout | ✅ | Mobile-optimized |
| Mock Data (fallback) | ✅ | 8 products, коли бекенд/БД недоступні |
| Backend API | ✅ | FastAPI, `/api/v1/products/{matrix, matrix-live, matrix-cached, by-category, list}` |
| Real Data Scraping | ✅ | cijene.me (Aroma/Voli/HDL/IDEA); Instagram — mock-пости, атрибутовані реальному магазину (не окрема колонка) |
| MongoDB Persistence | ✅ | Best-effort upsert + 30-запис price_history, фонова задача, тепер зберігає й `category` |
| Групування за категоріями | ✅ | `/by-category` (backend) + `ProductsModal.tsx` (frontend, лениве завантаження при відкритті) |
| Кешоване завантаження + щотижневий планувальник | ✅ | `/matrix-cached` за замовчуванням; `APScheduler` — реальний скрейп щопонеділка 07:00 (Київ) + кнопка "Оновити ціни" вручну |
| User Features (wishlist, auth) | ⬜ | Не заплановано в поточному скоупі v0.1.0 |

---

## ✅ Phase 1 Complete — v0.1.0 (детальний звіт, 2026-07-07)

Версія узгоджена з `backend/app/main.py` (`FastAPI(version="0.1.0")`). Це перший наскрізний робочий зріз: лендінг → бекенд → реальний скрейпінг → (best-effort) персист.

**Що зроблено цієї фази, поверх того, що вже описано вище по файлу:**

1. **`cijene_scraper.py`** (новий файл) — реальний скрейпінг цін Aroma/Voli/HDL/IDEA через офіційний портал cijene.me (Inertia JSON, без браузера).
2. **`orchestrator.py`** переписаний — замість 4 mock-скрейперів реєструє `CijeneScraper` (реальні дані) + `InstagramMockScraper` (мок). Старі `aroma_mock_scraper.py`, `voli_mock_scraper.py`, `hdl_mock_scraper.py`, `idea_mock_scraper.py` — видалені.
3. **`/api/v1/products/matrix-live`** — виправлено декілька багів:
   - Раніше не було ключа `products` у відповіді → фронт завжди тихо падав на mock. Тепер конвертує групи в очікувану форму `{id, name, unit, prices[], image_url}`.
   - Атрибуція магазину бралась з ключа скрейпера, а не з `product.source` → всі ціни з cijene.me (одного скрейпера на 4 магазини) злипались в один фейковий стовпець. Виправлено.
   - Персист у MongoDB, доданий пізніше, чекав повний internal-таймаут драйвера (20-30с) при недоступній БД, через що вся відповідь вилітала за межі клієнтського таймауту → тепер персист запускається як фонова задача (`asyncio.create_task`) з жорстким кап 5с.
4. **MongoDB persistence** (`_persist_live_products`) — upsert по `id`, bounded `price_history` (`$slice: -30`) для майбутніх графіків динаміки цін.
5. **Фото товару** — маленька іконка (28px) в клітинці товару в `PriceMatrixLanding.tsx`, дані з `image_url` (реальні фото з cijene.me `storage/`).
6. **Інфраструктура для локального запуску без Docker:** `instagrapi` (потрібен для Instagram-скрейпінгу) конфліктує по pydantic-версії з рештою стеку (FastAPI/pydantic-settings v2) — імпорти `instagram_auth`/`instagram_scraper`/legacy `scrapers`-роутера зроблені опціональними (try/except), щоб застосунок піднімався без нього.
7. **Порти:** `PORTS.md` рекомендує 3000/8000 для локальної розробки без Docker, але на цій машині 3000 зайнятий іншим проєктом (SpaceCode Dashboard) — використовуємо Docker-зарезервовану пару 3001 (frontend) / 8001 (backend), яка теж задокументована в `PORTS.md`.
8. Живий рендер підтверджено скріншотом у браузері (Playwright): 287 реальних товарів з фото, 0 помилок консолі.
9. **Групування товарів за категоріями** (2026-07-07, друга частина сесії):
   - `backend/app/services/category_map.py` (новий файл) — мапить 10 категорій cijene.me на українську таксономію (Бакалія, М'ясо і риба, Молочка, Дитячі товари, Солодощі та снеки, Напої, Особиста гігієна, Побутова хімія, Акції); комбіновану категорію cijene.me «Voće i povrće» самі ділимо на **Овочі**/**Фрукти** за списком чорногорських/сербських ключових слів (`VEGETABLE_KEYWORDS`/`FRUIT_KEYWORDS`), з fallback-групою «Фрукти та овочі» для неоднозначних назв.
   - **`GET /api/v1/products/by-category`** (новий ендпоінт) — той самий живий скрейп cijene.me + Instagram-мок, що й `/matrix-live`, але результат згруповано в масив `{name, count, products[]}`, відсортований за `CATEGORY_ORDER`. Перевірено на реальних даних: 805 товарів → 12 категорій (Овочі 21, Фрукти 14, Молочка 43, Бакалія 43, М'ясо і риба 35, Солодощі та снеки 40, Напої 36, Особиста гігієна 15, Побутова хімія 16, Дитячі товари 6, Фрукти та овочі 3, Інше 15).
   - **Фронтенд підключено:** `ProductsModal.tsx` тепер лениво тягне `/by-category` тільки при відкритті модалки (щоб не дублювати 10-15с скрейп на кожному завантаженні лендінгу), рендерить товари секціями з заголовком категорії й лічильником, пошук фільтрує всередині категорій; малий фото-icon (28px) теж показується в списку. `productsAPI.byCategory()` доданий у `frontend/src/lib/api.ts` (timeout 30s, як і `priceMatrixLive`).
10. **Групування + сортування в основній таблиці цін** (2026-07-08):
    - `_build_product_row()` у `backend/app/api/v1/endpoints/products.py` тепер додає поле `category` (через `classify_group_category()` з `category_map.py`) до кожного рядка — раніше категорію рахував лише `/by-category`, тепер вона є і в `/matrix-live`. `/by-category` спрощено — бере `category` вже з рядка замість повторного рахунку.
    - **`PriceMatrixLanding.tsx`** (головна таблиця на лендінгу) — три зміни:
      1. **Товари, у яких ціна є ТІЛЬКИ в Instagram** (всі 4 «реальні» магазини `null`), винесені в окремий блок в самому кінці таблиці з плашкою «Лише в Instagram» — раніше були розкидані по всьому списку. Перевірено на живих даних: 15 з 287 товарів. ⚠️ Замінено 2026-07-09 (п.13 нижче) — ці 15 товарів насправді мали атрибутуватись реальному магазину, а не окремому джерелу «Instagram»; блок «Лише в Instagram» і ця логіка прибрані.
      2. **Плашки-заголовки груп** («Овочі · 21», «Молочка · 43» і т.д.) додані прямо в основну таблицю (`<tr><td colSpan={...}>`) — раніше групування було видно тільки в модалці «Товари», в самій таблиці цін секцій не було, хоча дані вже приходили згруповані. Порядок категорій — той самий `CATEGORY_ORDER`, що і в бекенді (продубльований у фронтенді, оскільки з API приходить вже готовий label, а не структура для сортування).
      3. **Липка шапка з назвами магазинів**: таблиця обгорнута в скрол-контейнер (`maxHeight: 70vh; overflowY: auto`), `<thead>` — `position: sticky; top: 0`. Рядок з лого/назвами магазинів завжди залишається зверху, а плашки груп і рядки товарів прокручуються під ним.
    - Якщо в даних узагалі нема категорій (наприклад, mock-фолбек з 8 товарів без `category`) — групування вимикається автоматично, таблиця показує плаский список як раніше.
11. **Кеш замість live-скрейпу на кожному завантаженні + кнопка "Оновити ціни" + щотижневий планувальник** (2026-07-08):
    - **Проблема, яку виправлено:** раніше `/matrix-live` (реальний скрейп cijene.me, 10-15с) викликався при КОЖНОМУ відкритті лендінгу — зайве навантаження на cijene.me й повільне перше відображення для кожного відвідувача.
    - **`GET /api/v1/products/matrix-cached`** (новий ендпоінт, `products.py`) — читає останній збережений скан з MongoDB (`db.products`, сортування за `updated_at`), з жорстким кап 5с через `asyncio.wait_for` (та ж проблема "connected, але недоступний" Mongo, що і в persist-логіці) — якщо БД пуста/недоступна, віддає mock (8 товарів), як і раніше робив `/matrix`. Тепер це основний ендпоінт для завантаження лендінгу.
    - **`_persist_live_products()`** — виправлено: `category` тепер теж зберігається в MongoDB (раніше `$set` не включав це поле, тож кеш втрачав групування після рестарту).
    - **`refresh_prices_job()`** (новий, `products.py`) — той самий скрейп+групування+persist, що й `/matrix-live`, але `await`-иться напряму (не fire-and-forget), бо викликається планувальником, а не HTTP-запитом.
    - **Планувальник (`backend/app/main.py`)** — `APScheduler` (`AsyncIOScheduler` + `CronTrigger`) підключений нарешті: `refresh_prices_job` запускається автоматично щопонеділка о 07:00 за Києвом (`ZoneInfo("Europe/Kyiv")`), старт/shutdown в `lifespan`. `apscheduler==3.11.3` доданий у `requirements.txt` (раніше стояв лише руками в venv для legacy-оркестратора).
    - **Кнопка "Оновити ціни"** — додана у ДВОХ місцях: (1) маленька кругла іконка ⟳ біля слова "Товари" у навігації хедера (`LandingPageDesignBrief.tsx`), (2) текстова кнопка "Оновити ціни" прямо в шапці таблиці цін біля слова "Товар" (`PriceMatrixLanding.tsx`, за скріншотом користувача). Обидві викликають `onRefreshPrices` → `fetchMatrix(true)` → реальний `/matrix-live` (а не кеш); під час запиту іконка крутиться (`monteShopSpin` keyframes), кнопка недоступна для повторного кліку.
    - **`frontend/src/lib/api.ts`** — `productsAPI.matrixCached()` (без спец. timeout, бо швидкий) додано поруч з `priceMatrixLive()`; початкове завантаження сторінки (`useEffect` при монтуванні) тепер викликає `matrixCached()`, а не `priceMatrixLive()` — реальний скрейп лишається тільки для планувальника й кнопки.
    - Перевірено: `/matrix-cached` повертає mock за 5с (Mongo недоступна в цій пісочниці — очікувано, реальний інстанс буде на проді), `/matrix-live` як і раніше повертає 287 товарів за ~10с; лог старту бекенда підтверджує `Added job "refresh_prices_job"` + `Scheduler started`.
12. **MongoDB встановлена локально на Windows** (2026-07-08): `winget install MongoDB.Server` — працює як Windows-сервіс (`Automatic` startup), слухає `127.0.0.1:27017`, без авторизації (дефолтний community-інстал). Доданий `backend/.env` (раніше не існував) з `MONGODB_URL=mongodb://localhost:27017` — дефолт у `config.py` (`mongodb://admin:admin@mongo:27017`) розрахований на Docker-мережу й тут не резолвиться. Після рестарту бекенд підключається до Mongo миттєво (раніше падав у 30с internal timeout драйвера і йшов у mock). `/matrix-cached` тепер реально повертає `"source": "cache"` з живими даними, а не завжди mock.
13. **Виправлена атрибуція mock-даних Instagram** (2026-07-09): у `/matrix-live`/`/matrix-cached` "найдешевша ціна" іноді показувала джерело **Instagram** — виявилось, це 15 захардкоджених фейкових "постів" (`instagram_mock_scraper.py`), чиї назви не збігаються з жодним реальним товаром cijene.me (fuzzy-match не проходить поріг 85%), тож кожен ставав окремим рядком з ЄДИНОЮ ціною — тривіально "найдешевшою". За задумом кожен пост публікується Instagram-акаунтом КОНКРЕТНОГО магазину (назви штибу "Premium Mleko **Aroma**", "Fresh Olives **HDL** Black" явно на це вказують), тож:
    - `instagram_mock_scraper.py`: `source` кожного товару змінено з фейкового `"Instagram"` на реальний магазин, якого стосується пост (`Aroma`/`Voli`/`HDL`/`IDEA`) — ціна тепер конкурує в правильній колонці замість фейкового 5-го джерела.
    - `MOCK_STORES` (backend `products.py` і frontend `LandingPageDesignBrief.tsx`) — стовпець «Instagram» видалений, залишились тільки 4 реальні магазини.
    - `PriceMatrixLanding.tsx` — прибрана спеціальна логіка «Лише в Instagram» (виокремлення рядків у окремий блок унизу таблиці) як мертвий код, оскільки джерела з такою назвою більше не існує.
    - Перевірено на живих даних: `stores` тепер `[Aroma, Voli, HDL, IDEA]` (4, не 5); "Fresh Olives HDL Black" → cheapest HDL, "Organic Yogurt Voli" → cheapest Voli і т.д. — усі 15 колишніх «Instagram-only» рядків тепер атрибутовані правильному магазину.
14. **Мобільна версія лендінгу + виправлений Tailwind pipeline** (2026-07-10), за `design_handoff_monte_shop_price_landing/README-mobile.md`:
    - 🔴 **Критичне відкриття по дорозі:** Tailwind CSS **ніколи не працював** у цьому проєкті — `tailwindcss@^4.0.0` встановлений, але без `postcss.config`/`@tailwindcss/postcss`, і `globals.css` містив старий v3-синтаксис (`@tailwind base/components/utilities`) замість v4 `@import "tailwindcss"`. Реально в браузер віддавався НЕОБРОБЛЕНИЙ CSS-файл (буквально текст `@tailwind base;` як є). Це не було помітно раніше, бо весь наявний UI побудований переважно на inline `style={{}}`, а Tailwind-класи (`rounded-3xl`, `shadow-2xl` тощо) були лише декоративним доповненням — але для мобільної версії якраз потрібна РЕАЛЬНА респонсивна поведінка (`hidden`/`md:flex` тощо), яка без робочого Tailwind не могла спрацювати. Виправлено: доданий `@tailwindcss/postcss` (`npm install --legacy-peer-deps`, через pre-existing конфлікт react19 vs `@testing-library/react@14`), створений `postcss.config.mjs`, `globals.css` переведений на `@import 'tailwindcss'; @config '../../tailwind.config.ts';` (v4 підтримує старий JS/TS `tailwind.config.ts` через `@config` для зворотної сумісності — не довелося переписувати весь theme на CSS `@theme`). Заразом прибраний мертвий `@layer components` блок (`.btn`/`.card`/`.badge`, `body{@apply bg-neutral-900...}`) — це був **build-blocking error** (`Cannot apply unknown utility class 'text-primary-500'`) з іншого (темного) шаблону, що ніколи не використовувався живими компонентами (тільки orphan `Header.tsx`/`PriceMatrix.tsx`/`SearchBar.tsx`/`TrendingProducts.tsx`), і якби він скомпілювався — зробив би `<body>` темним (`bg-neutral-900`), зламавши весь світлий «paper» дизайн.
    - **`frontend/src/lib/productMatrix.ts`** (новий файл) — винесені спільні `CATEGORY_ORDER`/`groupByCategory`/`withCheapest`/`formatPrice`/`translations`, раніше продубльовані в `PriceMatrixLanding.tsx`; заразом виправлений старий баг `?.index || -1` → `?? -1` (falsy-zero: якщо найдешевший магазин — перший у списку (Aroma, index 0), `0 || -1` давало `-1` і підсвітка/напис «дешевше всього» зникали — стосувалося 56 з 287 товарів).
    - **`frontend/src/components/PriceCardsMobile.tsx`** (новий файл) — мобільний список карток замість таблиці (візуальний референс з `.dc.html`, НЕ скопійований напряму): чіп-стрічка магазинів (горизонтальний скрол), заголовок секції з кнопкою «Оновити ціни», плашки-категорії, картки товару (назва+іконка+юніт, найкраща ціна праворуч, міні-смуга 4 цін з підсвіткою найдешевшої, «—» для відсутніх). Рендериться поруч з `PriceMatrixLanding` — обидва завжди монтуються, Tailwind `hidden md:block` / `md:hidden` перемикає які видно (без JS media-query, без гідратейшн-мисматчу).
    - **`LandingPageDesignBrief.tsx`** — хедер і хіро стали респонсивними: sticky-хедер на мобільному (`sticky md:static`), десктопна nav (Товари/Магазини/Про проєкт) схована на мобільному (`hidden md:flex`), додано ☰-меню (`useState` toggle) з тими самими пунктами; H1 58px→32px, теглайн 19px→15px, паддінги хіро зменшені, форма пошуку — stacked (вертикально) на мобільному замість joined-pill рядка. **Знайдений і виправлений супутній баг:** `display:'flex'` inline на кнопці-гамбургері перебивав `md:hidden` (inline style завжди виграє в каскаді) — кнопка лишалась видимою і на десктопі; переніс `display` у className (`flex md:hidden`).
    - Перевірено програмно через Playwright (не тільки скріншот, а `getComputedStyle().display` на кожному брейкпоінті): на 390px — таблиця `none`, картки `block`, десктопна nav `none`, гамбургер `flex`; на 1280px — навпаки. Клік по гамбургеру: `aria-expanded` `false→true`, дропдаун з реальними пунктами nav. 0 console errors на обох брейкпоінтах.

**Свідомо не зроблено в межах v0.1.0** (кандидати для Phase 2):
- Реальний Instagram-скрейпінг (лишається mock, тепер хоча б з правильною атрибуцією до реальних магазинів)
- PostgreSQL використання (підключений, але не пише історію/аналітику)
- Виправлення i18n (два незалежні стеки мови, next-intl locales `ukr/rus/mne` не збігаються з реальним `ru/uk/en` — саме тому мобільні скріншоти/перевірки цієї сесії показують РОСІЙСЬКИЙ текст на `/ukr`, це не регресія мобільної версії)
- Очищення мертвого коду (orphan-компоненти з `DESIGN_EXTRACT.md`, і тепер також мертвий `.btn/.card/.badge` CSS-шар — сам CSS вже прибраний, але файли `Header.tsx`/`PriceMatrix.tsx`/`SearchBar.tsx`/`TrendingProducts.tsx` все ще лежать невикористані)

---

## 📋 Phase 4 — Акаунти, списки покупок, адмінка, локалізація

**Повний план і статус: [`PHASE_4_PLAN.md`](./PHASE_4_PLAN.md)** — окремий документ, бо запит користувача (2026-07-13) охоплює ~10 фіч (auth, шаровані/збережені списки покупок з тарифними лімітами, адмінка з CRUD магазинів/тарифів/скрейпер-агентів, переклад товарів по мовах, +2 нові локалі), розбитих на 7 фаз (4.0-4.6) з окремими архітектурними рішеннями (стратегія auth, де живуть дані юзера, TTL гостьових списків).

**Готово (Phase 4.0, 2026-07-13):**

15. **Швидкі UI-фікси + нові locale-заглушки:**
    - **Видимість пошукового поля** — `<input>` в hero мав `border:none` без явного фону; після виправлення Tailwind-пайплайну (п.14) preflight-скидання зробило фон `transparent`, поле стало майже невидимим на фоні фото. Виправлено в `LandingPageDesignBrief.tsx`: `background-color: rgba(120, 130, 128, 0.3)` (сірий, 30% прозорості, за ТЗ) + видима рамка `1px solid rgba(15, 20, 25, 0.25)`.
    - **Лого → кнопка "на головну"** — блок "M" + "Monte-Shop-Price" в хедері обгорнутий у `<button onClick={onHomeClick}>`. `onHomeClick` закриває будь-яку відкриту модалку (Товари/Магазини/Про проєкт) і робить smooth-scroll наверх — оскільки це SPA без реального роутингу між секціями (Товари/Магазини/Про проєкт — модалки), "на головну" = закрити модалку + scroll top.
    - **Нові locale-файли (частина п.10 запиту)** — `frontend/src/locales/mne.json` (Чорногорська) вже існував; додані `srb.json` (Сербська, екавиця: цена/cena) і `bos.json` (Боснійська, ієкавиця: cijena, як у mne.json). Підключені в `frontend/src/i18n.ts` і `frontend/next-intl.config.ts` (масив `locales`, тип `Locale`, `pathnames`). Всі 5 роутів (`/ukr /rus /mne /srb /bos`) — 200 OK.
      ⚠️ **Не зроблено:** це тільки next-intl message-каталоги на рівні роутингу. Реальний UI лендінгу (`TRANSLATIONS` у `LandingPageDesignBrief.tsx`) має свій окремий хардкод `ru/uk/en` і перемикач на 3 кнопки, не підключений до next-intl (той самий раніше задокументований розрив). Повне підключення — **Phase 4.6** в `PHASE_4_PLAN.md`.
    - Перевірено Playwright: overflow=0 на всіх брейкпоінтах (без регресій), computed style інпуту підтверджений, клік по лого scrollY 472→0, 0 console errors, `tsc --noEmit` чистий.

16. **Phase 4.1 — Список Покупок для незалогінених (гостьовий режим)** (2026-07-13, готово):
    - Nav "Товари" перейменований на "Список покупок". Клік відкриває `ShoppingListModal.tsx` (замінив `ProductsModal.tsx`, видалений — повністю замінений) — той самий пошук + лінивий `/by-category` фетч, плюс кнопка "+ Додати" на кожному товарі, що додає його в клієнтський кошик.
    - **Сесія + кошик**: `frontend/src/lib/shoppingCart.ts` — випадковий UUID у `localStorage` (`monteShopSessionId`, надсилається як `owner_session_id` при створенні — не auth, лише поле анонімного власника, до якого Phase 4.2 прикріпить реальний `owner_user_id`) + сам кошик (`monteShopCart`), тож перезавантаження сторінки до натискання "Створити список" не губить вибір.
    - **"Створити список"** (праворуч у шапці модалки, з лічильником, заблокована при порожньому кошику) → `POST /api/v1/lists` → очищає кошик → `router.push` на `/[locale]/list/[id]` (нова окрема сторінка, не модалка) — id одразу є посиланням для шарингу.
    - **Перегляд списку** (`ShoppingListView.tsx`, сторінка `app/[lang]/list/[id]/page.tsx`): назва/юніт, чекбокс з закресленням (повторний клік знімає закреслення), найкраща ціна + магазин, міні-смуга цін по 4 магазинах (`—` де немає) — перевикористовує `formatPrice`/`DEFAULT_STORES` з `lib/productMatrix.ts`. Кнопка "Поділитися списком" копіює посилання.
    - **Закреслення зберігається на сервері і шариться**: клік по чекбоксу → `PATCH /api/v1/lists/{id}/toggle` → змінює `checked` в MongoDB. Перевірено двома окремими browser context — другий бачить закреслення першого після перезавантаження.
    - **TTL гостьового списку вирішено**: 30 днів неактивності через Mongo TTL-індекс на `updated_at` (`LIST_TTL_SECONDS` в `lists.py`).
    - **Backend**: новий `backend/app/api/v1/endpoints/lists.py` (`/api/v1/lists`) — колекція `shopping_lists` (`_id`=uuid4 hex, `items`, `owner_session_id`, `owner_user_id=None` до Phase 4.2, `created_at`/`updated_at`); `GET /lists/{id}` резолвить ціни жваво з `db.products` за id (список завжди показує актуальні ціни, не застиглий знімок).
    - Знайдений і виправлений баг: `onClose()` (яка синхронно розмонтовує модалку разом з її `router`-замиканням) викликалась ДО `router.push(...)` в `createList()`, через що навігація на нову сторінку списку інколи губилась — виправлено переставленням порядку (push, потім close).
    - Перевірено наскрізно (Playwright + curl): create→get→toggle→persist після reload→другий browser context бачить той самий стан; overflow=0 на новій сторінці 280-1280px; 0 console errors; `tsc --noEmit` чистий.

**Готово (Phase 4.2, 2026-07-14):** акаунти. Auth — **обидва методи одразу** (email+пароль ТА magic-link, вибір користувача при вході, за окремим явним запитом), сесія в HttpOnly JWT-кукі. Magic-link листи йдуть через **той самий Resend-акаунт, що вже використовується в MonteLand/KartIQ** (перевикористаний за прямою згодою користувача). Збережені/множинні списки: "Список покупок" для залогіненого з ≥1 списком показує панель "Мої списки" з кнопкою "+ Новий список"; у перегляді списку — кнопка "Зберегти список" (інпут назви, не native prompt). Тарифні ліміти (Free 3 / Simple 10 / Pro 100, поки хардкод — адмінка в Phase 4.4 зробить це редагованим) — enforced і при створенні, і при збереженні, 403 з повідомленням показується в UI (не тільки console.error). Guest-TTL перероблений на partial-індекс (`owner_user_id: None`), щоб збережені списки з нього виключались. Перевірено наскрізно curl + Playwright (реальний magic-link лист, реальний браузер, обидва tier-limit і saved-badge кейси). Деталі — `PHASE_4_PLAN.md`.

**Готово (Phase 4.3+4.4, 2026-07-14):** магазини + адмінка. Нова колекція `stores` (замінила хардкод `MOCK_STORES` у `StoresModal.tsx`) — `GET /stores` публічний, CRUD — тільки адмін. Свідомо НЕ чіпав реальний scraping/matching pipeline (`cijene_scraper.py`) — він і далі працює через `name`-рядок, як раніше; міграція реального скрейпінгу на цю колекцію — окрема, ризикованіша робота поза скоупом цього запиту. Адмінка: **рішення прийнято** — той самий Next.js застосунок, `/[lang]/admin`, той самий auth з Phase 4.2 + прапор `is_admin` на юзері (не окремий інструмент, не окремий логін). Перший адмін ставиться через `backend/scripts/bootstrap_admin.py` (chicken-and-egg — адмінка не може створити першого адміна сама). 3 таби: Магазини (CRUD), Тарифи (тепер редаговані через `db.settings`, хардкод 3/10/100 — лише fallback для чистої БД), Юзери (призначення тарифу). Перевірено наскрізно: не-адмін отримує 403, адмін створює магазин і він одразу з'являється в публічному API, зміна тарифу юзера одразу впливає на `/lists/mine`. Деталі — `PHASE_4_PLAN.md`.

**Готово (Phase 4.6, 2026-07-14):** локалізація — об'єднання i18n-стеків (URL-локаль тепер єдине джерело істини, `Lang` = 6 next-intl кодів `ukr/rus/mne/srb/bos/eng`, старий 3-пігулковий перемикач замінений на `<select>`), поле `name_i18n` на продуктах + `translation_service.py` (Groq, опційний, вимкнений за замовчуванням — свідомо НЕ перевикористаний ключ hrd-minion без окремого запиту), ручний і AI-переклад через адмінку, мовний пошук (`name_i18n.{lang}` регекс-фолбек, коли `$text` не вистачає). Деталі — `PHASE_4_PLAN.md`.

**Готово (Phase 4.5, 2026-07-14):** скрейпер-агенти в адмінці. Виявлено — існує ДВА оркестратори: активний (`services/scrapers/orchestrator.py`, реально працює, знає лише `cijene` + `instagram`) і мертва legacy-система (`services/orchestrator.py` + `endpoints/scrapers.py`, залежить від `instagrapi`, вже вимкнена через `try/except ImportError` в `router.py`) — 4.5 побудований поверх активного, legacy не чіпав. Нова колекція `scraper_agents` (`store_ids` — FK у `db.stores`, бо cijene.me покриває всі 4 магазини за один скрейп), 4-й таб "Скрейпери" в адмінці: список з last-run статусом, "Запустити зараз" (реальний виклик `ScraperOrchestrator.run_single()`), "+ Додати сайт" (name/url/strategy/stores) — `custom`-стратегія зберігається, але не запускається (400 з поясненням: новий формат сайту потребує написаного вручну парсера — авто-білдера парсерів це не додає, як і планувалось). Перевірено наскрізно curl (реальний запуск Instagram-агента: 15 товарів, статус success; custom-агент коректно відхиляється). Деталі — `PHASE_4_PLAN.md`.

**Усі фази Phase 4 (4.0-4.6) завершені.**

**Bugfix (2026-07-15):** "Про проєкт" і "Магазини" модалки рендерились крихітною смужкою (48px/64px замість реальної ширини) на десктопі й мобільному. Корінь: `tailwind.config.ts`'s кастомна `spacing` шкала перевикористовує імена `xs/sm/md/lg/xl/2xl/3xl`, які ТАКОЖ є стандартними іменами `maxWidth`-шкали — дефолтна Tailwind-функція домішує `spacing` в `maxWidth` ПІСЛЯ named-розмірів, тож кастомні значення мовчки перекривали реальні у КОЖНОМУ `max-w-2xl`/`3xl`/`sm`/`xs` по всьому застосунку (не лише в цих двох модалках — також `ShoppingListModal`×2, `ShoppingListView`, `AuthModal`, тарифи в адмінці). Config-рівневі фікси (`extend.maxWidth`, повна заміна `theme.maxWidth`, нативний v4 `@theme`-блок) НЕ спрацювали навіть після повністю чистого ребілду — підтверджений баг Tailwind v4's `@config`-compat шару для v3-style конфігів. Виправлено на рівні кожного використання: `max-w-[42rem]` замість `max-w-2xl` (arbitrary-value синтаксис обходить theme-резолюцію повністю). Другий, окремий баг у `StoresModal.tsx`: таблиця без `overflow-x-auto`/`min-width` — URL ламався по літері на мобільному; додано `overflow-auto` + `min-w-[520px]`. Перевірено Playwright-скріншотами 1440×900 і 390×844. Деталі — `CLAUDE.md` п.20.

**Доповнення Phase 4.6 (2026-07-17):** поле `name_i18n` існувало, але було порожнім у ВСІХ 287 реальних товарів — єдиний перекладач (Groq AI) свідомо не мав ключа. Новий `grocery_dictionary.py` — безкоштовний детермінований словник (~150 слів: молочка/овочі/м'ясо/напої/побутова хімія тощо), перекладає лише загальну назву товару ("Mlijeko Imlek Moja kravica" → "Молоко Imlek Moja kravica"), бренд не чіпає. Підключений як основний перекладач у `translation_service.py` (AI — фолбек, якщо словник нічого не впізнав), автоматично рахується при кожному живому скрейпі (`_persist_live_products`) і одноразово прогнаний по всій БД (`scripts/backfill_translations.py`) — 281/287 (98%) отримали переклад, 6 без перекладу — це чисті бренд-назви (Coca Cola, Red Bull...), так і має бути. Попутно знайдено і виправлено 2 реальні баги, що ламали `/search/products` **для БУДЬ-ЯКОГО запиту**, не лише перекладених: (1) на колекції `products` взагалі не було text-індексу — `$text` кидав виняток, який мовчки ковтався, і `name_i18n`-фолбек ніколи не встигав спрацювати (додано створення індексу при старті + розділені try/except); (2) `ProductSummary.source` вимагав `str`, а всі товари з cijene.me мають `source: None` (агрегація кількох магазинів) — 500 на кожному реальному пошуку (виправлено на `Optional[str]`). Перевірено наскрізно: curl (`?q=молоко&lang=ukr` → 9 результатів, `?q=milk&lang=eng` → 13, `?q=сир&lang=ukr` → 19) і реальний Playwright-браузер на `localhost:3001/ukr` — таблиця показує "Молоко 2.8% Lazine", "Йогурт Imlek Moja kravica" і т.д.

**Bugfix (2026-07-17, 2 частини):** (1) hero-пошук на лендінгу — інпут+кнопка "Знайти" не мали `value`/`onChange`/обробника взагалі, чисто декоративні. Виправлено в `LandingPageDesignBrief.tsx`: контрольований `searchQuery`, живий client-side фільтр по вже завантаженому `products`, "нічого не знайдено" для всіх 6 локалей. (2) пошук на сторінці створення списку ("Список покупок") був НЕ пов'язаний з (1) — окремий, глибший баг: `ShoppingListModal.tsx` при КОЖНОМУ відкритті бив `GET /products/by-category`, який перезапускає повний живий скрейп cijene.me (~10-15с), а не читає вже завантажені дані з лендінгу; під React 18 StrictMode (dev) ефект подвоюється — два одночасні живі скрейпи, і якщо один повертав порожній/іншій результат, `categories` лишався незаповненим і модалка намертво показувала "Товари не знайдені" з жодного разу не показуючи fallback. Виправлено видаленням live-фетчу повністю — категорії тепер рахуються client-side з уже завантаженого `products`-пропа (`groupByCategory()` з `lib/productMatrix.ts`, той самий хелпер, що й таблиця на лендінгу), миттєво, без мережі, без сценарію відмови. Перевірено наскрізно Playwright: пошук "молоко" → 8 товарів у групі "Молочка" + 1 в "Інше", додавання в кошик, "Створити список" → реальний перехід на `/ukr/list/{id}` з товаром і живою ціною.

**Deploy (2026-07-17):** перший реальний production-деплой — http://138.199.204.107:3010 (адмінка `/ukr/admin`), той самий Hetzner VPS, що й hrd-minion (свідомо підтверджено користувачем, спільна інфраструктура). `kartiq-backend`/`kartiq-frontend` зупинені для звільнення пам'яті (не видалені). Дорогою знайдено й виправлено `instagrapi` — реальний блокер `pip install` (pydantic v1/v2 конфлікт), плюс латентний баг необгорнутого `AromaScraper`-імпорту. Повний runbook і всі деталі безпеки — `CLAUDE.md` п.23.

---

**Last Updated:** 2026-07-17
**Developed with:** Claude Code (claude.ai/code)