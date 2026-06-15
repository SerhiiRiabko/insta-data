# Insta-data — Technology Stack & Architectural Decisions

---

## 🛠️ Technology Stack

### **Frontend**
| Компонент | Технологія | Версія | Причина |
|-----------|-----------|--------|---------|
| **Framework** | Next.js | 15.x | SSR + SSG, optimize для SEO, швидкість, спільний досвід з MonteLand |
| **React** | React | 19.x | Server Components, потужна UI |
| **Styling** | Tailwind CSS | 4.x | Utility-first, green+gold色板, швидкі прототипи |
| **Animations** | Framer Motion | 11.x | Плавні переходи, red/green price changes |
| **Data Fetching** | TanStack Query | 5.x | Кешування, retry logic, стан синхронізації |
| **i18n** | next-intl | 3.x | Мультимовність (UKR, RUS, MNE), URL segments |
| **Charts** | Recharts | 2.x | Графіки цін, легкі, React-友好 |
| **Icons** | Heroicons | 2.x | UI components, вбудовані SVG |
| **Validation** | Zod | 3.x | Type-safe parsing API responses |
| **HTTP Client** | axios | 1.x | Простота, interceptors, timeout handling |

### **Backend**
| Компонент | Технологія | Версія | Причина |
|-----------|-----------|--------|---------|
| **Framework** | FastAPI | 0.104+ | Async, OpenAPI docs, validation via Pydantic |
| **ORM (SQL)** | SQLAlchemy | 2.0+ | PostgreSQL integration, migrations via Alembic |
| **Migrations** | Alembic | 1.13+ | Version control для БД schema |
| **NoSQL Driver** | motor (async) | 3.3+ | Async MongoDB driver, non-blocking |
| **Validation** | Pydantic | 2.x | Type hints, JSON schema, errors |
| **Logging** | structlog | 24.x | Structured logging, JSON output |
| **API Docs** | FastAPI Docs | Built-in | /docs + /redoc endpoints |
| **Testing** | pytest | 8.x | Unit + integration tests |
| **Code Quality** | black + ruff | Latest | Formatting, linting |

### **Databases**
| Компонент | Технологія | Версія | Причина |
|-----------|-----------|--------|---------|
| **Primary DB** | MongoDB | 6.x | Гнучкість schema, full-text search, швидкість |
| **Timeseries DB** | PostgreSQL | 16.x | price_history, ACID, аналітика |
| **Cache** | Redis | 7.x | Session store, rate limiting, kesh на пошук |
| **Search** | MongoDB Atlas Search | Latest | Full-text search, FTS indexes |

### **Infrastructure & DevOps**
| Компонент | Технологія | Версія | Причина |
|-----------|-----------|--------|---------|
| **Containerization** | Docker | 24.x | Isolate scrapers, consistency |
| **Orchestration** | Docker Compose | 3.x | Local development, simple deployment |
| **Reverse Proxy** | Nginx | Latest | SSL termination, load balancing |
| **Process Manager** | supervisord | 4.x | (як у hrd-minion) для manage bot/services |
| **CI/CD** | GitHub Actions | Latest | Auto-test + deploy |

### **Web Scraping & Parsing**
| Компонент | Технологія | Версія | Причина |
|-----------|-----------|--------|---------|
| **Instagram** | instagrapi | 2.x | Account auth, post parsing, simpler than API |
| **Web Scraping** | Playwright | 1.40+ | Headless browser, JS rendering (для NEXT_DATA) |
| **HTML Parsing** | BeautifulSoup4 | 4.12+ | Fallback для static sites |
| **Image Processing** | Pillow | 10.x | Crop, resize, normalize product images |
| **OCR** | pytesseract + Tesseract | 5.x | Price extraction dari gambar |
| **Regex** | Python re | Built-in | Fallback pattern matching |

