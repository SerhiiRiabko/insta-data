# 🏛️ INSTA-DATA — АРХІТЕКТУРА ПРОЕКТУ

**Версія:** 1.0  
**Дата:** 2026-06-16  
**Статус:** АРХІТЕКТУРНИЙ ПЛАН — готовий до реалізації  

---

## 📌 НАПАД НА ПРОБЛЕМУ

### **Бізнес-Проблема**
```
Чорногорія: 4 головних магазинів (Aroma, Voli, HDL, IDEA) 
+ Instagram з постами про товари
= Немає централізованого місця для порівняння цін

Вирішення: Платформа що скрейпить обидва джерела 
+ показує матрицю товари×магазини×ціни 
+ 3 мови + красивий UI
```

### **Ключові Вимоги**
| # | Вимога | Критичність | Рішення |
|----|--------|------------|---------|
| 1 | Парсинг Instagram постів (48 год) | 🔴 MUST | instagrapi + Tesseract OCR |
| 2 | Скрейп 4 магазинів (ціни + назви) | 🔴 MUST | Playwright + BeautifulSoup |
| 3 | Матриця товари × магазини × ціни | 🔴 MUST | React Grid + MongoDB |
| 4 | Пошук товарів на обох табах | 🔴 MUST | MongoDB full-text search |
| 5 | Wishlist (список для отримання) | 🟡 SHOULD | MongoDB + React state |
| 6 | Історія цін для графіків | 🟡 SHOULD | PostgreSQL timeseries |
| 7 | 3 мови (УКР/РУС/МНЕ) | 🟡 SHOULD | next-intl |
| 8 | Красивий UI (зелений + золото) | 🟡 SHOULD | Tailwind 4 + Framer Motion |
| 9 | Мобільна адаптивність | 🟢 NICE | Responsive design |
| 10 | Розширення на бота | 🟢 NICE | REST API structure |

---

## 🏗️ АРХІТЕКТУРА —層ВНЕВИЙ ПОГЛЯД

```
┌─────────────────────────────────────────────────────────────┐
│                    КОРИСТУВАЧ (Web Browser)                 │
│                    http://localhost:3003                     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼──────┐               ┌──────▼────┐
    │ Frontend   │               │ API Docs  │
    │ Next.js 15 │◄─ REST API ◄─►│ /docs     │
    │ React 19   │ (JSON)        │ Swagger   │
    │ Tailwind 4 │               └───────────┘
    └────┬──────┘
         │
         │ HTTP/JSON
         │
    ┌────▼──────────────────────────────────┐
    │    BACKEND — FastAPI (8001:8000)      │
    │                                         │
    │  ┌──────────────────────────────────┐  │
    │  │ API Gateway                      │  │
    │  │ /api/v1/prices/{tab}             │  │
    │  │ /api/v1/search                   │  │
    │  │ /api/v1/wishlist                 │  │
    │  │ /api/v1/scrapers/status          │  │
    │  └──────────────────────────────────┘  │
    │                                         │
    │  ┌──────────────┬──────────────┐       │
    │  │  Services    │  Scrapers    │       │
    │  │              │              │       │
    │  │ - Search Svc │ - Instagram  │       │
    │  │ - Price Svc  │ - Aroma      │       │
    │  │ - Wishlist   │ - Voli       │       │
    │  │ - Image Proc │ - HDL        │       │
    │  │              │ - IDEA       │       │
    │  │              │ - Scheduler  │       │
    │  └──────────────┴──────────────┘       │
    │                                         │
    │  ┌──────────────┬──────────────┐       │
    │  │  Databases   │  Cache       │       │
    │  │              │              │       │
    │  │ - MongoDB    │ - Redis      │       │
    │  │   (products) │   (search)   │       │
    │  │              │              │       │
    │  │ - PostgreSQL │              │       │
    │  │   (history)  │              │       │
    │  └──────────────┴──────────────┘       │
    └────────────────────────────────────────┘
         │                      │
    ┌────▼──────┐          ┌────▼──────┐
    │ Docker     │          │ External  │
    │ Network    │          │ Services  │
    │            │          │           │
    │ - mongo    │          │ - Tesseract (OCR)
    │ - postgres │          │ - Playwright
    │ - redis    │          │ - BeautifulSoup
    └────────────┘          └───────────┘
```

