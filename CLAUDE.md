# CLAUDE.md — Insta-data Project Instructions

Цей файл надає контекст Claude Code при роботі з цим проектом.

---

## 📋 Проект Insta-data

**Мета:** Автоматичний моніторинг цін товарів харчування через Instagram + офіційні сайти магазинів Чорногорії.

**Статус:** Phase 0 — Ініціалізація (2026-06-15)

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

# 5. Run backend
python main.py

# 6. Frontend setup (в новому terminal)
cd frontend
npm install
npm run dev

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
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

## 📚 Документація (Читай ЦЕ при старті!)

Коли повертаєшся до проекту:

1. **Читай ПЕРШИМ:** `docs/PROJECT_INFO.md`
   - Статус проекту
   - Прийняті рішення
   - Наступні кроки

2. **Потім:** `docs/BUSINESS_LOGIC.md`
   - User Stories
   - Workflow'и
   - Data models

3. **Потім:** `docs/TECHNOLOGY.md`
   - Tech stack
   - Архітектура
   - Рішення чому

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

## 📞 Next Steps

- [ ] Phase 0: Ініціалізація (CURRENT)
  - [x] Структура папок
  - [x] .env.example
  - [x] .gitignore
  - [x] CLAUDE.md
  - [ ] docker-compose.yml
  - [ ] Backend skeleton
  - [ ] Frontend skeleton
  
- [ ] Phase 1: Instagram Parser POC
  - [ ] instagrapi login
  - [ ] Post scraping
  - [ ] OCR + regex
  - [ ] Image normalization
  - [ ] Unit tests

- [ ] Phase 2: Web Scrapers (4 магазини)
- [ ] Phase 3: Backend API
- [ ] Phase 4: Frontend UI
- [ ] Phase 5: Integration & Testing

---

**Остання оновлена:** 2026-06-15
**Автор:** Serhii Riabko