### **Monitoring & Observability**
| Компонент | Технологія | Версія | Причина |
|-----------|-----------|--------|---------|
| **Logging** | structlog | 24.x | JSON logs → centralized (FUTURE) |
| **Error Tracking** | Sentry | Latest | Exception monitoring |
| **Status Page** | Uptime Kuma | Latest | Public status, monitoring |
| **Metrics** | Prometheus (FUTURE) | Latest | Performance metrics |

---

## 🏗️ Архітектурні Рішення

### **1. Мікросервісна Архітектура**

**Рішення:** Розділити application на 5 незалежних сервісів:

```
┌────────────────────────────────────────────────────┐
│           API Gateway (FastAPI)                    │
│        /api/v1/* + /health + /docs                │
└────────────────┬─────────────────────────────────┘
                 │
    ┌────────────┼────────────┬──────────────┐
    │            │            │              │
┌───▼──┐   ┌────▼────┐  ┌────▼────┐  ┌───▼───┐
│Search│   │ Wishlist│  │ History │  │ Price │
│Service   │ Service │  │ Service │  │Tracker│
└───┬──┘   └────┬────┘  └────┬────┘  └───┬───┘
    │           │            │           │
    └───────────┼────────────┴───────────┘
                │
    ┌───────────┼─────────────────┐
    │           │                 │
┌───▼───────┐   │         ┌─────▼────┐
│ NoSQL DB  │   │         │SQL DB    │
│(MongoDB)  │   │         │(PostgreSQL)
└───────────┘   │         └──────────┘
                │
    ┌───────────▼──────────────────────┐
    │ Scraper Orchestrator (Scheduler) │
    │ ┌─────────┐ ┌─────────┐ ┌──────┐│
    │ │Instagram│ │Web Scrs.│ │Cache││
    │ │ Parser  │ │(4 sites)│ │(Redis)
    │ └─────────┘ └─────────┘ └──────┘│
    └────────────────────────────────┘
```

**Причина:**
- Кожен сервіс має одну відповідальність (SRP)
- Можна масштабувати окремо (e.g., більше workers для scrapers)
- Легко добавити нові сервіси (e.g., Notification Service для вебхуків)
- Ізольована логіка для тестування

### **2. БД Стратегія: Polyglot Persistence**

**Рішення:** Використовуємо MongoDB + PostgreSQL

#### **MongoDB (Primary DB)**
```
Чому:
- Гнучка schema (продукти можуть мати різні атрибути)
- Full-text search на product_name (вбудовано)
- Fast writes для scrapers (шаблонний document)
- Simple price.history append operation (atomic)
- Легко сховати raw_data з різних джерел

Collections:
- products           (10k-100k docs, index на: name, slug, created_at)
- scraped_data       (logs of scrapes, TTL index 90 днів)
- wishlist           (users, index на user_id)
```

#### **PostgreSQL (Timeseries + Analytics)**
```
Чому:
- ACID гарантії для точних цін
- Timeseries queries (дані за період)
- Graphing + trend analysis
- Compliance (якщо потрібно)

Tables:
- price_history      (id, product_id, store, price, timestamp)
- products_meta      (product_id, product_name, sources[], created_at)
```

**Sync Strategy:**
```
MongoDB ──[async insert]──> PostgreSQL
   ↓                            ↓
Real-time search          Historical analysis
   ↓                            ↓
 Fresh data              Trends, anomalies, alerts
```

### **3. Image Normalization Strategy**

**Рішення:** Один формат, один стиль

```python
# ImageProcessor service
def normalize_product_image(image_path: str) -> str:
    """
    Стандартизуємо всі товарні фото:
    - Crop до 1:1 (product only, no background)
    - Resize до 500x500px
    - Format: JPEG (80% quality)
    - Watermark: "insta-data.me" (opcional)
    - Store: AWS S3 or local /images/
    """
```

**Workflow:**
```
Instagram Post ─┐
Web Scrape     ├─> [Raw Image] ─> [Normalize] ─> [Upload S3] ─> [MongoDB.image_url]
               │
```

