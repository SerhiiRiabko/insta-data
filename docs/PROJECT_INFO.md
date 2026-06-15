# Insta-data — Project Info

**Дата старту:** 2026-06-15  
**Статус:** Phase 0 — Ініціалізація ✅  
**Власник:** Serhii Riabko  
**Мета:** Автоматичний моніторинг цін товарів через Instagram і офіційні сайти магазинів Чорногорії з аналізом динаміки та порівнянням.

**Статус Фаз:**
- ✅ **Phase 0: Ініціалізація & Інфра** (COMPLETED 2026-06-15)
- ⏳ **Phase 1: Instagram Parser POC** (NEXT)
- ⏳ **Phase 2: Web Scrapers** (4 магазини)
- ⏳ **Phase 3: Backend API** (FastAPI endpoints)
- ⏳ **Phase 4: Frontend** (Next.js UI + design)
- ⏳ **Phase 5: Integration & Testing**

---

## 📋 Вимоги & Рішення

### Функціональність
| # | Вимога | Рішення | Статус |
|----|--------|---------|--------|
| 1 | Парсинг Instagram для постів з товарами | Selenium/Insta-API + кеш | ⏳ |
| 2 | Web scraping 4 магазинів (Aroma, Voli, HDL, IDEA) | BeautifulSoup/Playwright | ⏳ |
| 3 | Порівняння цін товарів між магазинами | NoSQL index (product_name + store) | ⏳ |
| 4 | Матриця товари × магазини × ціни | Frontend React grid + filtering | ⏳ |
| 5 | Мультимовність (Чорногорська, Українська, Російська) | i18n tabs | ⏳ |
| 6 | Два табу: "Соціальні мережі" + "Офіційні сайти" | Окремі endpoint'и + UI tabs | ⏳ |
| 7 | Пошук товарів на кожній табі | Full-text search NoSQL | ⏳ |
| 8 | Список продуктів для задання (wishlist) | User list → backend query | ⏳ |
| 9 | Адаптивність (iPhone + Samsung) | Responsive design mobile-first | ⏳ |
| 10 | Красивий UI (зелений + золото + анімація) | Tailwind CSS + Framer Motion | ⏳ |
| 11 | История цін для графіків | SQL (PostgreSQL) + timeseries | ⏳ |
| 12 | Smart price tracking (останні 3 снимки + поточна) | NoSQL indexing strategy | ⏳ |
| 13 | Можливість розширення на бота (свій, не Бот-Фазер) | REST API структура | ⏳ |

---

## 🏛️ Архітектурні Рішення

### 1. **Мікросервісна архітектура**
```
┌─────────────────────────────────────────┐
│         Frontend (Next.js 15)           │
│  Зелений + золото + анімація            │
└────────────────────┬────────────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼─────┐    ┌────▼─────┐    ┌───▼──────┐
│  Auth    │    │  Search  │    │ Wishlist │
│  Service │    │  Service │    │ Service  │
└────┬─────┘    └────┬─────┘    └───┬──────┘
     │               │               │
┌────▼────────────────▼───────────────▼────┐
│         API Gateway (FastAPI)            │
└────┬────────────────┬────────────────────┘
     │                │
  ┌──▼──┐      ┌──────▼──────┐
  │NoSQL│      │  SQL        │
  │(Main│      │  (History)  │
  │ DB) │      └─────────────┘
  └──┬──┘
     │
  ┌──▼─────────────────────────┐
  │ Scrapers (Docker services) │
  │ - Instagram parser         │
  │ - Aroma, Voli, HDL, IDEA   │
  └────────────────────────────┘
```

### 2. **БД Стратегія**
- **NoSQL (MongoDB/DynamoDB)**: Основна БД для товарів, цін, пошуку
  - Collection: `products` (product_name, stores, current_prices, last_3_updates)
  - Collection: `scraped_data` (raw Instagram posts + web scrapes)
  - Collection: `wishlist` (user → list of products)
  
- **SQL (PostgreSQL)**: История цін для аналітики
  - Table: `price_history` (product_id, store_id, price, timestamp)
  - Table: `users` (if auth needed later)

### 3. **Цінова логіка** (ВАЖЛИВО)
- **Як часто оновлюються ціни?** → Перевіримо при першому скрейпі
- **Стратегія зберігання:**
  ```
  products.prices = {
    current: { aroma: 1.39, voli: 0.85, hdl: 0.85, idea: 1.49 },
    history: [
      { timestamp: 2026-06-15_14:00, prices: {...} },
      { timestamp: 2026-06-15_10:00, prices: {...} },
      { timestamp: 2026-06-14_14:00, prices: {...} }
    ]
  }
  ```
  → Щоб мати поточну + 3 попередніх для аналізу