---

## 📊 DATA FLOW — ОСНОВНІ СЦЕНАРІЇ

### **Сценарій 1: Користувач Шукає Товар**

```
┌──────────────────────────────────────────────────────┐
│ FRONTEND: Користувач вводить "млеко" у SearchBar     │
│ (Tab: "📱 Соціальні мережи")                        │
└──────────────┬──────────────────────────────────────┘
               │
               │ GET /api/v1/search?q=млеко&source=instagram
               │ Headers: {Content-Type: application/json}
               │
    ┌──────────▼──────────────────────────────┐
    │ BACKEND: SearchService.search()          │
    │                                          │
    │ 1. Query MongoDB.products:                │
    │    {                                      │
    │      name: { $regex: "млеко", $options: "i" },
    │      source: "instagram"                  │
    │    }                                      │
    │                                          │
    │ 2. Return top 20 results sorted by       │
    │    updated_at DESC                       │
    └──────────┬──────────────────────────────┘
               │
               │ Response:
               │ {
               │   "results": [
               │     {
               │       "id": "507f...",
               │       "name": "Млеко 1L",
               │       "description": "Лактозно свежо",
               │       "image_url": "https://...",
               │       "prices": [
               │         {"store": "instagram", "price": 1.49, "timestamp": "2026-06-16T10:00"}
               │       ],
               │       "last_updated": "2026-06-16"
               │     }
               │   ]
               │ }
               │
    ┌──────────▼──────────────────────────────┐
    │ FRONTEND: Render PriceMatrix             │
    │ - Таблиця з товарами в рядках           │
    │ - Магазини в стовпцях                   │
    │ - Найнижча ціна (зелена)                │
    └──────────────────────────────────────────┘
```

### **Сценарій 2: Автоматичний Скрейп Instagram (6 AM Kyiv)**

```
┌──────────────────────────────────────────────────────┐
│ APScheduler: Запускає run_instagram_scraper()        │
│ (Час: Щодня 06:00 Kyiv)                            │
└──────────┬──────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────┐
│ InstagramSessionManager:                             │
│ 1. Load session from disk (або login if new)        │
│ 2. self.client.user_medias() → 30 медіа             │
│ 3. Filter: last 48 hours                            │
└──────────┬──────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────┐
│ InstagramPostScraper.process_posts():                │
│ 1. Extract images from each post                    │
│ 2. Download image URL                               │
│ 3. Resize & save locally (optional)                 │
└──────────┬──────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────┐
│ PriceExtractor.extract_from_image():                 │
│ 1. OCR with Tesseract → raw text                    │
│ 2. Regex: find EUR prices (0.99€, €0.99, 0,99€)   │
│ 3. NLP: extract product name (first line)           │
│ 4. Return: {product_name, prices[], raw_text}      │
└──────────┬──────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────┐
│ ProductService.save_product():                       │
│ 1. Create dedup_hash = MD5(product_name + "instagram")
│ 2. Check if exists in MongoDB                       │
│ 3. If YES: append price to history                  │
│ 4. If NO: create new document                       │
│ 5. Log: "saved 45 products from Instagram"          │
└──────────┬──────────────────────────────────────────┘
           │
           ▼
    MongoDB.products (updated)
```

### **Сценарій 3: Скрейп Офіційних Сайтів (Паралельно)**