### **4. Price Update Frequency Detection**

**Рішення:** Адаптивний моніторинг

```
Алгоритм:
1. Скрейпимо всі 4 сайти щодня о 08:00
2. Порівнюємо з попереднім днем
3. Якщо > 10% товарів змінило ціну → сайт оновлюється щодня
4. Якщо < 5% товарів змінило → оновлюємо раз на 3 дні
5. Зберігаємо last_update_frequency в products.meta

Результат:
aroma.me     → Daily
voli.me      → Daily
hdl.me       → Every 3 days
idea.co.me   → Every 3 days
```

### **5. Price History Storage (Rotation Strategy)**

**Рішення:** Останні 3 + поточна в NoSQL, весь history в SQL

```json
// MongoDB products collection
{
  "product_name": "Jaffa Biskvit",
  "current_prices": {
    "aroma": 1.39,
    "voli": 0.85,
    "hdl": 0.85,
    "idea": 1.49
  },
  "price_history": [
    { "timestamp": "2026-06-15T14:00", "prices": {...} },  // NEW
    { "timestamp": "2026-06-14T14:00", "prices": {...} },  // SHIFT
    { "timestamp": "2026-06-13T14:00", "prices": {...} }   // SHIFT
    // Old data DELETED to save space
  ]
}
```

```sql
-- PostgreSQL price_history (complete history)
INSERT INTO price_history (product_id, store_name, price, timestamp)
VALUES ('jaffa-biskvit-150g', 'aroma', 1.39, '2026-06-15T14:00Z');
-- Зберігаємо ВЕСЬ history для графіків
```

**Причина:**
- Швидка доступ до поточної ціни (NoSQL)
- Компактне зберігання (3 версії in place, не весь history)
- Графіки беруть дані з SQL (не обтяжуємо NoSQL)
- Легко визначити тренд (↑/↓/→)

### **6. Мультимовність через next-intl**

**Рішення:** URL segments + i18n middleware

```
Structure:
/[lang]/
├── /ukr/
├── /rus/
└── /mne/

URL Examples:
- https://insta-data.me/ukr/  (Ukrainian)
- https://insta-data.me/rus/  (Russian)
- https://insta-data.me/mne/  (Montenegrin)

Backend:
- API returns all data in main language + translations
- Frontend requests with ?lang=ukr query param
```

**Translations Storage:**
```
frontend/
├── locales/
│   ├── ukr.json    { "search": "Пошук", ... }
│   ├── rus.json    { "search": "Поиск", ... }
│   └── mne.json    { "search": "Pretraga", ... }
```

### **7. Instagram Parsing Strategy**

**Рішення:** Account-based parsing via instagrapi

```python
# Backend: instagram_parser.py
async def scrape_instagram_posts():
    """
    1. Login via instagrapi (email + password)
    2. Fetch posts from last 48 hours (user account)
    3. Extract:
       - product_name (regex + AI parsing)
       - images (download + normalize)
       - prices per store (OCR + regex)
    4. Deduplicate by image_hash
    5. Save to MongoDB.scraped_data
    """
```

**Flow:**
```
Instagram Account ─> instagrapi Login ─> Fetch Posts
    ↓                                      ↓
User Photo                          OCR + Regex
    ↓                                      ↓
prices: "Voli: 0.85€, Aroma: 1.39€" ─> Extract
                                         ↓
                                    MongoDB update
```

### **8. Web Scraper Parallelization**

**Рішення:** Async scrapers + Docker containers

```python
# backend/scrapers/orchestrator.py
async def run_daily_scrape():
    tasks = [
        aroma_scraper.scrape(),
        voli_scraper.scrape(),
        hdl_scraper.scrape(),
        idea_scraper.scrape()
    ]
    results = await asyncio.gather(*tasks)
    await merge_and_deduplicate(results)
```