- **SQL для графіків:** `price_history` окремо для timeseries

### 4. **Instagram Парсинг**
- Потрібні credentials від користувача (email + password)
- Скрейпимо пости за останні 2 дні
- Витягуємо: `product_name`, `stores`, `prices` (OCR + regex)
- Нормалізуємо картинки (одна величина, формат JPEG)

### 5. **Мультимовність & Табу**
- **Три мови:** UKR, RUS, MNE (Чорногорська)
- **Два табу:** 
  - "📱 Соціальні мережі" (Instagram data)
  - "🏪 Офіційні сайти" (web scrapes)
- Окремі endpoint'и: `/api/v1/prices/instagram` + `/api/v1/prices/official`

---

## 💬 Записи Розмов

### Сесія 2 (2026-06-15) — Phase 0 Ініціалізація ✅
**Тема:** Структура проекту, конфіги, Docker setup

**Що було зроблено:**
1. ✅ Створена структура папок (як архітектор, по прикладу MonteLand + hrd-minion)
2. ✅ `.env.example` з правильно схованими паролями (без git commit)
3. ✅ `.gitignore` з усіма sensitive файлами
4. ✅ `CLAUDE.md` з інструкціями для проекту
5. ✅ `docker-compose.yml` (MongoDB, PostgreSQL, Redis, Backend, Frontend, Nginx)
6. ✅ Backend skeleton:
   - FastAPI app с lifespan events
   - Pydantic config management (.env)
   - structlog logging setup
   - MongoDB + PostgreSQL connection modules
   - API v1 router skeleton
7. ✅ Frontend skeleton:
   - Next.js 15 package.json
   - next-intl для i18n
   - Tailwind 4, Framer Motion, Recharts
   - Dockerfile for dev

**Credentials:** Instagram `Niobium_Runas` (пароль в .env, не в git) ✅

---

### Сесія 1 (2026-06-15)
**Тема:** Уточнення вимог, архітектура, документація

**Ключові моменти:**
1. **Структура:** MonteLand-подібна (Next.js + FastAPI) + красивий UI (зелений, золото)
2. **Архітектура:** Мікросервісна послідовно
3. **БД:** NoSQL (основна) + SQL (история цін)
4. **Цінова логіка:** Останні 3 + поточна, smart update tracking
5. **Instagram:** Користувач надасть credentials
6. **Мови:** 3 (UKR, RUS, MNE) в табах
7. **Табу:** Соціальні мережі + Офіційні сайти окремо
8. **Пошук & wishlist:** На обох табах
9. **Розширення:** REST API для майбутнього бота

---

## 📌 Прийняті Рішення

| Рішення | Обґрунтування |
|---------|---------------|
| Next.js 15 + FastAPI | Потужна стек, як MonteLand, proven |
| MongoDB (NoSQL) | Швидкість, гнучкість структури, full-text search |
| PostgreSQL для history | Timeseries, аналітика, гарантії ACID |
| Мікросервісна архітектура | Масштабованість, розділення відповідальності |
| Docker контейнери для scrapers | Ізоляція, простий маніпулювання, версіонування |
| Tailwind + Framer Motion | Красивий дизайн, анімація, responsive |
| REST API (не GraphQL) | Простота, webhook'и для боту, кешування |

---

## 🗂️ Структура папок (TBD)
```
insta-data/
├── frontend/              ← Next.js 15
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── i18n/          ← UKR, RUS, MNE
│   └── package.json
├── backend/               ← FastAPI
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   └── core/
│   ├── alembic/
│   └── requirements.txt
├── scrapers/              ← Docker services
│   ├── instagram_parser/
│   ├── aroma_scraper/
│   ├── voli_scraper/
│   ├── hdl_scraper/
│   └── idea_scraper/
├── docs/                  ← Документація
│   ├── PROJECT_INFO.md
│   ├── BUSINESS_LOGIC.md
│   ├── TECHNOLOGY.md
│   └── ARCHITECTURE.md
├── docker-compose.yml
└── .env
```

---

## 🚀 Next Steps
1. ✅ Створити документи (Project-info, Business-logic, Technology)
2. ⏳ Деталізувати архітектуру з `/make-plan`
3. ⏳ Ініціалізувати проект структуру
4. ⏳ Налаштувати MongoDB + PostgreSQL локально
5. ⏳ Розпочати з Instagram парсера
6. ⏳ Web scrapers для 4 магазинів
7. ⏳ Frontend (матриця, пошук, wishlist)
8. ⏳ Деплой на сервер