```
┌──────────────────────────────────────────────────────┐
│ ScraperOrchestrator.run_all_scrapers():              │
│ Запускає 4 скрейпери паралельно:                    │
│ - AromaScraper                                       │
│ - VoliScraper                                        │
│ - HDLScraper                                         │
│ - IdeaScraper                                        │
└──────────┬──────────────────────────────────────────┘
           │
    ┌──────┴──────┬──────────┬──────────┐
    │             │          │          │
┌───▼──┐   ┌──────▼──┐ ┌────▼──┐ ┌────▼──┐
│Aroma │   │Voli     │ │HDL    │ │IDEA   │
│      │   │         │ │       │ │       │
│Scrape│   │Scrape   │ │Scrape │ │Scrape │
│pages │   │pages    │ │pages  │ │pages  │
└────┬─┘   └────┬────┘ └───┬───┘ └────┬──┘
     │          │          │          │
     │ Extract products (name, price, URL)
     │
     └──────────┬──────────────────────┘
                │
       ┌────────▼────────┐
       │ Normalize Prices │
       │ EUR, 2 decimals  │
       └────────┬────────┘
                │
       ┌────────▼────────────────────┐
       │ Deduplicate & Save           │
       │ - MongoDB (current prices)   │
       │ - PostgreSQL (history)       │
       │ - Redis cache (search)       │
       └────────────────────────────┘
```

---

## 🗄️ БАЗА ДАНИХ — SCHEMA

### **MongoDB — ОСНОВНА БД (NoSQL)**

```javascript
// Collection: products
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "Млеко 1L",
  "description": "Свежо млеко, 3.5% масти",
  "category": "Млечни производи",
  "image_url": "https://cdn.example.com/products/mleko-1l.jpg",
  "source": "instagram",  // "instagram" | "aroma" | "voli" | "hdl" | "idea"
  "dedup_hash": "a1b2c3d4e5f6g7h8",  // MD5(name + source)
  "prices": [
    {
      "store": "instagram",  // eller: "aroma", "voli", etc
      "price": 1.49,
      "currency": "EUR",
      "timestamp": ISODate("2026-06-16T10:30:00Z")
    },
    {
      "store": "aroma",
      "price": 1.39,
      "currency": "EUR",
      "timestamp": ISODate("2026-06-16T09:15:00Z")
    }
  ],
  "created_at": ISODate("2026-06-15T08:00:00Z"),
  "updated_at": ISODate("2026-06-16T10:30:00Z"),
  
  // Denormalized for fast queries
  "current_prices": {
    "instagram": 1.49,
    "aroma": 1.39,
    "voli": 1.45,
    "hdl": 1.35,
    "idea": 1.55
  },
  "min_price": 1.35,
  "max_price": 1.55,
  "cheapest_store": "hdl"
}

// Index for fast search
db.products.createIndex({ name: "text", description: "text" })
db.products.createIndex({ dedup_hash: 1 })
db.products.createIndex({ source: 1, updated_at: -1 })
```

### **PostgreSQL — ІСТОРІЯ ЦІН (SQL)**

```sql
-- Table: price_history (для аналітики + графіків)
CREATE TABLE price_history (
  id SERIAL PRIMARY KEY,
  product_id VARCHAR(24) NOT NULL,  -- ObjectId from MongoDB
  product_name VARCHAR(255) NOT NULL,
  store VARCHAR(50) NOT NULL,       -- "aroma", "voli", etc
  price DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'EUR',
  timestamp TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT fk_product_id FOREIGN KEY (product_id)
    REFERENCES products(mongo_id) ON DELETE CASCADE,
  
  INDEX idx_product_store_time (product_id, store, timestamp),
  INDEX idx_store_time (store, timestamp),
  INDEX idx_timestamp (timestamp)
);

-- Sample query: Last 3 prices for "Млеко" at "aroma"
SELECT price, timestamp FROM price_history
WHERE product_id = 'abc123...' AND store = 'aroma'
ORDER BY timestamp DESC LIMIT 3;

-- Table: wishlist (if auth added)
CREATE TABLE wishlist (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  product_id VARCHAR(24) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### **MongoDB — WISHLIST**

```javascript
// Collection: wishlists
{
  "_id": ObjectId("..."),
  "user_id": "anonymous",  // або UUID якщо auth
  "products": [
    {
      "product_id": ObjectId("507f..."),
      "product_name": "Млеко 1L",
      "added_at": ISODate("2026-06-16T12:00:00Z")
    }
  ],
  "created_at": ISODate("2026-06-16T12:00:00Z"),
  "updated_at": ISODate("2026-06-16T14:30:00Z")
}
```

### **Redis — КЕШ**

```
// Full-text search results cache (5 min TTL)
cache:search:млеко:instagram => [
  {id: "507f...", name: "Млеко 1L", score: 0.95},
  {id: "507g...", name: "Млеко 2L", score: 0.85}
]