**Docker Setup:**
```yaml
services:
  aroma-scraper:
    image: insta-data/aroma-scraper:latest
    environment:
      - MONGODB_URL=mongodb://mongo:27017
    
  voli-scraper:
    image: insta-data/voli-scraper:latest
  
  hdl-scraper:
    image: insta-data/hdl-scraper:latest
  
  idea-scraper:
    image: insta-data/idea-scraper:latest
```

### **9. Wishlist Persistence**

**Рішення:** localStorage (anonymous) + Database (auth users)

```
Anonymous User:
└─ localStorage.wishlist = ["product-id-1", "product-id-2"]
   (Browser only, lost on clear cache)

Authenticated User (FUTURE):
└─ MongoDB.wishlist = { user_id, product_ids[] }
   (Persistent, synced across devices)
```

### **10. Search & Filtering Architecture**

**Рішення:** Full-text search на MongoDB + Redis cache

```
User Input: "jaffa"
    ↓
GET /api/v1/search?q=jaffa&source=instagram&lang=ukr
    ↓
Backend:
1. Check Redis cache (key: "search:jaffa:instagram:ukr")
2. If miss → Query MongoDB:
   db.products.find({
     $text: { $search: "jaffa" },
     source: "instagram"
   })
3. Cache result 1 hour
4. Return top 20 results
    ↓
Frontend:
- Display results in grid
- Sort by: price (asc), name (asc), recency (desc)
```

---

## 📦 Project Structure

```
insta-data/
├── frontend/                          ← Next.js 15
│   ├── public/
│   │   └── images/
│   │       └── stores/               ← Aroma, Voli, HDL, IDEA logos
│   ├── src/
│   │   ├── app/
│   │   │   ├── [lang]/               ← i18n routing
│   │   │   │   ├── page.tsx          ← Home (matrix view)
│   │   │   │   ├── instagram/        ← Social media tab
│   │   │   │   ├── official/         ← Official sites tab
│   │   │   │   ├── wishlist/         ← User's wishlist
│   │   │   │   └── product/[slug]/   ← Product detail + chart
│   │   │   └── api/                  ← Route handlers
│   │   ├── components/
│   │   │   ├── PriceMatrix.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── WishlistButton.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── LanguageSelector.tsx
│   │   │   ├── StoreIcon.tsx
│   │   │   └── ResponsiveGrid.tsx
│   │   ├── lib/
│   │   │   ├── api-client.ts         ← Axios + interceptors
│   │   │   ├── utils.ts
│   │   │   └── constants.ts
│   │   ├── locales/
│   │   │   ├── ukr.json
│   │   │   ├── rus.json
│   │   │   └── mne.json
│   │   └── styles/
│   │       └── globals.css            ← Tailwind + custom theme
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── package.json
│
├── backend/                           ← FastAPI
│   ├── app/
│   │   ├── main.py                   ← FastAPI app instance
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── prices.py     ← /prices/* routes
│   │   │       │   ├── search.py     ← /search routes
│   │   │       │   └── wishlist.py   ← /wishlist routes
│   │   │       └── router.py         ← Include all routers
│   │   ├── services/
│   │   │   ├── search_service.py     ← MongoDB queries
│   │   │   ├── price_tracker.py      ← Price updates
│   │   │   ├── wishlist_service.py
│   │   │   └── image_processor.py
│   │   ├── models/
│   │   │   ├── product.py            ← Pydantic schemas
│   │   │   ├── price.py
│   │   │   └── wishlist.py
│   │   ├── database/
│   │   │   ├── mongodb.py            ← MongoDB connection
│   │   │   ├── postgres.py           ← PostgreSQL connection
│   │   │   └── migrations.py
│   │   ├── core/
│   │   │   ├── config.py             ← Environment vars
│   │   │   ├── logger.py             ← Logging setup
│   │   │   └── exceptions.py
│   │   └── middleware/
│   │       ├── cors.py
│   │       └── rate_limit.py
│   ├── alembic/                       ← SQL migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── requirements.txt
│   └── main.py                        ← Entry point
│
├── scrapers/                          ← Microservices (Docker)
│   ├── instagram_parser/
│   │   ├── scraper.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── aroma_scraper/
│   │   ├── scraper.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── voli_scraper/
│   │   ├── scraper.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── hdl_scraper/
│   │   ├── scraper.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── idea_scraper/
│   │   ├── scraper.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── orchestrator/                  ← Scheduler
│       ├── orchestrator.py
│       └── Dockerfile
│
├── docker-compose.yml                 ← Local development
├── .env                              ← Credentials
├── .env.example
├── .gitignore
└── docs/
    ├── PROJECT_INFO.md
    ├── BUSINESS_LOGIC.md
    ├── TECHNOLOGY.md
    └── API.md                        ← OpenAPI spec (TBD)
```

