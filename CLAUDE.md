# CLAUDE.md — Insta-data Project Instructions

Цей файл надає контекст Claude Code при роботі з цим проектом.

---

## 📋 Проект Insta-data

**Мета:** Автоматичний моніторинг цін товарів харчування через Instagram + офіційні сайти магазинів Чорногорії.

**Статус:** ✅ **v0.1.0 — Phase 1 завершена** (2026-07-07): лендінг + backend API + реальний скрейпінг цін (cijene.me) + MongoDB-персист. Деталі — розділ [«Phase 1 Complete — v0.1.0»](#-phase-1-complete--v010-2026-07-07) внизу файлу. Версія узгоджена з `backend/app/main.py` (`FastAPI(version="0.1.0")`).

**Tech Stack:**
- **Frontend:** Next.js 15 + React 19 + Tailwind 4 + Framer Motion
- **Backend:** FastAPI + SQLAlchemy 2.0 + Pydantic
- **Databases:** MongoDB (primary, best-effort persist) + PostgreSQL (підключений, поки не використовується) + Redis (не підключений)
- **Scrapers:** `cijene_scraper.py` (реальні дані Aroma/Voli/HDL/IDEA через cijene.me, aiohttp) + `instagram_mock_scraper.py` (мок). `instagrapi`/Playwright-скрейпери для сайтів магазинів написані (`store_scrapers.py`), але не підключені до orchestrator — замінені одним cijene.me-агрегатором
- **Infrastructure:** локально без Docker (venv + uvicorn + npm run dev) — Docker Compose є, але на цій машині не використовувався для розробки

---

## 🔐 Credentials (НЕ передаємо в git!)

### Instagram Account
```
Email:    Niobium_Runas
Password: (в .env файлі, не в коді!)
```

**Важно:**
- Пароль зберігаємо тільки в `.env` локально
- `.env` файл в `.gitignore`
- `.env.example` містить шаблон без паролів
- На сервері використовуємо environment variables (supervisord config)

---

## 📁 Структура Проекту

```
insta-data/
├── frontend/                    ← Next.js 15 (React 19)
│   ├── public/
│   │   └── images/             ← Store logos, icons
│   ├── src/
│   │   ├── app/
│   │   │   ├── [lang]/         ← i18n routing (ukr/rus/mne)
│   │   │   ├── api/            ← Route handlers
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── PriceMatrix.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── WishlistButton.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   └── ...
│   │   ├── lib/
│   │   │   ├── api-client.ts   ← Axios client
│   │   │   ├── constants.ts
│   │   │   └── utils.ts
│   │   ├── locales/            ← Translations
│   │   │   ├── ukr.json
│   │   │   ├── rus.json
│   │   │   └── mne.json
│   │   ├── styles/
│   │   │   └── globals.css     ← Tailwind + custom theme
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   └── package.json
│
├── backend/                     ← FastAPI
│   ├── app/
│   │   ├── main.py             ← FastAPI app instance
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── prices.py
│   │   │       │   ├── search.py
│   │   │       │   └── wishlist.py
│   │   │       └── router.py
│   │   ├── services/
│   │   │   ├── search_service.py
│   │   │   ├── price_tracker.py
│   │   │   ├── wishlist_service.py
│   │   │   └── image_processor.py
│   │   ├── models/
│   │   │   ├── product.py
│   │   │   ├── price.py
│   │   │   └── wishlist.py
│   │   ├── database/
│   │   │   ├── mongodb.py
│   │   │   ├── postgres.py
│   │   │   └── migrations.py
│   │   ├── core/
│   │   │   ├── config.py       ← Settings from .env
│   │   │   ├── logger.py
│   │   │   └── exceptions.py
│   │   └── middleware/
│   │       ├── cors.py
│   │       └── rate_limit.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── .env                    ← Local config (НЕ комітити!)
│   ├── requirements.txt
│   └── main.py                 ← Entry point
│
├── scrapers/                    ← Docker microservices
│   ├── instagram_parser/
│   │   ├── scraper.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── aroma_scraper/
│   ├── voli_scraper/
│   ├── hdl_scraper/
│   ├── idea_scraper/
│   └── orchestrator/            ← Scheduler for daily runs
│       ├── orchestrator.py
│       └── Dockerfile
│
├── docs/
│   ├── PROJECT_INFO.md         ← Проект інформація & рішення
│   ├── BUSINESS_LOGIC.md       ← User Stories & функціональність
│   ├── TECHNOLOGY.md           ← Tech stack & архітектура
│   └── API.md                  ← API endpoints (TBD)
│
├── .github/
│   └── workflows/
│       ├── test.yml            ← Run tests on PR
│       └── deploy.yml          ← Deploy to production (TBD)
│
├── docker-compose.yml          ← Local dev environment
├── .env.example                ← Template без паролів
├── .gitignore
├── CLAUDE.md                   ← This file
├── README.md
└── ...
```

---

## 🚀 Запуск Локально

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Git

### Setup
```bash
# 1. Clone & setup
cd c:/Users/Serhii/OneDrive/Рабочий\ стол/Insta-data
cp .env.example .env

# 2. Edit .env з реальними credentials
# - INSTAGRAM_PASSWORD (Niobium_Runas пароль)
# - MONGODB_PASSWORD
# - POSTGRES_PASSWORD
# - SECRET_KEY (генеруємо: python -c "import secrets; print(secrets.token_urlsafe(32))")

# 3. Start services
docker-compose up -d

# 4. Backend setup
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# 5. Run backend (Docker)
docker-compose up -d backend

# 6. Run frontend (Docker)
docker-compose up -d frontend

# LOCAL DEVELOPMENT PORTS (reserved):
# Frontend: http://localhost:3001  ← Docker port (Next.js)
# Backend API: http://localhost:8001  ← Docker port (FastAPI)
# API Docs: http://localhost:8001/docs
# MongoDB: localhost:27017
# PostgreSQL: localhost:5432
# Redis: localhost:6379
# 
# ⭐ SEE ALSO: PORTS.md for complete port assignments & troubleshooting
```

---

## 📝 Git Flow Правила

### Branch Naming
```
feature/feature-name         ← Нові features
fix/bug-description          ← Bug fixes
docs/update-description      ← Documentation
refactor/component-name      ← Refactoring
test/test-description        ← Tests
```

### Commit Message Format
```
type(scope): description

feat(instagram): add post parser with OCR
fix(search): optimize full-text query
docs(api): document /prices endpoint
test(backend): add unit tests for price tracker
refactor(frontend): extract PriceMatrix component
```

### Git Workflow
```bash
# 1. Create feature branch
git checkout -b feature/instagram-parser

# 2. Make changes
# ... edit files ...

# 3. Commit
git add <files>
git commit -m "feat(instagram): add post parser with OCR"

# 4. Push
git push origin feature/instagram-parser

# 5. Create PR on GitHub
# → Code review → Merge

# 6. Delete branch
git branch -d feature/instagram-parser
```

---

## ✅ Code Quality Rules

### REST API
- Правильні HTTP методи: GET, POST, PUT, DELETE, PATCH
- Правильні статус коди: 200, 201, 204, 400, 401, 404, 500
- JSON format для request/response
- API versioning: `/api/v1/*`
- Proper error messages с codes

### Unit Tests (Обов'язково!)
```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=app tests/
# Coverage >= 80%
```

### Linting & Formatting (Python)
```bash
# Format
black .

# Lint
ruff check .

# Type checking
mypy app/
```

### Linting & Formatting (Frontend)
```bash
# Format
prettier --write .

# Lint
eslint src/

# Type check
npm run type-check
```

---

## 📚 Документація (ОБОВ'ЯЗКОВО прочитай!)

**⭐ ЧИТАЙ ПЕРШИМ:** `ARCHITECTURE.md`
- Повна архітектура проекту
- Data flow сценарії
- API endpoints specification
- Database schemas
- Service descriptions
- Deployment strategy

**Потім (якщо потрібна деталь):**

1. **`PORTS.md`** ← 🔴 **MUST READ** — Зарезервовані портови (3001, 8001, etc.) + troubleshooting
2. **`PLAN.md`** — Детальний план реалізації всіх фаз
3. **`docs/PROJECT_INFO.md`** — Статус, рішення, наступні кроки

---

## 🎨 Frontend Components (Monte-Shop-Price Landing)

### Core Components
| Component | File | Purpose | Status |
|-----------|------|---------|--------|
| **LandingPageDesignBrief** | `src/components/LandingPageDesignBrief.tsx` | Main landing page (Variant A) | ✅ Done |
| **PriceMatrixLanding** | `src/components/PriceMatrixLanding.tsx` | Price comparison table | ✅ Done |
| **ProductsModal** | `src/components/ProductsModal.tsx` | Products listing dialog, згруповано за категоріями | ✅ Done (лениво тягне `/by-category` при відкритті; пошук/фільтрація працюють; кнопка "+ Add to list" без onClick) |
| **StoresModal** | `src/components/StoresModal.tsx` | Stores info dialog | ✅ Done (реальні URL магазинів) |
| **AboutModal** | `src/components/AboutModal.tsx` | About project dialog | ✅ Done |

### Design System
- **Colors:** Accent #0b6e4f, Deep #0f3d2e, Cheapest #d8f3e3
- **Typography:** Plus Jakarta Sans (UI), Space Grotesk (prices)
- **Spacing:** 44px sections, 10-16px table cells
- **Breakpoints:** Designed for 1280px desktop (responsive via `tableLayout: fixed`)

---

## 🔄 Update Documentation After Each Task

**ВАЖНО:** Після кожної доробки / спрінту оновлюємо документи:

1. **PROJECT_INFO.md**
   - Оновляємо статус (✅ Done / ⏳ In Progress)
   - Додаємо записи розмов
   - Оновляємо next steps

2. **BUSINESS_LOGIC.md**
   - Оновляємо статус US (реалізовані)
   - Коригуємо workflow якщо необхідно

3. **TECHNOLOGY.md**
   - Оновляємо реальний stack
   - Додаємо нові компоненти
   - Документуємо архітектурні рішення

---

## 🐳 Docker Services

```yaml
# docker-compose.yml contains:
services:
  mongo:       # MongoDB (primary DB)
  postgres:    # PostgreSQL (history)
  redis:       # Redis (cache)
  backend:     # FastAPI app
  frontend:    # Next.js (dev only, Vercel in prod)
  nginx:       # Reverse proxy (future)
```

### Useful Commands
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart service
docker-compose restart backend

# Stop all
docker-compose down

# Remove volumes (careful!)
docker-compose down -v
```

---

## 🎨 Design System

> ⚠️ Цей блок раніше описував інший (темно-зелений/золотий, Inter font) дизайн — залишок вимог ще до появи design brief (`docs/PROJECT_INFO.md`, вимога #10). Компоненти `PriceMatrix`/`SearchBar`/`WishlistButton`/`PriceChart`/`LanguageSelector` з `next-intl` (`useTranslations()`) справді існують у `src/components/`, але ніде не імпортуються — мертвий код, що відповідає покинутому напрямку з `DESIGN_EXTRACT.md`, не поточному лендінгу.
>
> **Реальна дизайн-система** живого лендінгу (Variant A) описана вище в розділі «🎨 Frontend Components»: accent `#0b6e4f`, deep `#0f3d2e`, cheapest `#d8f3e3`, Plus Jakarta Sans + Space Grotesk.

---

## 🚨 Important Notes

⚠️ **Instagram Credentials**
- Використовуємо тільки для скрейпингу постів
- НЕ зберігаємо пароль в коді
- Session file в `.gitignore`

⚠️ **Database**
- NoSQL (MongoDB) для швидкого доступу до товарів
- SQL (PostgreSQL) для аналітики + price history
- Redis для кешування пошуку

⚠️ **Scraper Architecture**
- Кожен scraper — окремий Docker контейнер
- Запускаються паралельно (orchestrator)
- Дедублікація в backend

⚠️ **Performance**
- Page load < 2s
- Search < 100ms
- API responses < 500ms

---

## 🔧 Backend Development Status (2026-07-02)

### ✅ Backend Implemented
- FastAPI app structure (main.py, lifespan manager, CORS)
- Config system (Settings from .env: MongoDB, PostgreSQL, Redis, Instagram)
- Search API endpoints (6+ methods: /products, /price, /cheapest, /trending, /source, /stats, /mock)
- Database schemas (MongoDB + PostgreSQL models)
- Services scaffolded (auth, scraper, price_extractor, product_service, search_service, store_scrapers, orchestrator)

### ✅ Phase 1: Frontend-Backend Integration (2026-07-02)

**COMPLETED COMMITS:**
1. **0e1a83f** (2026-07-01): Landing page Variant A
   - LandingPageDesignBrief.tsx (photo-forward hero + floating matrix)
   - PriceMatrixLanding.tsx (responsive price table)
   - Modal dialogs (ProductsModal, StoresModal, AboutModal)

2. **a766bc9** (2026-07-02): Backend Phase 1 Endpoints
   - `GET /api/v1/products/matrix?lang=ru|uk|en`
   - `GET /api/v1/products/list?limit=50&skip=0`
   - Schemas: `PriceMatrixResponse`, `ProductListResponse`
   - Helper: `calculate_cheapest()`, `format_product_row()`
   - File: `backend/app/api/v1/endpoints/products.py` (250+ lines)

3. **89565d4** (2026-07-02): Frontend API Integration
   - `frontend/src/lib/api.ts`: Added `productsAPI` module
   - `frontend/src/components/LandingPageDesignBrief.tsx`: Integrated useEffect + fetch
   - Data flow: Component → useEffect → API call → State update → Render

4. **83accdd** (2026-07-02): Documentation Update
   - Updated CLAUDE.md with Phase 1 completion notes

**IMPLEMENTATION DETAILS:**

**Backend (a766bc9):**
```
/backend/app/api/v1/endpoints/products.py
├── Schemas:
│   ├── PriceMatrixResponse (stores[], products[], updated_at, total_products)
│   └── ProductListResponse (products[], total_count, updated_at)
├── Endpoints:
│   ├── GET /matrix (lang query param, fallback to mock)
│   └── GET /list (pagination: limit, skip)
└── Mock Data: 8 products × 4 stores (AROMA, VOLI, HDL, IDEA)
```

**Frontend (89565d4):**
```
/frontend/src/lib/api.ts
├── productsAPI.priceMatrix(lang) → axios GET request
└── productsAPI.list(limit, skip) → axios GET request

/frontend/src/components/LandingPageDesignBrief.tsx
├── useEffect: fetch on mount + lang change
├── State: products[], stores[], loading, (error removed)
├── Loading UI: "Завантажуємо ціни..."
├── Fallback: MOCK_PRODUCTS, MOCK_STORES
└── Data passed to: PriceMatrixLanding component
```

**Testing Checklist:**
- ✅ Backend listens on localhost:8000
- ✅ Frontend listens on localhost:3000
- ✅ CORS configured: localhost:3000 in allow_origins
- ✅ API response includes: stores, products, updated_at, total_products
- ✅ Mock data returned when DB empty
- ✅ Lang parameter switches API language dynamically
- ✅ Loading state displays during fetch
- ✅ Error fallback to mock data works

---

## 📋 UPCOMING PHASES

- **Phase 2: Data Seeding** (2026-07-03)
  - [ ] Seed MongoDB with 8 products from mock data
  - [ ] Test endpoints via Postman/curl
  - [ ] Verify frontend receives real DB data
  
- **Phase 3: Real Scrapers** (2026-07-04 to 2026-07-06)
  - [ ] Aroma.me scraper (Playwright + BeautifulSoup)
  - [ ] Voli.me scraper
  - [ ] HDL.me scraper  
  - [ ] IDEA.me scraper
  - [ ] Instagram scraper (instagrapi + OCR + Tesseract)
  - [ ] Price normalization (EUR format)
  
- **Phase 4: Background Tasks** (2026-07-07 to 2026-07-08)
  - [ ] Celery/APScheduler integration
  - [ ] 24h auto-scan scheduler
  - [ ] Retry logic with exponential backoff
  - [ ] Error notifications
  
- **Phase 5: Security & Polish** (2026-07-09 to 2026-07-10)
  - [ ] JWT authentication (/auth/login, /auth/register)
  - [ ] Rate limiting (Redis)
  - [ ] Integration tests
  - [ ] Performance optimization

### ✅ Phase 2: Data Seeding (2026-07-02)

**Commit 714fc03: Data Seeding Endpoint + Script**
- ✅ `backend/scripts/seed_products.py` — CLI seed script (125 lines)
  - Async MongoDB connection
  - 8 mock products insertion
  - Price calculation & dedup hash
  - Progress logging & verification
  
- ✅ `POST /api/v1/products/seed` — HTTP seed endpoint
  - Clears existing products
  - Inserts 8 mock products
  - Returns: {success, message, products_cleared, products_inserted, total_in_db}
  
- ✅ Data seeded in MongoDB:
  - 8 products × 4 stores
  - Prices: €0.49–€9.20
  - All cheapest prices calculated
  - All dedup hashes generated

**Frontend-Backend Integration Verified:**
- ✅ Frontend fetches real DB data (not mock fallback)
- ✅ Table displays 8 products from MongoDB
- ✅ All prices correct
- ✅ Cheapest cells highlighted
- ✅ Language switching works
- ✅ Loading state displays

**Testing Done:**
- ✅ Backend seed endpoint (curl test)
- ✅ MongoDB data verified (8 products)
- ✅ Frontend API call succeeds
- ✅ Table renders with real data
- ✅ Network tab shows correct response

---

## 📞 Next Steps

- [x] **Phase 0: Frontend Landing Page** ✅ (DONE 2026-07-01)
  - [x] Структура папок
  - [x] .env.example
  - [x] .gitignore
  - [x] CLAUDE.md
  - [x] PORTS.md (3001/8001 зарезервовано)
  - [x] LandingPageDesignBrief.tsx (Variant A)
  - [x] PriceMatrixLanding.tsx (price table)
  - [x] ProductsModal, StoresModal, AboutModal
  - [x] Responsive table layout
  - [x] i18n (RU/UK/EN translations)

**Зроблено 2026-07-01 (Commit 0e1a83f):**
- ✅ **LandingPageDesignBrief.tsx** — Variant A implementation
  - Photo-forward hero section (Kotor Bay foto + linear-gradient 180deg overlay)
  - Центрований hero контент: kicker pill → H1 (58px/800) → tagline → search bar
  - Floating price matrix (margin-top: 40px, centered, max-width: 1400px)
  - White header: logo (M) | nav (Товари/Магазины/О проєкте) | language pills (RU/UK/EN)
  - Modal dialogs: ProductsModal, StoresModal, AboutModal (scaffolded)
  
- ✅ **PriceMatrixLanding.tsx** — Price comparison table
  - Fixed header bar "Товар | Обновлено сегодня" (100% width, fixed positioning)
  - Table layout: `tableLayout: fixed` + column widths
    - Product: 24% (product name + unit)
    - Store 1-4: 16% кожна (Aroma, Voli, HDL, IDEA)
    - Cheapest summary: 12% (best price + store name)
  - Cheapest cell highlighting: #d8f3e3 bg + #05603a text + 3px green border
  - No horizontal scroll (overflow: hidden)
  - Responsive padding & font sizes (optimized for 1280px width)
  
- ✅ **Layout fixes:**
  - Removed `overflow-x-auto` (horizontal scroll)
  - Added `boxSizing: border-box` to prevent overflow
  - Centered table with `display: flex` + `justify-content: center`
  - Max-width 1400px constraint
  - Full table width within bounds (no exceeding page edges)

- ✅ **Styling per design handoff:**
  - Colors: #0b6e4f (accent), #0f3d2e (deep), #d8f3e3 (cheapest bg), #f6faf8 (header bg)
  - Typography: Plus Jakarta Sans (UI) + Space Grotesk (prices)
  - Spacing: 44px horizontal padding (page level), 10-16px table padding
  - Border radii: card 18px, pills 999px, inputs 10px, badges 7px
  - Shadows: table card shadow (0 28px 64px -30px rgba(6,78,59,0.4))

- ✅ **i18n support:**
  - RU/UK/EN translations for all UI strings
  - Localized price formatting: EUR with comma (RU/UK) or period (EN)
  - Language switcher in header (3 buttons with active/inactive states)

- ✅ **Testing:** Running on localhost:3000 (Next.js dev server)
  
- [ ] Phase 1: Instagram Parser POC — не зроблено, `instagram_mock_scraper.py` лишається mock
  - [ ] instagrapi login
  - [ ] Post scraping (48 годин)
  - [ ] OCR + regex для витягу товарів
  - [ ] Image normalization
  - [ ] Unit tests & validation

- [x] Phase 2: Web Scrapers (4 магазини) ✅ (2026-07-07) — інакше, ніж планувалось: замість окремих Playwright-скрейперів на кожен сайт, один агрегатор `cijene_scraper.py` (aiohttp, без браузера) тягне реальні ціни всіх 4 магазинів одразу з офіційного порталу cijene.me
  - [x] Deduplication/grouping logic — `ProductMatcherService` (fuzzy matching)
  - [x] Parallel execution — `ScraperOrchestrator.run_all()` (cijene + instagram паралельно)

- [x] Phase 3: Backend API (FastAPI) ✅ — `/api/v1/products/{matrix, matrix-live, list, seed}`
- [x] Phase 4: Integration & Testing ✅ — живий рендер підтверджено скріншотом у браузері (Playwright), 287 реальних товарів, 0 помилок консолі

---

## ✅ Phase 1 Complete — v0.1.0 (2026-07-07)

Перший наскрізний робочий зріз: лендінг → бекенд → реальний скрейпінг → (best-effort) MongoDB-персист. Версія узгоджена з `backend/app/main.py` (`FastAPI(version="0.1.0")`).

**Нове цієї фази:**
1. `backend/app/services/scrapers/cijene_scraper.py` — реальний скрейпінг Aroma/Voli/HDL/IDEA через cijene.me (Inertia JSON, `aiohttp`, без браузера), 16 сторінок × ~790 store-priced товарів по Podgorica.
2. `orchestrator.py` переписаний на `CijeneScraper` + `InstagramMockScraper`; старі `aroma_mock_scraper.py`/`voli_mock_scraper.py`/`hdl_mock_scraper.py`/`idea_mock_scraper.py` видалені.
3. `/api/v1/products/matrix-live` — виправлено відсутній ключ `products` у відповіді (фронт тихо падав на mock), неправильну атрибуцію магазину (брала ключ скрейпера замість `product.source`, злипаючи всі 4 магазини в один), і блокуючий персист (тепер `asyncio.create_task` + 5с timeout, замість `await` на весь internal timeout MongoDB-драйвера).
4. `_persist_live_products()` — best-effort upsert у MongoDB + bounded `price_history` (останні 30 знімків) для майбутніх графіків.
5. Маленька іконка-фото товару (28px) в `PriceMatrixLanding.tsx`, з реальних `image_url` з cijene.me `storage/`.
6. `app/services/__init__.py` і `router.py` — імпорти, що залежать від `instagrapi` (конфліктує по pydantic-версії з FastAPI-стеком), зроблені опціональними, щоб застосунок піднімався без нього.
7. Локальний запуск без Docker: backend `localhost:8001`, frontend `localhost:3001` (порт 3000/8000 з `PORTS.md` зайнятий іншим проєктом на цій машині).
8. **Групування за категоріями** (2026-07-07/08): `backend/app/services/category_map.py` (мапить 10 cijene.me-категорій + свій поділ «Voće i povrće» на Овочі/Фрукти за keyword-списками) + `GET /api/v1/products/by-category` — той самий скрейп, згрупований у `{name, count, products[]}`. `_build_product_row()` тепер віддає поле `category` і в `/matrix-live`, не тільки в `/by-category`. `ProductsModal.tsx` лениво тягне `/by-category` при відкритті (щоб не дублювати 10-15с скрейп на кожному завантаженні лендінгу) і рендерить секціями з заголовком + лічильником.
9. **Основна таблиця цін (`PriceMatrixLanding.tsx`)** (2026-07-08): плашки-заголовки груп прямо в таблиці (той самий `CATEGORY_ORDER`, продубльований на фронтенді); товари, у яких ціна є лише в Instagram (всі 4 «реальні» магазини `null`), винесені окремим блоком у кінець таблиці замість того, щоб бути розкиданими по списку (15 з 287 на живих даних) — ⚠️ замінено 2026-07-09 (п.12 нижче), логіка «Лише в Instagram» прибрана; `<thead>` зроблений `position: sticky; top: 0` всередині скрол-контейнера (`maxHeight: 70vh`), тож рядок з назвами магазинів залишається видимим, поки прокручуються групи і товари під ним. Якщо категорій немає (mock-фолбек) — групування вимикається, показується плаский список.
10. **Кеш замість live-скрейпу при завантаженні + щотижневий планувальник + кнопка "Оновити ціни"** (2026-07-08, продовження): раніше лендінг запускав реальний скрейп cijene.me на КОЖНОМУ відкритті. Тепер:
    - `GET /api/v1/products/matrix-cached` (новий) — читає останній збережений скан з MongoDB (кап 5с через `asyncio.wait_for`, фолбек на mock, якщо БД пуста/недоступна) — це тепер дефолтний ендпоінт для завантаження лендінгу.
    - `_persist_live_products()` — доданий `category` в `$set` (раніше губився при збереженні, кеш втрачав групування).
    - `refresh_prices_job()` (новий) — той самий скрейп+persist, що й `/matrix-live`, але `await`-иться напряму, бо викликається планувальником.
    - **APScheduler нарешті підключено** в `app/main.py` (`AsyncIOScheduler` + `CronTrigger`, `ZoneInfo("Europe/Kyiv")`) — `refresh_prices_job` виконується автоматично щопонеділка о 07:00 за Києвом. `apscheduler==3.11.3` доданий у `requirements.txt`.
    - Кнопка "Оновити ціни" — у двох місцях: іконка ⟳ біля "Товари" в навігації, і текстова кнопка "Оновити ціни" прямо в шапці таблиці цін (за місцем, яке користувач позначив на скріншоті). Обидві запускають реальний `/matrix-live`, поки триває — іконка обертається, кнопка заблокована.
    - `frontend/src/lib/api.ts` — `productsAPI.matrixCached()` доданий; початкове завантаження сторінки тепер викликає його замість `priceMatrixLive()`.
11. **MongoDB встановлена локально на Windows** (2026-07-08): `winget install MongoDB.Server` — Windows-сервіс (`Automatic`), `127.0.0.1:27017`, без авторизації. Доданий `backend/.env` з `MONGODB_URL=mongodb://localhost:27017` (дефолт у `config.py` розрахований на Docker-мережу `mongo:27017` і тут не резолвиться). Бекенд тепер підключається миттєво замість 30с internal timeout.
12. **Виправлена атрибуція mock-даних Instagram** (2026-07-09): "найдешевша ціна" іноді показувала джерело Instagram - причина: 15 захардкоджених фейкових постів (`instagram_mock_scraper.py`) не збігались з жодним реальним товаром cijene.me, тож кожен ставав окремим рядком з ЄДИНОЮ ціною. Кожен пост насправді належить акаунту КОНКРЕТНОГО магазину: `source` змінено з `"Instagram"` на реальний магазин (Aroma/Voli/HDL/IDEA), стовпець «Instagram» видалений з `MOCK_STORES`, логіка «Лише в Instagram» прибрана з `PriceMatrixLanding.tsx`.

13. **Мобільна версія лендінгу (390px) + виправлений Tailwind pipeline** (2026-07-10): за `design_handoff_monte_shop_price_landing/README-mobile.md`. 🔴 По дорозі виявлено, що Tailwind CSS **ніколи не компілювався** в цьому проєкті (відсутній `postcss.config`/`@tailwindcss/postcss` при `tailwindcss@^4.0.0` + старий v3-синтаксис `@tailwind ...` в `globals.css`) — весь наявний UI виглядав нормально лише завдяки inline `style={{}}`. Виправлено: `postcss.config.mjs` + `@tailwindcss/postcss`, `globals.css` → `@import 'tailwindcss'; @config '../../tailwind.config.ts';` (зберігає існуючий JS-конфіг брендових кольорів), прибраний мертвий `@layer components` блок іншого (темного) шаблону, який блокував білд (`Cannot apply unknown utility class`) і зробив би `<body>` темним, якби скомпілювався. Нове: `PriceCardsMobile.tsx` (картки замість таблиці — чіп-стрічка магазинів, категорії, best-price + міні-смуга 4 цін, «—» для відсутніх), спільний `lib/productMatrix.ts` (усунуто дублювання групування/cheapest-логіки між десктопом і мобайлом, заразом виправлений `?.index || -1` → `?? -1` баг, що ламав підсвітку для 56 товарів з ціною в Aroma), респонсивний хедер/хіро в `LandingPageDesignBrief.tsx` (sticky на мобільному, ☰-меню, stacked форма пошуку). Перевірено через Playwright `getComputedStyle` на 390px і 1280px — коректне перемикання видимості, 0 console errors.

**Свідомо поза скоупом v0.1.0:** реальний Instagram-скрейпінг (лишається mock, тепер з правильною атрибуцією), використання PostgreSQL, виправлення двох паралельних i18n-стеків (мобільна версія теж успадковує цю проблему — дефолт `lang='ru'` незалежно від URL), чистка мертвого коду (orphan `Header.tsx`/`PriceMatrix.tsx`/`SearchBar.tsx`/`TrendingProducts.tsx`).

---

## 📋 Phase 4 — Акаунти, списки покупок, адмінка, локалізація

Запит користувача (2026-07-13, ~10 фіч: auth, шаровані/збережені списки покупок з тарифними лімітами Free/Simple/Pro, адмінка з CRUD магазинів/тарифів/скрейпер-агентів, переклад товарів по мовах, +2 нові локалі) розбитий на 7 фаз (4.0-4.6). **Повний план: [`PHASE_4_PLAN.md`](./PHASE_4_PLAN.md).**

14. **Phase 4.0 — швидкі UI-фікси + locale-заглушки** (2026-07-13, готово): видимість пошукового поля (`background-color: rgba(120,130,128,0.3)` + `1px` рамка — раніше `border:none` без фону, стало невидимим після того, як Tailwind preflight почав реально працювати, п.13); лого+назва в хедері тепер `<button onClick={onHomeClick}>` — закриває відкриту модалку і scroll-top (SPA без реального роутингу); нові `frontend/src/locales/srb.json` і `bos.json` (Чорногорська `mne.json` вже існувала), підключені в `i18n.ts`+`next-intl.config.ts`, всі 5 роутів 200 OK — але це тільки next-intl каталоги, реальний UI-перемикач мов (`ru/uk/en` хардкод у `LandingPageDesignBrief.tsx`) досі не підключений до них (Phase 4.6). Перевірено Playwright: 0 overflow-регресій, 0 console errors, `tsc` чистий.

15. **Phase 4.1 — гостьовий Список Покупок** (2026-07-13, готово): nav "Товари"→"Список покупок"; `ShoppingListModal.tsx` (замінив видалений `ProductsModal.tsx`) з кнопкою "+ Додати" → клієнтський кошик (`lib/shoppingCart.ts`, localStorage: session UUID + cart); "Створити список" → `POST /api/v1/lists` → `router.push` на нову сторінку `/[lang]/list/[id]` (`ShoppingListView.tsx`) — id одразу є посиланням для шарингу; чекбокс закреслює товар і зберігає стан на сервері (`PATCH .../toggle`), перевірено що другий browser context бачить те саме закреслення. Backend: новий `lists.py` (`/api/v1/lists`), колекція `shopping_lists`, ціни резолвляться жваво з `db.products` при кожному `GET`, TTL 30 днів неактивності. Знайдений і виправлений баг: `onClose()` викликалась до `router.push()` і інколи гасила навігацію — переставлено порядок. Перевірено Playwright: overflow=0, 0 console errors, `tsc` чистий.

16. **Phase 4.2 — акаунти** (2026-07-14, готово): auth — **обидва методи** (email+пароль ТА magic-link, вибір користувача), HttpOnly JWT-кукі сесія (`auth_service.py`, `auth.py`). Magic-link через **перевикористаний Resend-акаунт з MonteLand/KartIQ** (`email_service.py`, за прямою згодою користувача — "маємо змогу відправляти листи, як в інших проєктах?"). `AuthModal.tsx` — таб-перемикач Magic Link / Пароль; 👤-кнопка в хедері. Збережені списки: `ShoppingListModal` показує "Мої списки" для залогінених з ≥1 списком; `ShoppingListView` — кнопка "Зберегти список" (інпут назви). Тарифи (Free 3/Simple 10/Pro 100, `core/tiers.py`, хардкод до Phase 4.4) enforced при створенні й збереженні, 403 показується в UI. Guest-TTL індекс перероблений на partial (`owner_user_id: None`) — збережені списки з нього виключені; знайдений і виправлений баг: `RedirectResponse` з `set_cookie` на ІНЖЕКТОВАНОМУ `response`-параметрі не спрацьовує, якщо ендпоінт повертає інший об'єкт Response — кука мала ставитись на сам `RedirectResponse`. Перевірено наскрізно curl + Playwright (реальний Resend-лист, реальний браузер, tier-limit і saved-badge).

17. **Phase 4.3+4.4 — магазини + адмінка** (2026-07-14, готово): нова колекція `db.stores` (`stores.py`) — публічний `GET`, CRUD тільки для адміна; `StoresModal.tsx` тепер тягне звідти замість хардкоду. Реальний scraping pipeline (`cijene_scraper.py`) свідомо НЕ мігрований на цю колекцію — далі працює через `name`-рядок, як і раніше (окрема, ризикованіша робота). Адмінка (`admin.py`, `[lang]/admin/AdminPageClient.tsx`) — той самий auth з Phase 4.2 + прапор `is_admin`, не окремий інструмент. Перший адмін — через одноразовий `backend/scripts/bootstrap_admin.py` (chicken-and-egg, адмінка не може сама себе бутстрапнути). 3 таби: Магазини, Тарифи (`db.settings`, тепер реально редаговані — Free/Simple/Pro більше не хардкод), Юзери (призначення тарифу). Перевірено: 403 не-адміну, реальне створення магазину через UI одразу видно в публічному API, зміна тарифу юзера одразу відбивається на `/lists/mine`.

18. **Phase 4.6 — локалізація: об'єднання i18n-стеків + переклад товарів + мовний пошук** (2026-07-14, готово): URL-локаль тепер єдине джерело істини — `lib/productMatrix.ts` експортує `type Lang = 'ukr'|'rus'|'mne'|'srb'|'bos'|'eng'` (додано 6-у локаль `eng`), `LandingPageDesignBrief.tsx` читає її через `useParams()`, перемикач мов робить `router.push()` замість `useState`; 3-пігулковий перемикач замінений на `<select>` (6 пігулок ламали б mobile-фікс з Phase 4.0). Всі компоненти з `lang`-пропом (`StoresModal`, `AboutModal`, `AuthModal`, `ShoppingListModal`, `ShoppingListView`, `PriceMatrixLanding`, `PriceCardsMobile`) імпортують спільний `Lang`; bridge-функції (`ListPageClient.tsx`, `ShoppingListModal.tsx`) видалені — мапінг більше не потрібен. Backend: нове поле `name_i18n` на продуктах + `translation_service.py` (перший LLM-інтеграція в цьому бекенді — Groq, опційний `groq_api_key`, пустий за замовчуванням: свідомо НЕ перевикористаний ключ hrd-minion без окремого запиту, бо це вже квота продакшн-бота, не email-кейс з Phase 4.2) — `resolve_display_name()` з фолбеком на оригінальну назву; ручний (`PUT /admin/products/{id}/translations`) і AI (`POST .../translate`, `.../translate-missing`) шляхи перекладу, обидва admin-only. `/matrix`, `/matrix-cached`, `/list`, `/matrix-live`, `/by-category` отримали `lang`-параметр і резолвлять переклад. Пошук (`search_service.py`) додатково матчить `name_i18n.{lang}` регексом, коли `$text` не вистачає результатів (Mongo не дозволяє `$text` всередині `$or`). Перевірено: curl наскрізно (реальний manual-переклад через адмін-сесію, matrix-cached показує переклад для `eng` і фолбек для `ukr`), всі 6 locale-роутів 200 з реальним HTML, `tsc --noEmit` чистий, бекенд рестартнувся без помилок імпорту. **НЕ перевірено реальним браузером** цієї сесії — Playwright MCP відключився посеред сесії; варто пройтись Playwright-перевіркою окремо. Деталі: `PHASE_4_PLAN.md` → Phase 4.6.

19. **Phase 4.5 — скрейпер-агенти в адмінці** (2026-07-14, готово): виявлено ДВА оркестратори — активний `services/scrapers/orchestrator.py` (реально працює, `_register_scrapers()` знає лише `cijene` і `instagram`) та legacy `services/orchestrator.py` + `endpoints/scrapers.py` (залежить від `instagrapi`, вже вимкнена гілка через `try/except ImportError` в `router.py`, власний неписаний `ScraperLog` в SQL). 4.5 побудований поверх активного оркестратора, legacy не чіпав. Нова колекція `scraper_agents` (`store_ids` — FK у `db.stores`, бо cijene.me за один скрейп покриває всі 4 магазини одразу); 4-й таб "Скрейпери" в адмінці: список зі статусом останнього запуску, "Запустити зараз" (реальний `ScraperOrchestrator.run_single()`), "+ Додати сайт" — `custom`-стратегія зберігається як конфіг, але не запускається (400 з поясненням: новий сайт потребує вручну написаного парсера, авто-білдер парсерів не додавався, як і планувалось). Свідомо НЕ будував pause/resume для реального тижневого cron-джоба — фронтендова заглушка `scraperAPI.pause()/.resume()` вже була підключена лише до вимкненої legacy-системи, а не до реальної, і в самому запиті Phase 4.5 паузи не було. Перевірено наскрізно curl (реальний запуск Instagram-агента: 15 товарів, `last_run_status: success`; custom-агент коректно відхиляється з 400), `tsc --noEmit` чистий. Додатково — реальний Playwright-прогін (magic-link логін у справжньому браузері, всі 4 таби адмінки, клік "Запустити зараз" на **реальному** Cijene.me-агенті запустив справжній live-скрейп cijene.me через UI: **✓ Успішно · 783 товарів**, 0 помилок консолі). Деталі: `PHASE_4_PLAN.md` → Phase 4.5.

**Усі фази Phase 4 (4.0-4.6) завершені.**

20. **Bugfix — модалки "Про проєкт" і "Магазини" рендерились крихітною смужкою** (2026-07-15): користувач повідомив, що обидві модалки виглядають зламаними на десктопі й мобільному. Корінь проблеми — набагато ширший, ніж ці дві модалки: `tailwind.config.ts` визначає кастомні `spacing`-токени з іменами `xs/sm/md/lg/xl/2xl/3xl` (для `p-*`/`gap-*` за брифом), а стандартна `maxWidth`-шкала Tailwind використовує ТІ САМІ імена — дефолтна тема-функція `maxWidth` домішує весь `spacing` scale ПІСЛЯ власних named-розмірів, тож кастомні spacing-значення (3rem/4rem/0.5rem/0.25rem) мовчки перекривали реальні (42rem/48rem/24rem/20rem) в КОЖНОМУ використанні `max-w-2xl`/`max-w-3xl`/`max-w-sm`/`max-w-xs` по всьому застосунку — не лише в `AboutModal`/`StoresModal`, а й в обох виглядах `ShoppingListModal`, `ShoppingListView`, `AuthModal`, панелі тарифів в адмінці, і мертвому (не підключеному) `SearchBar.tsx`. Спроби виправити на рівні конфігу — `extend.maxWidth`, повна заміна `theme.maxWidth` (не `extend`), нативний v4 `@theme`-блок в `globals.css` — усі не спрацювали навіть після повністю чистого ребілду (`.next` + `node_modules/.cache` видалені): цей проєкт вантажить `@config '../../tailwind.config.ts'` (Tailwind v4 3.x compat-шар для v3-style конфігів), і той компат-шар продовжує домішувати spacing в maxWidth незалежно від того, що написано в конфізі — підтверджена, відтворювана поведінка, не здогад. Фінальне рішення: замінено кожне використання на arbitrary-value синтаксис (`max-w-[42rem]` замість `max-w-2xl` і т.д.) — це повністю обходить theme-резолюцію. Заразом виявлений і виправлений ДРУГИЙ, окремий мобільний баг у `StoresModal.tsx`: `<table>` без `overflow-x-auto` і без `min-width` — URL-посилання (клас `break-all`) переносились по одній літері на рядок на вузьких екранах; додано `overflow-auto` на обгортку + `min-w-[520px]` на таблицю, тепер скролиться горизонтально замість того, щоб ламати текст. Перевірено Playwright-скріншотами на 1440×900 і 390×844 (iPhone-розмір) для обох модалок + AuthModal (той самий root-cause фікс) — усі рендеряться коректно, 0 нових помилок консолі. `tsc --noEmit` чистий.

21. **Доповнення Phase 4.6 — словниковий перекладач + реальний бекфіл `name_i18n` + 2 знайдені баги пошуку** (2026-07-17, готово): Phase 4.6 (п.18) зробила поле `name_i18n` і фолбек-логіку, але жоден перекладач нічого не писав у нього — Groq AI шлях був єдиним і навмисно без ключа, тож всі 287 реальних товарів мали `name_i18n: {}`. Запит: перекласти саме загальну назву товару (не бренд) — "Mlijeko Imlek Moja kravica" → "Молоко Imlek Moja kravica" в `ukr`. Новий `backend/app/services/grocery_dictionary.py` — безкоштовний детермінований словник (~150 слів, зібраний з реального словника всіх 287 товарів: молочка/бакалія/м'ясо-риба/овочі/фрукти/напої/солодощі/гігієна + прикметники свіжий/білий/червоний/мелений/кислий тощо), diacritic-insensitive нормалізація ("č"/"c" — той самий ключ), перекладає лише впізнані токени, решту (бренди, номери моделей, відсотки) лишає як є. `translation_service.translate_name()` тепер пробує словник першим, AI (перейменований `_translate_name_ai`) — лише якщо словник нічого не впізнав. Автоматично рахується при кожному живому скрейпі (`products.py::_persist_live_products`); одноразовий `backend/scripts/backfill_translations.py` прогнаний по існуючих 287 — 281 (98%) отримали переклад, 6 без перекладу (Coca Cola, Red Bull, Munchmallow, Lino čokolino, Bananica Soko Štark, Smoki Flips Štark) — чисті бренд/product-line назви без жодного загального слова, це правильна поведінка, не пропуск. Попутно знайдено і виправлено 2 реальні баги, що ламали `/search/products` для БУДЬ-ЯКОГО запиту (не лише перекладеного): (1) на колекції `products` не було text-індексу — `$text` кидав виняток, `except Exception` мовчки ковтав його, і `name_i18n`-regex-фолбек ніколи не встигав спрацювати; виправлено створенням індексу при старті (`main.py`, idempotent) + розділенням try/except в `search_service.py`, щоб майбутній збій `$text` більше не блокував фолбек; (2) `ProductSummary.source` в `search.py` вимагав `str`, а всі товари з cijene.me мають `source: None` (агрегація кількох магазинів в одному товарі) — кожен реальний пошук падав з 500 на валідації відповіді; виправлено на `Optional[str]`. Перевірено наскрізно: curl проти реального бекенда (`/products/matrix?lang=ukr|rus|eng`, `/search/products?q=молоко&lang=ukr` → 9 результатів вкл. "Кисле Молоко Drezga", `?q=milk&lang=eng` → 13, `?q=сир&lang=ukr` → 19) і реальний Playwright-браузер на `localhost:3001/ukr` — таблиця цін показує "Молоко 2.8% Lazine", "Йогурт Imlek Moja kravica sa 2.8% mm", "Буряк Natureta" тощо, бренди недоторкані. 0 нових помилок консолі (лише передіснуючі favicon 404 + очікуваний 401 для неавторизованої сесії). Деталі: `PHASE_4_PLAN.md` → Phase 4.6 (розділ "Follow-up 2026-07-17").

22. **Bugfix — пошук у 2 місцях: hero-пошук на лендінгу (декоративний) + пошук на сторінці створення списку (живий скрейп на кожне відкриття)** (2026-07-17): користувач повідомив про два окремі баги пошуку поспіль.

    **(a) Hero-пошук на лендінгу.** `<input>` + кнопка "Знайти" в `LandingPageDesignBrief.tsx` не мали `value`/`onChange`/жодного обробника — чиста верстка з дизайн-брифу, ніколи не підключена до логіки. Виправлено: контрольований `searchQuery` (стейт у батьківському компоненті), живий client-side фільтр `products.filter(p => p.name.toLowerCase().includes(searchQuery))`, застосований і до `PriceMatrixLanding`, і до `PriceCardsMobile` (обидва рекомпутять групування категорій самі, з пропа); додано локалізований `noResults` для всіх 6 мов. Перевірено Playwright: "молоко" → 11 рядків з коректно перерахованими заголовками категорій ("Молочка · 8"), неіснуючий запит → повідомлення "Нічого не знайдено", очищення поля → всі 299 рядків повертаються.

    **(b) Пошук на сторінці створення списку — глибший, окремий баг.** `ShoppingListModal.tsx` (відкривається через "Список покупок" в наві) на кожне відкриття бив `GET /products/by-category`, а цей ендпоїнт — **не кешований запит**, а повний живий скрейп cijene.me (~10-15с, той самий, що й "Оновити ціни"), хоча ідентичні дані (з `category`-полем) вже лежали в пропі `products`, завантаженому один раз на лендінгу через швидкий `/matrix-cached`. Під React 18 StrictMode (dev) ефект викликається двічі — це запускало ДВА одночасних живих скрейпи при кожному відкритті модалки; якщо перегони або флакі зовнішнього сайту повертали порожній/неповний результат, `categories` лишався `null`, а через відсутність фолбеку на вже завантажений `products`-проп модалка мертво зависала на "Товари не знайдені" — і пошук виглядав "не працює", бо фільтрувати було нічого. Відтворено наживо: реальний виклик `/by-category` повернув 200 з 12 категоріями через прямий `fetch`, але паралельний виклик з додатку (StrictMode-дубль) впав у порожній стан. Виправлено видаленням live-фетчу повністю: групування категорій тепер рахується client-side з уже завантаженого `products`-пропа через `groupByCategory()` (перевикористаний хелпер з `lib/productMatrix.ts`, той самий, яким уже рахує групи таблиця на лендінгу) — миттєво, без мережі, без сценарію відмови. Заразом прибрано мертвий код: стейти `categories`/`loadingCategories`, гілка "flat fallback" рендеру (`filteredFlat`), невикористовуваний `categoryLabel`-проп у `ProductRow`, переклад-ключі `category`/`loadingCategories` у всіх 6 локалях (`productsAPI.byCategory()` в `api.ts` і сам бекенд-ендпоїнт `/by-category` лишені — працюючий, просто більше нізвідки не викликаються в UI). Перевірено наскрізно Playwright: відкриття модалки — миттєве (без 10-15с паузи), пошук "молоко" → "Молочка (8)" + "Інше (1)" з коректними перекладеними назвами, клік "+ Додати" → лічильник кошика оновився, "Створити список" → реальний `router.push` на `/ukr/list/{id}` зі створеним товаром і живою ціною (тестовий запис після перевірки видалений з БД). `tsc --noEmit` чистий, 0 нових помилок консолі.

---

**Остання оновлена:** 2026-07-17
**Автор:** Serhii Riabko