// Product detail cache (30 min TTL)
cache:product:507f => {
  name: "Млеко 1L",
  prices: {...},
  ...
}

// Scraper status (real-time)
scraper:status:instagram => {
  last_run: "2026-06-16T06:00:00Z",
  products_found: 45,
  success: true
}
```

---

## 🔌 API ENDPOINTS — SPECIFICATION

### **1. SEARCH ENDPOINT**

```http
GET /api/v1/search?q=млеко&source=instagram&limit=20

Response 200 OK:
{
  "total": 150,
  "returned": 20,
  "query": "млеко",
  "results": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "Млеко 1L",
      "description": "Свежо млеко",
      "image_url": "https://...",
      "source": "instagram",
      "current_prices": {
        "instagram": 1.49,
        "aroma": 1.39,
        "voli": 1.45
      },
      "min_price": 1.39,
      "max_price": 1.49,
      "cheapest_store": "aroma",
      "last_updated": "2026-06-16T10:30Z"
    }
  ]
}
```

### **2. PRICES BY TAB**

```http
GET /api/v1/prices/instagram?limit=50&offset=0

Response:
{
  "tab": "instagram",
  "total_products": 1250,
  "products": [
    {
      "id": "507f...",
      "name": "Млеко 1L",
      "prices": [...],
      "min_price": 1.39
    }
  ],
  "last_scrape": "2026-06-16T06:00Z"
}

---

GET /api/v1/prices/official?store=aroma&limit=50

Response:
{
  "tab": "official",
  "store": "aroma",
  "products": [...],
  "last_scrape": "2026-06-16T09:15Z"
}
```

### **3. WISHLIST ENDPOINTS**

```http
POST /api/v1/wishlist/add
{
  "product_id": "507f1f77bcf86cd799439011"
}

Response 201:
{
  "message": "Added to wishlist",
  "product": {id, name}
}

---

GET /api/v1/wishlist

Response 200:
{
  "count": 5,
  "products": [...]
}

---

DELETE /api/v1/wishlist/{product_id}

Response 204: No Content
```

### **4. SCRAPER STATUS**

```http
GET /api/v1/scrapers/status

Response:
{
  "instagram": {
    "enabled": true,
    "last_run": "2026-06-16T06:00Z",
    "status": "success",
    "products_found": 45,
    "errors": []
  },
  "aroma": {
    "enabled": true,
    "last_run": "2026-06-16T06:15Z",
    "status": "success",
    "products_found": 230,
    "errors": []
  },
  ...
}
```

---

## 🎨 FRONTEND STRUCTURE

### **Routes (Next.js 15 with i18n)**

```
/[lang]/                           ← Root layout
├── page.tsx                        ← Landing + main search
├── (app)/
│   ├── search/[query]
│   │   └── page.tsx               ← Search results
│   ├── product/[id]
│   │   └── page.tsx               ← Product detail + chart
│   ├── wishlist
│   │   └── page.tsx               ← Wishlist page
│   └── compare
│       └── page.tsx               ← Price comparison matrix

