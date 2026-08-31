# 📊 Shop Price Online Project Status

**Last Updated:** 2026-08-31
**Status:** 🟢 DEPLOYED — http://138.199.204.107:3010 (ME + UA, multi-country)
**Version:** 1.1.0 (renamed from Insta-Data / Monte-Shop-Price on 2026-08-29)

> ⚠️ **This file is a point-in-time snapshot, updated occasionally.** For the
> current, actively-maintained day-by-day changelog with full technical
> detail, read **[CLAUDE.md](CLAUDE.md)** first (entries 24-38 cover
> everything below, including everything in the "Phase 5" section right
> below that's now out of date - see the correction note under it). Phase 4
> detail (auth, shopping lists, admin panel, localization) lives in
> **[PHASE_4_PLAN.md](PHASE_4_PLAN.md)**.

---

## 🏆 Phase 6: Deep UA coverage, real АТБ automation, Коло data (2026-08-30 → 2026-08-31)

Everything below **supersedes specific claims in "Phase 5" further down**
(kept as-is for its own historical accuracy, not edited) - see CLAUDE.md
#30-38 for full detail on each:

- **АТБ is now a real, registered, automated scraper**, not "written but
  disabled". Every Playwright approach (plain, stealth JS patch,
  `patchright`) still gets blocked by Cloudflare, but `undetected-
  chromedriver` in headed mode passes reliably - runs against a permanent
  virtual display (`Xvfb :99`) since the VPS has no real one. #32-33.
- **Сільпо can get rate-limited by the site itself** after heavy scraping
  and occasionally needs a manual data bridge
  (`scripts/merge_silpo_manual.py`) - not a code bug, confirmed by the
  same category pages loading fine from a different IP. #32, #36.
- **Коло has a tiny (7-product) manually-collected price set**
  (`scripts/merge_kolo_manual.py`) sourced from a third-party site's
  scanned promo images (not extractable text, not automatable without
  OCR) - still no real online catalog anywhere, confirmed on 4 separate
  sources across the session. #38.
- **6 new product categories per store**: Алкоголь, Дитячі товари,
  Особиста гігієна, Побутова хімія, Зоотовари, Яйця (split out of
  Молочка) - previously every scraper only covered food. #33-35.
- **Matching got a lot more aggressive** (by explicit user request, a
  deliberate precision-for-coverage trade-off): Овочі/Фрукти/М'ясо і риба
  match on core name only, ignoring variety/brand; produce singular/
  plural normalized (огірок/огірки etc); drinks lost their filler words
  ("напій"/"газований"/...) so e.g. Pepsi matches across stores - except
  carbonation words are kept for anything with "вод" in the name, so
  water's negazovana/gazovana stays correctly distinct. #31, #35, #37.
- **`/matrix-cached` was silently truncating UA at 2000 products** (~16%
  of the real 2371-item catalog) - raised to 10000. #36.
- **UA never had an automatic weekly refresh at all** (the scheduled job
  was hardcoded ME-only) - fixed and moved to Mon 03:00 (ME) / 03:15 (UA)
  Europe/Kyiv. #36.