---

## 🚀 Deployment & Infrastructure

### **Local Development**
```bash
# Start all services
docker-compose up -d

# Services running:
- Frontend:      http://localhost:3000
- Backend API:   http://localhost:8000
- MongoDB:       localhost:27017
- PostgreSQL:    localhost:5432
- Redis:         localhost:6379
```

### **Production (TBD)**
```
Option A: Traditional Server (similar to hrd-minion)
- VPS (Hetzner)
- Docker + supervisord
- Nginx reverse proxy
- GitHub Actions CI/CD

Option B: Serverless (FUTURE)
- Frontend: Vercel
- Backend: AWS Lambda / Google Cloud Functions
- DB: MongoDB Atlas + AWS RDS
```

---

## 🔐 Security Considerations

| Риск | Мітігація |
|------|----------|
| **Instagram Creds** | .env файл, не в git, rotate токени |
| **API Rate Limiting** | Redis-backed rate limiter (100 req/min) |
| **CORS** | Whitelist origins (localhost:3000 dev, domain prod) |
| **SQL Injection** | SQLAlchemy ORM + Pydantic validation |
| **XSS** | React escaping + CSP headers |
| **Data Breach** | Encrypt sensitive data at rest, HTTPS only |

---

## 📈 Performance Targets

| Метрика | Ціль | Як досягнути |
|---------|------|--------------|
| Page Load (Time to Interactive) | < 2s | Optimize Next.js, Redis cache |
| API Response (search) | < 100ms | MongoDB FTS index, caching |
| Price Update Latency | < 5 min | Async scrapers, queue system |
| Image Load | < 1s | S3 CDN, WebP format |
| Database Query | < 50ms | Proper indexing, query optimization |

---

## 🧪 Testing Strategy

```
Backend:
├── Unit Tests (pytest)
│   ├── Services (search, price_tracker, image_processor)
│   └── Utils (parsing, normalization)
├── Integration Tests
│   ├── API endpoints
│   ├── MongoDB queries
│   └── PostgreSQL operations
└── E2E Tests (Playwright)
    ├── User workflows
    └── Scraper accuracy

Frontend:
├── Component Tests (Vitest)
├── UI Tests (Storybook)
└── E2E Tests (Cypress/Playwright)
    ├── Search functionality
    ├── Wishlist add/remove
    └── Language switching
```

---

## 📚 Документація & Стандарти

| Артефакт | Інструмент |
|----------|-----------|
| API Docs | FastAPI /docs (Swagger) |
| DB Schema | dbdocs.io (TBD) |
| Architecture Diagrams | Mermaid |
| ADRs (Architectural Decision Records) | TECHNOLOGY.md |
| Changelog | CHANGELOG.md (per commit) |

---

## 🎯 Next Technical Steps

1. ✅ Defined tech stack
2. ⏳ Set up local Docker environment
3. ⏳ Initialize MongoDB + PostgreSQL schemas
4. ⏳ Build Instagram scraper POC
5. ⏳ Build web scrapers for 4 sites
6. ⏳ Set up FastAPI skeleton
7. ⏳ Build Frontend component library
8. ⏳ Integrate all services
9. ⏳ CI/CD setup
10. ⏳ Deploy to production