/api/
└── auth/...                        ← API routes (if needed)
```

### **Key Components**

| Component | Purpose | Props |
|-----------|---------|-------|
| **SearchBar** | Full-text search input | `onSearch(query)`, `source` |
| **PriceMatrix** | 2D grid: товари × магазини | `products[]`, `stores[]` |
| **TabSwitcher** | Instagram vs Official sites | `activeTab`, `onTabChange` |
| **LanguageSelector** | UKR/RUS/MNE | `currentLang`, `onLangChange` |
| **PriceChart** | Recharts timeseries | `product_id`, `days=30` |
| **WishlistButton** | Add/remove from wishlist | `productId`, `isInWishlist` |
| **PriceCard** | Single product card | `product`, `stores` |

### **Design Tokens**

```css
/* Colors */
--primary: #2D5016;      /* Dark Green */
--success: #4CAF50;      /* Light Green (cheapest) */
--accent: #D4AF37;       /* Gold */
--bg: #1A1A1A;          /* Dark background */
--text: #FFFFFF;        /* White text */

/* Typography */
--font: Inter, sans-serif;
--text-sm: 12px;
--text-base: 14px;
--text-lg: 16px;
--text-xl: 18px;
--text-2xl: 24px;

/* Spacing */
--gap-xs: 4px;
--gap-sm: 8px;
--gap-md: 16px;
--gap-lg: 24px;
--gap-xl: 32px;
```

---

## ⚙️ BACKEND SERVICES — ДЕТАЛЬ

### **1. InstagramSessionManager**
```python
class InstagramSessionManager:
    """
    Manages instagrapi session (login, caching, error handling)
    
    - Load cached session from disk
    - Create new session if expired
    - Handle 2FA, rate-limiting
    - Logout on exit
    """
    
    Methods:
    - load_or_create_session() -> bool
    - get_client() -> Client
    - refresh_if_needed() -> bool
```

### **2. InstagramPostScraper**
```python
class InstagramPostScraper:
    """
    Scrape posts from Instagram account
    
    - Get posts from past 48 hours
    - Download images
    - Extract caption + metadata
    """
    
    Methods:
    - scrape_recent_posts(username, hours_back=48) -> List[Media]
    - process_posts(posts) -> List[Dict]
```

### **3. PriceExtractor**
```python
class PriceExtractor:
    """
    Extract product names + prices from images using Tesseract OCR
    
    - OCR each image
    - Regex: find EUR prices
    - NLP: extract product name
    - Normalize: return structured data
    
    Accuracy: ~75-85% (OCR limitation)
    """
    
    Methods:
    - extract_from_image_url(url) -> Dict
    - extract_from_image(img) -> Dict
```

### **4. ProductService**
```python
class ProductService:
    """
    CRUD for products in MongoDB
    
    - Save new products
    - Deduplicate by MD5(name + store)
    - Update price history
    - Search by name
    """
    
    Methods:
    - save_product(data) -> str (product_id)
    - find_by_name(query, limit=20) -> List[Product]
    - update_price_history(product_id, store, price)
    - find_by_dedup_hash(hash) -> Product
```

### **5. SearchService**
```python
class SearchService:
    """
    Full-text search across products
    
    - MongoDB text index
    - Redis caching (5 min TTL)
    - Pagination support
    - Source filtering (instagram | official)
    """
    
    Methods:
    - search(query, source=None, limit=20) -> List[Product]
    - cache_key() -> str
    - invalidate_cache(query)
```

### **6. StoreScraper (Abstract)**
```python
class StoreScraper(ABC):
    """Base class for all store scrapers"""
    
    Methods (to implement):
    - scrape_products() -> List[{name, price, url}]
    - normalize_price(price_str) -> float
    - parse_html(html) -> List[Product]
    
    Concrete Implementations:
    - AromaScraper (aromamarketi.me)
    - VoliScraper (voli.me)
    - HDLScraper (digitalniletak.me/hd-lakovic)
    - IdeaScraper (idea.co.me)
```

### **7. ScraperOrchestrator**
```python
class ScraperOrchestrator:
    """
    Manages all scrapers, runs them parallel, logs status
    
    - APScheduler: run at 6 AM Kyiv daily
    - Parallel execution: 4 store scrapers
    - Error handling + retry logic
    - Update scraper_status in Redis
    """
    
    Methods:
    - run_all_scrapers()
    - run_instagram_scraper()
    - run_official_scrapers() (parallel)
    - get_status() -> Dict
