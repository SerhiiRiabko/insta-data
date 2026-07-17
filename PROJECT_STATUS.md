# 📊 Insta-Data Project Status

**Last Updated:** 2026-07-17
**Status:** 🟡 ACTIVE DEVELOPMENT — Phase 4.0-4.6 done, not yet deployed to production
**Version:** 1.0.0

> ⚠️ **This file is a point-in-time snapshot, updated occasionally.** For the
> current, actively-maintained project status, read **[PROJECT_MAP.md](PROJECT_MAP.md)**
> first — it's updated after every task/phase. Phase 4 detail (auth, shopping
> lists, admin panel, localization) lives in **[PHASE_4_PLAN.md](PHASE_4_PLAN.md)**.
> Day-to-day changelog with technical detail is in **[CLAUDE.md](CLAUDE.md)**.

---

## 🏆 Completion Summary

### Phase 0-3: Foundation, scrapers POC, frontend integration ✅ COMPLETE (2026-06-16 → 2026-07-02)
Docker Compose scaffold, Instagram OCR-based scraper POC, mock store scrapers
(Aroma/Voli/HDL/IDEA), first working price-matrix frontend. Superseded by
Phase 4 below — the mock scrapers described in the original Phase 1-3 docs
(`PHASE_1_COMPLETION.md`, `PHASE_2_COMPLETION.md`, `PHASE_3_PLAN.md`) were
removed once the real cijene.me-based scraper (Phase 4) replaced them.

### Phase 4.0-4.6: Accounts, shopping lists, admin panel, localization ✅ COMPLETE (2026-07-13 → 2026-07-17)
Full detail in [PHASE_4_PLAN.md](PHASE_4_PLAN.md); summary:
- **4.0** — quick UI fixes, 2 new locale stubs (srb/bos)
- **4.1** — guest shopping lists (no login), shareable link, 30-day TTL
- **4.2** — accounts (email+password AND magic-link), saved/multiple lists, tier limits
- **4.3** — stores admin (CRUD, replaces hardcoded mock store list)
- **4.4** — admin panel (auth-gated, tiers CMS, user management)
- **4.5** — scraper agents in admin (manage/run the real cijene.me scraper from the UI)
- **4.6** — localization unification (6 locales: ukr/rus/mne/srb/bos/eng, one
  `Lang` type, one URL-locale source of truth), product name translation
  (`name_i18n` + free dictionary translator, see 2026-07-17 follow-up below),
  language-aware search
- **Real scraping replaced mocks**: the current live data source is
  `cijene_scraper.py` (cijene.me aggregator, covers Aroma/Voli/HDL/IDEA in one
  scrape) + an Instagram mock, orchestrated by
  `app/services/scrapers/orchestrator.py`. The Phase 1-3 mock scrapers
  (`aroma_mock_scraper.py`, `hdl_mock_scraper.py`, `idea_mock_scraper.py`,
  `voli_mock_scraper.py`) and the Instagram OCR pipeline (`instagrapi`,
  Tesseract) referenced throughout this doc's older sections below are no
  longer part of the live pipeline.

### 2026-07-17 follow-up: real product-name translations + 2 search bugfixes
- `grocery_dictionary.py` — free, deterministic word-level translator (no API
  key needed), backfilled `name_i18n` for 281/287 (98%) real products.
- Fixed two bugs that silently broke `/search/products` for any query (missing
  MongoDB text index; a response model requiring a field that's always `None`
  on real data).
- Fixed the landing-page hero search bar (was pure unwired UI) and the
  "create shopping list" search (was re-running a full ~10-15s live scrape on
  every modal open instead of filtering already-loaded data).

Full detail: `PROJECT_MAP.md` → "Bugfix (2026-07-17, 2 частини)" and
`CLAUDE.md` → changelog entries 21-22.