- **End-of-session state**: ~3100+ UA products, 150+ cross-store
  comparisons, 6 stores with at least some data (Коло's being nominal).

---

## 🏆 Phase 5: Multi-country (ME + UA) — ✅ COMPLETE (2026-08-29 → 2026-08-30)

> ⚠️ Historical - written 2026-08-30, several claims below (АТБ "not
> registered", Коло "can't be scraped, period", match counts) are now out
> of date. See "Phase 6" above for what actually changed. Left unedited
> below as an accurate record of what was true at the time.

The project (and its folder) was renamed **Shop Price Online**. It's no
longer Montenegro-only:

- **Country selector** (ME/UA) on the site header and in the admin store
  form - `GET /countries`, `stores.country` field, all matrix endpoints take
  a `country` param. Details: CLAUDE.md #25.
- **4 real, live Ukrainian scrapers**: Novus, Varus, Сільпо, Фора - all
  Playwright-driven (plain HTTP gets blocked, likely TLS fingerprinting).
  АТБ is written (`atb_scraper.py`) but **not registered** - it sits behind
  a genuine Cloudflare managed challenge that beat every approach tried
  (`navigator.webdriver` patch, headed mode, real Chrome via
  `channel="chrome"`). Коло has no online price catalog at all - can't be
  scraped, period. Details: CLAUDE.md #26-27.
- **Cross-store product matching was mostly broken, then fixed twice**:
  (1) category was part of the matching key, and Novus's own "Фрукти та
  овочі" combined category never matched Сільпо/Varus/Фора's split
  categories - fixed by splitting it client-side by Ukrainian keyword;
  (2) the unit-stripping regex was ASCII-only, so Cyrillic "кг"/"г"/"л"
  suffixes were never stripped, defeating exact-name matching even for
  identical products; (3) different stores use different Ukrainian words
  for the same item (томат vs помідор, лосось vs сьомга, confirmed by
  manually browsing all 5 stores' category pages) - added a synonym
  normalization pass. Multi-store matches went from ~5 to 30-44 out of
  ~750-850 products. Details: CLAUDE.md #28-29.
- **Promo highlighting**: discounted items get a distinct green highlight
  independent of whether they're also the cheapest, using `old_price`/
  `is_promo` fields added to the scraper pipeline.
- **UX**: rows sorted so genuine multi-store comparisons float to the top
  of each category instead of being buried among single-store listings
  (still the majority - independent retailers mostly carry different
  specific brands/SKUs, not a shared catalog, unlike Montenegro's
  cijene.me aggregator).
- **Production outage found and fixed along the way**: an orphaned
  `next-server` process (unrelated to this phase, pre-existing) was
  blocking the frontend's port; root-caused to a missing
  `stopasgroup`/`killasgroup` in the supervisor config and fixed
  permanently. Also fixed a broken `cloudflare-warp` apt source on the VPS
  that blocked installing Playwright's system dependencies.

## 🏆 Completion Summary (Montenegro-only phases, historical)

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

**Deployed (2026-07-17).** Live at http://138.199.204.107:3010 (admin:
http://138.199.204.107:3010/ukr/admin), backend at
http://138.199.204.107:8010. Full deployment detail, memory-safety measures,
and known follow-ups: `CLAUDE.md` changelog entry 23.

The target-server question flagged in the previous version of this section
(same Hetzner VPS as `hrd-minion`) was raised with the user and **explicitly
confirmed** — shared infrastructure, accepted knowingly. `kartiq-backend` and
`kartiq-frontend` were stopped (not removed - `supervisorctl start
kartiq-backend` / `pm2 start kartiq-frontend` to bring back) to free memory
on an already tight box (232Mi free, 0 swap before this deploy - a 2GB
swapfile was added as a safety net, and MongoDB's cache was capped to
avoid it happening again).

### ⚠️ Still before this is a "real" production setup
- [ ] Domain + SSL/HTTPS (currently plain HTTP on raw ports; the session
  cookie is deliberately non-`Secure` to work over HTTP - **must** be
  revisited once a domain exists, see `CLAUDE.md` entry 23)
- [ ] Resend API key (magic-link email doesn't actually send yet - the
  bootstrapped admin account uses email+password instead)
- [ ] Set up database backups (MongoDB has zero backup/snapshot strategy)
- [ ] Configure monitoring + logging beyond supervisord's stdout/stderr files
- [ ] Set up CI/CD pipeline (GitHub Actions) - deploys are still manual SSH
- [ ] Decide whether to restore `kartiq-backend`/`kartiq-frontend` or leave
  them off; the server is memory-constrained enough that running everything
  at once isn't comfortably safe

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

**Project Status: 🟢 DEPLOYED — http://138.199.204.107:3010 (feature-complete for Phase 4.0-4.6)**

Real cijene.me scraping | 6 locales | Accounts + shopping lists + admin panel | Live, no domain/SSL yet

Next: domain + HTTPS (and flip the session cookie back to `Secure` once there's one). See [PROJECT_MAP.md](PROJECT_MAP.md) for current status.