```

---

## 🔄 DEPLOYMENT & OPERATIONS

### **Local Development**
```bash
# 1. Start Docker services
docker-compose up -d

# 2. Backend: auto-reload with --reload flag
# http://localhost:8001/docs

# 3. Frontend: auto-reload with npm run dev
# http://localhost:3003

# 4. View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### **Production (Future)**
```
- Deploy backend to Docker + supervisord (like hrd-minion)
- Frontend: Vercel (Next.js native)
- PostgreSQL: Cloud (AWS RDS, Hetzner)
- MongoDB: Cloud (MongoDB Atlas)
- Redis: Cloud (Redis Labs)
- Scrapers: Scheduled tasks (supervisord or K8s)
```

### **Monitoring & Alerts**
```
- Sentry: error tracking
- Structlog: JSON logging
- Redis: scraper_status real-time
- Email: daily summary (if configured)
```

---

## 🎯 ФАЗИ РЕАЛІЗАЦІЇ

### **Phase 0: Foundation ✅ (DONE)**
- ✅ Project structure
- ✅ Docker Compose
- ✅ CLAUDE.md + PLAN.md
- ✅ Port configuration

### **Phase 1: Instagram Parser POC** (2-3 тижні)
**Tasks:**
1. Data models (Pydantic + MongoDB)
2. Instagram session manager
3. Post scraper (instagrapi)
4. OCR + price extraction (Tesseract)
5. Product storage (MongoDB)
6. API endpoint `/api/v1/instagram/scrape`
7. Unit tests

**Deliverable:** Working endpoint that scrapes Instagram → MongoDB

### **Phase 2: Web Scrapers** (2-3 тижні)
**Tasks:**
1. StoreScraper base class
2. AromaScraper (aromamarketi.me)
3. VoliScraper (voli.me)
4. HDLScraper (digitalniletak.me)
5. IdeaScraper (idea.co.me)
6. Price normalization
7. PostgreSQL schema + Alembic migration
8. Scheduler integration (APScheduler)

**Deliverable:** Automated daily scraping of 4 stores

### **Phase 3: Frontend UI** (2-3 тижні)
**Tasks:**
1. Landing page layout
2. SearchBar component
3. PriceMatrix component (2D grid)
4. TabSwitcher (Instagram | Official)
5. LanguageSelector (UKR/RUS/MNE)
6. Product detail page
7. Wishlist page
8. Design system (Tailwind + Framer Motion)

**Deliverable:** Full frontend with all pages

### **Phase 4: Integration & Polish** (1-2 тижні)
**Tasks:**
1. Connect frontend → backend (API calls)
2. E2E testing
3. Performance optimization
4. Error handling + edge cases
5. Mobile responsiveness
6. Documentation

**Deliverable:** Production-ready platform

### **Phase 5: Deployment & Monitoring** (1 тиждень)
**Tasks:**
1. Docker image optimization
2. CI/CD pipeline (GitHub Actions)
3. Deploy to production server
4. Monitoring setup (Sentry)
5. Daily scraper monitoring

**Deliverable:** Live platform + monitoring

---

## 📋 CRITICAL DECISIONS & RATIONALES

| Decision | Alternative | Rationale |
|----------|-------------|-----------|
| **MongoDB (NoSQL)** | PostgreSQL only | Flexible schema, fast full-text search, easy scaling |
| **PostgreSQL (SQL)** | SQLite | Time-series data integrity, ACID guarantees, analytics |
| **Tesseract OCR** | Cloud Vision | Free, open-source, sufficient accuracy (~80%) |
| **Playwright** | Selenium | Modern, async support, better JS rendering |
| **APScheduler** | Celery + RabbitMQ | Simpler setup, native Python, sufficient for daily tasks |
| **Next.js** | React SPA | Server-side rendering, i18n built-in, SEO friendly |
| **Docker Compose** | K8s | Local dev simplicity, sufficient for MVP |
| **next-intl** | react-i18next | Built for Next.js 15, app router support |
| **Tailwind 4** | Styled Components | Performance, composable, rich design system |