### Not yet done
- [ ] Production deployment (this app has never been deployed — see the
  ⚠️ note under Deployment below about `DEPLOYMENT.md`'s target server)
- [ ] Automated scheduled scraping is in place (weekly Monday 07:00 Kyiv via
  APScheduler) but not yet verified running unattended in production
- [ ] Category header labels (Овочі/Молочка/...) are hardcoded Ukrainian
  regardless of UI locale — not yet localized (separate, smaller known gap)

---

## 📈 Statistics

| Metric | Count |
|--------|-------|
| **API Endpoints** | 40+ (products, search, auth, lists, admin, stores, scraper-agents) |
| **React Components** | 15+ |
| **Supported Languages** | 6 (ukr/rus/mne/srb/bos/eng) |
| **Live Data Source** | cijene.me (real scrape, aggregates Aroma/Voli/HDL/IDEA) + Instagram mock |
| **Total Products (current DB)** | 287 real scraped products |
| **Products with translated name (`name_i18n`)** | 281/287 (98%) — see 2026-07-17 follow-up |

---

## 🏗️ Architecture Overview

### Backend Stack
- **Framework:** FastAPI (async)
- **Database:** MongoDB (primary — native Windows service for local dev, not
  Docker; PostgreSQL/Redis exist in `docker-compose.yml` but aren't required
  for the current feature set)
- **Auth:** Session cookie (HttpOnly JWT), email+password AND magic-link
- **Scraping:** `cijene_scraper.py` (real, aggregator site) + Instagram mock,
  via `app/services/scrapers/orchestrator.py`
- **Translation:** `grocery_dictionary.py` (free, deterministic) with an
  optional Groq AI fallback (`translation_service.py`)
- **Scheduling:** APScheduler (weekly Monday 07:00 Kyiv)

### Frontend Stack
- **Framework:** Next.js 15 + React 19
- **Styling:** Tailwind CSS 4 (v3-style config via `@config` compat layer —
  see the documented `max-w-*`/spacing-scale collision gotcha in
  `PROJECT_MAP.md`)
- **i18n:** next-intl, 6 locales, URL locale segment is the single source of
  truth for the `Lang` type (`lib/productMatrix.ts`)
- **HTTP:** Axios

### Local Development (current, not Docker)
- **Backend:** `venv/Scripts/python.exe -m uvicorn app.main:app --port 8001`
- **Frontend:** `npm run dev -- -p 3001`
- **MongoDB:** native Windows service on `localhost:27017` (see `.env` comment)
- Ports **3001**/**8001** are the real, currently-used ports — not 3003/8001
  as described in the Docker-based sections further down this document.

---

## 🚀 Deployment Status

**Not yet deployed to production.** This has been local-dev-only throughout
Phase 4. `DEPLOYMENT.md` describes a planned Hetzner VPS setup —
⚠️ **verify its target server before using it**: it currently points at
`root@138.199.204.107`, which the top-level workspace `CLAUDE.md` (one level
up, for the unrelated `hrd-minion` project) marks **"ONLY PRODUCTION"** for a
different bot. This looks like it may be a copy-paste artifact rather than an
intentional shared-infrastructure decision — confirm before deploying
anything there.

### ⚠️ Before Production
- [ ] Resolve the `DEPLOYMENT.md` target-server question above
- [ ] Update `.env` with real production secrets (JWT secret, Resend API key
  already configured/shared per an earlier explicit user decision — see
  `CLAUDE.md` for which keys are safe to reuse across projects and which
  aren't)
- [ ] Configure domain/SSL
- [ ] Set up database backups
- [ ] Configure monitoring + logging
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Review security settings

---

## 📋 File Structure

```
insta-data/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── instagram.py
│   │   │   ├── scrapers.py
│   │   │   └── search.py
│   │   ├── services/
│   │   │   ├── instagram_auth.py
│   │   │   ├── instagram_scraper.py
│   │   │   ├── price_extractor.py
│   │   │   ├── product_service.py
│   │   │   ├── store_scrapers.py (5 scrapers)
│   │   │   ├── search_service.py
│   │   │   └── orchestrator.py
│   │   ├── models/
│   │   │   ├── product.py
│   │   │   └── schemas.py
│   │   ├── database/
│   │   │   ├── models.py (SQLAlchemy)
│   │   │   ├── mongodb.py
│   │   │   └── postgres.py
│   │   └── core/
│   │       ├── config.py
│   │       ├── logger.py
│   │       └── exceptions.py
│   ├── tests/unit/ (5 test files, 65+ cases)
│   ├── alembic/ (migrations)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/[lang]/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/ (6 components)
│   │   ├── lib/
│   │   │   └── api.ts
│   │   ├── locales/ (3 languages)
│   │   ├── middleware.ts
│   │   └── i18n.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── package.json
│   └── Dockerfile.dev
│
├── docker-compose.yml
├── .env.example
├── ARCHITECTURE.md (700+ lines)
├── PLAN.md (500+ lines)
├── QUICK_REFERENCE.md
├── PORTS_STATUS.md
├── PROJECT_STATUS.md (this file)
└── README.md
```

---

## 🔄 Data Flow

### 1. Instagram Scraping
```
InstagramSessionManager.load_or_create_session()
  ↓
InstagramPostScraper.scrape_recent_posts(username, hours_back=48)
  ↓
InstagramPostScraper.process_posts() → Extract images
  ↓
PriceExtractor.extract_from_image() → Tesseract OCR
  ↓
ProductService.save_product() → MongoDB (dedup by hash)
```

### 2. Official Site Scraping
```
ScraperOrchestrator.run_all_scrapers() [parallel]
  ├─ AromaScraper.scrape_products() → Playwright
  ├─ VoliScraper.scrape_products() → Playwright
  ├─ HDLScraper.scrape_products() → BeautifulSoup
  └─ IDEAScraper.scrape_products() → BeautifulSoup
  ↓
StoreScraper.normalize_product_data()
  ↓
ProductService.save_product() → MongoDB + PostgreSQL history
```

### 3. Search Flow
```
Frontend: SearchBar.handleSearch("Млеко")
  ↓
API: GET /api/v1/search/products?q=Млеко
  ↓
SearchService.search() → Check Redis cache
  ↓
MongoDB: Full-text search ($text operator)
  ↓
Cache result in Redis (5 min TTL)
  ↓
Return to Frontend → PriceMatrix renders ProductCards
```

---

## 📊 Performance Targets

| Metric | Target | Current Status |
|--------|--------|-----------------|
| Page Load | < 2s | ✅ Ready |
| Search Response | < 100ms | ✅ Ready |
| API Response | < 500ms | ✅ Ready |
| Instagram Scrape | < 5min | ✅ Ready |
| Web Scrape (4 sites parallel) | < 10min | ✅ Ready |
| Daily Full Scan | < 30min | ✅ Ready |
| OCR per image | < 3s | ✅ Ready |

---

## 🔐 Security Checklist

- [x] API key validation
- [x] Rate limiting ready (APScheduler backoff)
- [x] CORS configured
- [x] Environment secrets in .env (not in code)
- [x] Password hashing (for future user accounts)
- [x] Input validation (Pydantic + Zod)
- [ ] HTTPS (configure in production)
- [ ] JWT tokens (optional for future)
- [ ] Database encryption (optional)
- [ ] API rate limiting middleware (optional)

---

## 🧪 Testing Summary

### Backend Tests (65+ cases)
- Unit tests for all services
- Mock database + API calls
- Coverage target: 80%+
- Run: `pytest tests/unit/`

### Frontend (Optional)
- Component tests with React Testing Library
- E2E tests with Playwright
- Run: `npm test`

---

## 📚 Documentation Files

1. **ARCHITECTURE.md** — Full system design (700+ lines)
   - System diagram
   - Data flows
   - API specifications
   - Database schemas
   - Service descriptions

2. **PLAN.md** — Implementation roadmap
   - Phase 0-5 detailed tasks
   - Technology decisions
   - Timeline

3. **QUICK_REFERENCE.md** — Quick lookup
   - Port mapping
   - API endpoints summary
   - Docker commands
   - Common issues

4. **PORTS_STATUS.md** — Port allocation & troubleshooting
   - Port conflicts
   - Docker network
   - Environment variables

5. **PROJECT_STATUS.md** (this file)
   - Completion status
   - Statistics
   - File structure
   - Performance targets

6. **README.md** (in each service)
   - Setup instructions
   - Development guide
   - Deployment guide

---

## 🎯 Next Steps

`LOCAL_SETUP.md` and `DEPLOYMENT.md` already exist (items 1-2 of the original
list here are done) — see the ⚠️ deployment-target note above before using
`DEPLOYMENT.md`. Remaining open items:

1. **Production Deployment** — resolve the target-server question, then
   actually deploy (never done yet).
2. **Monitoring & Logging**
   - Add health check endpoints
   - Configure logging (structlog + JSON format)
   - Add metrics collection
3. **CI/CD Pipeline** (Optional)
   - GitHub Actions workflow
   - Automated testing
4. **Category header localization** — `Овочі`/`Молочка`/etc. are hardcoded
   Ukrainian regardless of UI locale (`category_map.py` on the backend);
   noted in `PROJECT_MAP.md`, not yet scheduled.

---

## 🚀 Quick Start (Local Development)

**Current, actually-used setup** (native, not Docker — see `LOCAL_SETUP.md`
for the full guide):

```bash
# 1. Backend (Terminal 1)
cd backend
venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8001

# 2. Frontend (Terminal 2)
cd frontend
npm run dev -- -p 3001

# 3. Access
# Frontend: http://localhost:3001/ukr  (or /rus /mne /srb /bos /eng)
# Backend:  http://localhost:8001
# API Docs: http://localhost:8001/docs
# MongoDB:  native Windows service, localhost:27017 (not Docker)
```

### Docker Compose (original design, not the current dev workflow)

The sections below (file structure, data flow, Docker services) describe the
original Phase 0-3 design and may not exactly match today's file layout — see
`PROJECT_MAP.md` for what's actually in the codebase now.

```bash
# 1. Navigate to project
cd insta-data

# 2. Copy .env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 3. Update frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# 4. Start all services
docker-compose up -d

# 5. Wait 30 seconds
sleep 30

# 6. Access
# Frontend: http://localhost:3003
# Backend: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

---

## 📞 Support & Resources

- **GitHub Repo:** https://github.com/SerhiiRiabko/insta-data
- **Issues:** Report bugs and feature requests
- **Discussions:** Q&A and ideas
- **Wiki:** Detailed documentation

---

## 📄 License

MIT License - See LICENSE file

---

**Project Status: 🟡 ACTIVE DEVELOPMENT — feature-complete for Phase 4.0-4.6, never deployed to production**

Real cijene.me scraping | 6 locales | Accounts + shopping lists + admin panel | Not yet deployed

Next: resolve the `DEPLOYMENT.md` target-server question, then actually deploy. See [PROJECT_MAP.md](PROJECT_MAP.md) for current status.