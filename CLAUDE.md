# CLAUDE.md — Insta-data Project Instructions

Цей файл надає контекст Claude Code при роботі з цим проектом.

---

## 📋 Проект Insta-data

**Мета:** Автоматичний моніторинг цін товарів харчування через Instagram + офіційні сайти магазинів Чорногорії.

**Статус:** Phase 0 — Landing Variant A ✅ (2026-07-01)

**Tech Stack:**
- **Frontend:** Next.js 15 + React 19 + Tailwind 4 + Framer Motion
- **Backend:** FastAPI + SQLAlchemy 2.0 + Pydantic
- **Databases:** MongoDB (primary) + PostgreSQL (history) + Redis (cache)
- **Scrapers:** instagrapi + Playwright + BeautifulSoup4 + Pillow
- **Infrastructure:** Docker + Docker Compose + supervisord (future)

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
| **ProductsModal** | `src/components/ProductsModal.tsx` | Products listing dialog | ✅ Scaffolded |
| **StoresModal** | `src/components/StoresModal.tsx` | Stores info dialog | ✅ Scaffolded |
| **AboutModal** | `src/components/AboutModal.tsx` | About project dialog | ✅ Scaffolded |

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

### Colors
```
Dark Green:    #2D5016  (Primary)
Light Green:   #4CAF50  (Cheapest price)
Gold:          #D4AF37  (Accent)
Dark BG:       #1A1A1A  (Background)
Text:          #FFFFFF  (Text)
```

### Typography
```
Font: Inter (sans-serif)
Sizes: 12px, 14px, 16px, 18px, 24px, 32px
Weight: 400 (regular), 600 (semibold), 700 (bold)
```

### Components
```
PriceMatrix    ← Main component (товари × магазини × ціни)
SearchBar      ← Real-time search
WishlistButton ← Add/remove from wishlist
PriceChart     ← Recharts для graphing
LanguageSelector ← UKR/RUS/MNE switcher
```

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

### ✅ Phase 1: Frontend Integration (2026-07-02)

**Backend Endpoints (Commit a766bc9):**
- ✅ `GET /api/v1/products/matrix` — price matrix for landing table
- ✅ `GET /api/v1/products/list` — product list with prices
- Helper functions: `calculate_cheapest()`, `format_product_row()`
- Schemas: `PriceMatrixResponse`, `ProductListResponse`

**Frontend Integration (Commit 89565d4):**
- ✅ **api.ts:** Added `productsAPI` with methods:
  - `priceMatrix(lang)` → GET /api/v1/products/matrix?lang=ru|uk|en
  - `list(limit, skip)` → GET /api/v1/products/list
  
- ✅ **LandingPageDesignBrief.tsx:** 
  - Fetch real data from backend on component mount
  - useEffect hook calls `productsAPI.priceMatrix(lang)` when lang changes
  - Loading state with "Завантажуємо ціни..." message
  - Fallback to MOCK_PRODUCTS/MOCK_STORES if API fails
  - Pass real data to PriceMatrixLanding component
  
- ✅ **Data Flow:**
  1. Component mounts → useEffect triggered
  2. API call to backend
  3. Response: {stores, products, updated_at, total_products}
  4. State updates → PriceMatrixLanding re-renders with real data
  5. If error → shows loading, keeps mock data as fallback

**Ready for Testing:**
- ✅ Backend endpoint: http://localhost:8000/api/v1/products/matrix
- ✅ Frontend component: http://localhost:3000 (with backend running)
  
- **Phase 2: Mock Data** (Tomorrow)
  - [ ] Seed MongoDB with 8 products (from landing mock data)
  - [ ] Test endpoints via Postman
  
- **Phase 3: Real Scrapers** (Days 3-5)
  - [ ] Aroma.me, Voli.me, HDL.me, IDEA.me (Playwright + BeautifulSoup)
  - [ ] Instagram scraper (instagrapi + OCR)
  
- **Phase 4: Background Tasks** (Days 6-7)
  - [ ] 24h auto-scan scheduler
  - [ ] Retry logic + error handling
  
- **Phase 5: Security & Polish** (Days 8-9)
  - [ ] JWT authentication
  - [ ] Rate limiting
  - [ ] Integration tests

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
  
- [ ] Phase 1: Instagram Parser POC
  - [ ] instagrapi login
  - [ ] Post scraping (48 годин)
  - [ ] OCR + regex для vitяу товарів
  - [ ] Image normalization
  - [ ] Unit tests & validation

- [ ] Phase 2: Web Scrapers (4 магазини)
  - [ ] Playwright for JS rendering
  - [ ] BeautifulSoup for HTML parsing
  - [ ] Deduplication logic
  - [ ] Parallel execution

- [ ] Phase 3: Backend API (FastAPI)
- [ ] Phase 4: Integration & Testing

---

**Остання оновлена:** 2026-07-01
**Автор:** Serhii Riabko