---

## 🚨 KNOWN RISKS & MITIGATION

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Instagram blocks session (anti-bot) | 🔴 HIGH | Implement rate limiting (1-2s delays), 2FA handling, session rotation |
| OCR accuracy < 50% | 🔴 HIGH | Manual fallback UI, regex + keyword matching, crowd-sourced corrections |
| Store pages change structure | 🟡 MEDIUM | Monitor with alerts, quarterly review, version control for selectors |
| Rate limiting on web scrapers | 🟡 MEDIUM | Implement backoff strategy, IP rotation (proxies), randomized delays |
| Database quota exceeded | 🟡 MEDIUM | Implement retention policy (365 days), archive old data |
| API downstream (if added) | 🟢 LOW | Use circuit breaker pattern, graceful degradation |

---

## 📐 PERFORMANCE TARGETS

| Metric | Target | How |
|--------|--------|-----|
| Page Load | < 2s | Lazy loading, CDN, image optimization |
| Search Response | < 100ms | MongoDB index + Redis cache |
| API Response | < 500ms | Async all DB calls, proper indexing |
| OCR per image | < 3s | CPU-bound, acceptable for batch |
| Daily scrape | < 30 min | Parallel 4 store scrapers + Instagram |
| Database size | < 1GB | Retention policy + archiving |

---

## ✅ VALIDATION & QA

### **Unit Tests (80% coverage)**
- Models, services, extractors
- Edge cases: invalid images, malformed prices, duplicates

### **Integration Tests**
- End-to-end scraping workflow
- Database consistency checks
- API endpoint responses

### **Manual Testing**
- Search + filter functionality
- Wishlist operations
- Multi-language UI
- Mobile responsiveness

### **Performance Testing**
- Load test: 100 concurrent users
- Stress test: 10x normal traffic
- Database query performance

---

## 📚 TECHNOLOGY STACK — FINAL

```
FRONTEND:
  - Next.js 15
  - React 19
  - Tailwind CSS 4
  - Framer Motion (animations)
  - Recharts (charts)
  - next-intl (i18n)
  - Axios (HTTP client)
  - Zod (validation)

BACKEND:
  - FastAPI 0.104.1
  - Uvicorn (ASGI server)
  - Pydantic v2 (validation)
  - Motor 3.3.2 (async MongoDB)
  - SQLAlchemy 2.0 (ORM)
  - Alembic (migrations)
  - structlog (logging)
  - APScheduler (task scheduling)

SCRAPERS:
  - instagrapi 2.0 (Instagram)
  - Playwright 1.40 (JS rendering)
  - BeautifulSoup4 (HTML parsing)
  - pytesseract 0.3.10 (OCR)
  - Pillow 10.1 (image processing)

DATABASES:
  - MongoDB 7.0 (primary)
  - PostgreSQL 16 (history)
  - Redis 7.0 (cache)

INFRASTRUCTURE:
  - Docker & Docker Compose
  - supervisord (production, optional)
  - GitHub Actions (CI/CD)
  - Sentry (error tracking)

DEPLOYMENT:
  - Hetzner VPS (backend)
  - Vercel (frontend, optional)
```

---

## 🎬 NEXT STEPS

### **Immediately (This Session)**
1. ✅ Architecture finalized
2. → Start Phase 1: Data Models + Instagram Session Manager
3. → Write first tests
4. → Integrate with API endpoint

### **This Week**
- Complete Phase 1: Instagram scraper working
- Deploy to Docker container
- Test with real Instagram data

### **Next Week**
- Phase 2: Web scrapers for 4 stores
- Database migrations
- Scheduler setup

### **Following Week**
- Phase 3: Frontend UI
- Connect to API
- Multi-language support

---

**STATUS:** 🟢 READY FOR PHASE 1 IMPLEMENTATION

**Architecture Document Approved By:** Serhii Riabko (Architect)  
**Date:** 2026-06-16  
**Version:** 1.0