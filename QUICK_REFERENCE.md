# ⚡ QUICK REFERENCE — INSTA-DATA

**Швидкий доступ до всього важливого**

---

## 🎯 ЩО ЦЕ?

```
Платформа для порівняння цін харчування в Чорногорії
через Instagram + офіційні сайти 4 магазинів
= матриця товари × магазини × ціни
```

---

## 📍 ОСНОВНІ ПОРТТИ

| URL | Сервіс | Статус |
|-----|--------|--------|
| http://localhost:3003 | Frontend (Next.js) | 🐳 Docker |
| http://localhost:8001 | Backend API | 🐳 Docker |
| http://localhost:8001/docs | Swagger API docs | 🐳 Docker |
| http://localhost:27017 | MongoDB | 🐳 Docker |
| http://localhost:5432 | PostgreSQL | 🐳 Docker |
| http://localhost:6379 | Redis | 🐳 Docker |

---

## 🗂️ ФАЙЛИ & ЇХ ПРИЗНАЧЕННЯ

| Файл | Призначення |
|------|-----------|
| **ARCHITECTURE.md** | ⭐ ОСНОВНА архітектура (діаграми, schemas, API) |
| **PLAN.md** | Детальний план реалізації (Phase 1-5) |
| **PORTS_STATUS.md** | Порти, конфлікти, troubleshooting |
| **CLAUDE.md** | Інструкції для Claude Code |
| **docker-compose.yml** | Сервіси, ports, volumes, env |
| **.env.example** | Шаблон для .env (без паролів) |
| **.env** | (СТВОРИТИ) з реальними credentials |

---

## 🏗️ АРХІТЕКТУРА В ОДНІЙ КАРТИНЦІ

```
User Browser (3003)
       ↓ REST API (JSON)
   Frontend (Next.js)
       ↓
   Backend API (8001)
     ↙  ↓  ↘
MongoDB PostgreSQL Redis
(products) (history) (cache)
     ↓
 Scrapers (parallel):
 - Instagram + OCR
 - Aroma (Playwright)
 - Voli (BeautifulSoup)
 - HDL (Playwright)
 - IDEA (BeautifulSoup)
```

---

## 📊 DATABASE SCHEMAS (в двох рядках)

### **MongoDB — products collection**
```javascript
{
  _id: ObjectId,
  name: "Млеко 1L",
  prices: [{store: "aroma", price: 1.39, timestamp}],
  current_prices: {aroma: 1.39, voli: 1.45},
  min_price: 1.39,
  cheapest_store: "aroma"
}
```

### **PostgreSQL — price_history table**
```sql
| id | product_id | store | price | timestamp |
|----|------------|-------|-------|-----------|
| 1  | 507f...    | aroma | 1.39  | 2026-06-16|
```

---

## 🔌 API ENDPOINTS

| Метод | URL | Що робить |
|-------|-----|-----------|
| GET | `/api/v1/search?q=млеко&source=instagram` | Пошук товарів |
| GET | `/api/v1/prices/instagram` | Всі товари (Instagram) |
| GET | `/api/v1/prices/official?store=aroma` | Товари магазину |
| POST | `/api/v1/wishlist/add` | Додати в wishlist |
| GET | `/api/v1/wishlist` | Показати wishlist |
| GET | `/api/v1/scrapers/status` | Статус всіх скрейперів |

---

## 🐳 DOCKER КОМАНДИ

```powershell
# Стартувати всі сервіси
docker-compose up -d

# Зупинити
docker-compose down

# Переглянути логи
docker-compose logs -f backend
docker-compose logs -f frontend

# Перезапустити один сервіс
docker-compose restart backend

# Видалити всі дані (CAREFUL!)
docker-compose down -v
```

---

## 🎨 FRONTEND COMPONENTS

| Компонент | Де | Що робить |
|-----------|-----|----------|
| **SearchBar** | Landing | Пошук товарів |
| **TabSwitcher** | Landing | Instagram vs Official sites |
| **PriceMatrix** | Search results | 2D grid: товари × магазини |
| **PriceChart** | Product detail | Графік ціни за 30 днів |
| **WishlistButton** | Product card | Add/remove from wishlist |
| **LanguageSelector** | Header | UKR / RUS / MNE |

---

## ⚙️ BACKEND SERVICES

| Сервіс | Файл | Що робить |
|--------|------|-----------|
| **InstagramSessionManager** | `services/instagram_auth.py` | Логін + кеш сесії |
| **InstagramPostScraper** | `services/instagram_scraper.py` | Скрейп постів (48 год) |
| **PriceExtractor** | `services/price_extractor.py` | OCR + витяг цін |
| **ProductService** | `services/product_service.py` | CRUD MongoDB |
| **SearchService** | `services/search_service.py` | Full-text пошук |
| **StoreScraper** | `services/store_scrapers.py` | Base class для магазинів |
| **ScraperOrchestrator** | `services/scheduler.py` | Запуск скрейперів (6 AM) |

---

## 📅 ФАЗИ

| Фаза | Час | Що |
|------|-----|-----|
| **Phase 0** | ✅ Done | Foundation (structure, Docker, docs) |
| **Phase 1** | → Next | Instagram parser (instagrapi + OCR) |
| **Phase 2** | Week 2-3 | Web scrapers (4 магазини) |
| **Phase 3** | Week 3-4 | Frontend UI (Next.js) |
| **Phase 4** | Week 4-5 | Integration & testing |
| **Phase 5** | Week 5-6 | Deployment |

---

## 🔑 CREDENTIALS

### **Instagram (in .env)**
```
INSTAGRAM_EMAIL=Niobium_Runas
INSTAGRAM_PASSWORD=your_real_password
```
⚠️ НЕ комітити в git!

### **Databases (auto-generated for local dev)**
```
MONGODB_USER=admin
MONGODB_PASSWORD=testpass123
POSTGRES_USER=admin
POSTGRES_PASSWORD=testpass123
REDIS_PASSWORD=redis_testpass
```

### **Generate SECRET_KEY**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🚀 QUICK START

```powershell
# 1. Створити .env з real passwords + SECRET_KEY
cp .env.example .env
# [edit .env with real values]

# 2. Запустити Docker
docker-compose up -d
Start-Sleep -Seconds 30

# 3. Перевірити статус
docker-compose ps
# All services should be "Up" or "healthy"

# 4. Тест URLs
# Frontend: http://localhost:3003
# API Docs: http://localhost:8001/docs

# 5. Переглянути логи
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## ❌ COMMON ISSUES

| Проблема | Рішення |
|----------|---------|
| Port 3003 in use | `docker-compose.yml`: change to 3004:3000 |
| Port 8001 in use | Kill old Python: `Stop-Process -Name python` |
| Docker not running | Start Docker Desktop or: `docker ps` |
| Can't connect to MongoDB | Check: `docker-compose ps mongo` (healthy?) |
| Frontend won't load | Check logs: `docker-compose logs frontend` |

---

## 📖 읽АЙ БІЛЬШЕ

- **ARCHITECTURE.md** — Повна архітектура (MUST READ)
- **PLAN.md** — Детальні задачі на кожну фазу
- **PORTS_STATUS.md** — Порти, конфлікти, debugging
- **CLAUDE.md** — Інструкції для Claude Code

---

## 🎯 НАСТУПНІ КРОКИ (Right Now!)

1. Create `.env` with real credentials
2. Run `docker-compose up -d`
3. Read **ARCHITECTURE.md** completely
4. Start **Phase 1: Task 1.1** (Data Models)
5. Code + test + commit

---

**Last Updated:** 2026-06-16  
**Status:** 🟢 READY FOR PHASE 1