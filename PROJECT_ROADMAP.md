# Insta-data Project Roadmap

**Project:** Monte-Shop-Price (Real-time Grocery Price Comparison)  
**Start Date:** 2026-06-15  
**Target Launch:** 2026-07-31  
**Duration:** 6-7 weeks (Phase 0-5)

---

## 📈 PROJECT PHASES

### ✅ Phase 0: Project Setup (2026-06-15 to 2026-06-30)

**Status:** COMPLETED ✅

**Deliverables:**
- ✅ Project structure created
- ✅ Tech stack selected (Next.js 15, FastAPI, MongoDB, PostgreSQL, Redis)
- ✅ Docker Compose configured
- ✅ Git repository initialized
- ✅ Documentation created (CLAUDE.md, PORTS.md, etc.)
- ✅ Environment setup (.env.example, .gitignore)

**Commits:** 8518292 (project init)

**Time Spent:** ~2 weeks

---

### ✅ Phase 1: Landing Page Design + Frontend-Backend Integration (2026-07-01 to 2026-07-02)

**Status:** COMPLETED ✅

**Frontend Deliverables:**
- ✅ Landing page Variant A implemented
  - Photo-forward hero (Kotor Bay)
  - Floating price matrix table
  - Responsive table layout (no horizontal scroll)
  - i18n support (RU/UK/EN)
  - Modal dialogs scaffolded (Products, Stores, About)
  
**Backend Deliverables:**
- ✅ Products API endpoints
  - `GET /api/v1/products/matrix` (price matrix for landing)
  - `GET /api/v1/products/list` (product list)
  - Mock data support (8 products × 4 stores)
  - Error fallback to mock data

**Integration Deliverables:**
- ✅ API client (frontend/src/lib/api.ts)
- ✅ Component data fetching (useEffect + setState)
- ✅ Language switching support
- ✅ Loading states

**Commits:**
- 0e1a83f: Landing page Variant A
- db62b34: Frontend documentation
- a766bc9: Backend Phase 1 endpoints
- 89565d4: Frontend-Backend integration
- 83accdd: Documentation update

**Time Spent:** ~4 hours

**Tests Passed:**
- ✅ Backend responds with mock data
- ✅ Frontend fetches and displays data
- ✅ Language switching works
- ✅ Table renders correctly
- ✅ Loading state displays

---

### ⏳ Phase 2: Data Layer (2026-07-03 to 2026-07-04)

**Status:** NOT STARTED

**Deliverables:**
- [ ] Seed MongoDB with initial 8 products
- [ ] Create ProductService.seed_products()
- [ ] Endpoint: `POST /api/v1/products/seed`
- [ ] Verify frontend fetches real DB data
- [ ] Test with Postman/curl

**Tasks:**
1. Write seed script for MongoDB
2. Insert 8 products from mock data
3. Set dedup_hash, source, timestamps
4. Verify frontend receives DB data (not mock)
5. Create seed endpoint (admin only)

**Time Estimate:** 4-6 hours

**Success Criteria:**
- [ ] Frontend table shows DB data (8 products)
- [ ] prices[] array populated for all 4 stores
- [ ] min_price calculated correctly
- [ ] cheapest_store highlighted correctly
- [ ] updated_at shows current timestamp

---

### ⏳ Phase 3: Real Scrapers (2026-07-05 to 2026-07-07)

**Status:** NOT STARTED

**Deliverables:**

#### 3A: Aroma.me Scraper
- [ ] Implement using Playwright (JS rendering)
- [ ] Fallback to BeautifulSoup (HTML)
- [ ] Parse product name, price, category
- [ ] Extract images (optional)
- [ ] Retry logic (3 attempts, exponential backoff)
- [ ] Error logging

#### 3B: Voli.me Scraper
- [ ] Same as Aroma.me
- [ ] Handle site-specific selectors
- [ ] Price normalization (EUR)

#### 3C: HDL.me Scraper
- [ ] Same as Aroma.me
- [ ] Handle site-specific selectors

#### 3D: IDEA.me Scraper
- [ ] Same as Aroma.me
- [ ] Handle site-specific selectors

#### 3E: Instagram Scraper
- [ ] instagrapi authentication
- [ ] Fetch recent posts (48h lookback)
- [ ] OCR text extraction (Tesseract)
- [ ] Price regex matching
- [ ] Image processing (normalize sizes)
- [ ] Product parsing (name, price, category)

**Files to Create/Update:**
- `backend/app/services/aroma_scraper.py`
- `backend/app/services/voli_scraper.py`
- `backend/app/services/hdl_scraper.py`
- `backend/app/services/idea_scraper.py`
- `backend/app/services/instagram_scraper.py` (enhance)
- `backend/app/api/v1/endpoints/scrapers.py` (enhance)

**Time Estimate:** 15-20 hours

**Success Criteria:**
- [ ] Each scraper returns 20+ products
- [ ] Prices extracted correctly (EUR format)
- [ ] Deduplication working (no duplicate products)
- [ ] Error handling + logging
- [ ] Retry logic working
- [ ] Frontend displays scraped data

---

### ⏳ Phase 4: Background Tasks & Scheduling (2026-07-08 to 2026-07-09)

**Status:** NOT STARTED

**Deliverables:**
- [ ] APScheduler integration
- [ ] 24h auto-scan scheduler
- [ ] Run all scrapers in parallel
- [ ] Retry logic with exponential backoff
- [ ] Error notifications (logging + optional email)
- [ ] Supervisor configuration (production)

**Files to Create/Update:**
- `backend/app/services/orchestrator.py` (enhance)
- `backend/app/core/scheduler.py` (new)
- `docker-compose.yml` (supervisor)

**Tasks:**
1. Integrate APScheduler
2. Configure 06:00 AM daily scan
3. Parallel execution for 5 scrapers
4. Retry failed scrapes (3 attempts)
5. Log results to file
6. Send error notifications

**Time Estimate:** 8-10 hours

**Success Criteria:**
- [ ] Scheduler runs on schedule
- [ ] All 5 scrapers execute in parallel
- [ ] Retry logic working
- [ ] Logs captured and readable
- [ ] Frontend receives updated data

---

### ⏳ Phase 5: Security, Authentication & Polish (2026-07-10 to 2026-07-12)

**Status:** NOT STARTED

**Deliverables:**

#### 5A: Authentication
- [ ] JWT token generation
- [ ] `/auth/login` endpoint
- [ ] `/auth/register` endpoint (admin only)
- [ ] Protected endpoints (admin, user roles)
- [ ] Token refresh logic

#### 5B: Rate Limiting
- [ ] Redis-based rate limiter
- [ ] 100 requests/minute per IP
- [ ] 1000 requests/day per user
- [ ] Graceful 429 responses

#### 5C: Testing
- [ ] Unit tests (services, utilities)
- [ ] Integration tests (endpoints)
- [ ] E2E tests (frontend + backend)
- [ ] Load testing (AB testing)

#### 5D: Optimization
- [ ] Redis caching for search results
- [ ] Database indexing optimization
- [ ] Frontend code splitting
- [ ] Image optimization (Aroma, Voli, etc.)

**Files to Create/Update:**
- `backend/app/core/auth.py` (new)
- `backend/app/api/v1/endpoints/auth.py` (new)
- `backend/app/middleware/rate_limit.py` (new)
- `backend/tests/` (new test suite)

**Time Estimate:** 12-15 hours

**Success Criteria:**
- [ ] Protected endpoints require JWT
- [ ] Rate limiting working
- [ ] Tests passing (80%+ coverage)
- [ ] Page load < 2s
- [ ] API response < 500ms

---

## 🎯 KEY MILESTONES

| Milestone | Date | Status |
|-----------|------|--------|
| Project Structure | 2026-06-30 | ✅ DONE |
| Landing Page + API | 2026-07-02 | ✅ DONE |
| Data Layer Ready | 2026-07-04 | ⏳ TODO |
| Real Scrapers | 2026-07-07 | ⏳ TODO |
| Scheduler Live | 2026-07-09 | ⏳ TODO |
| Security Complete | 2026-07-12 | ⏳ TODO |
| **LAUNCH READY** | **2026-07-15** | ⏳ TODO |

---

## 📊 EFFORT BREAKDOWN

| Phase | Frontend | Backend | Docs | Total |
|-------|----------|---------|------|-------|
| 0: Setup | - | 3h | 3h | 6h |
| 1: Landing + API | 3h | 2h | 1h | 6h |
| 2: Data Layer | - | 4h | 1h | 5h |
| 3: Scrapers | - | 18h | 2h | 20h |
| 4: Scheduler | - | 8h | 1h | 9h |
| 5: Security | 2h | 10h | 2h | 14h |
| **TOTAL** | **5h** | **45h** | **10h** | **60h** |

**Estimated:** 2-3 weeks full-time development

---

## 🚀 DEPLOYMENT CHECKLIST

- [ ] All tests passing
- [ ] Docker Compose working locally
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Supervisor configuration ready
- [ ] SSL certificates obtained
- [ ] Domain configured
- [ ] Backup strategy documented
- [ ] Monitoring set up (logs, errors)
- [ ] Performance benchmarks met

---

## 📋 RISK ASSESSMENT

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Scraper sites change layout | High | Medium | Monitor, quick fixes |
| Instagram API rate limits | Medium | Low | Retry logic, caching |
| Database performance | High | Low | Indexing, query optimization |
| CORS issues | Low | Low | Pre-testing with different origins |
| Data quality issues | Medium | Medium | Validation, manual review |

---

## 🔄 CONTINUOUS IMPROVEMENT (Post-Launch)

- [ ] User feedback collection
- [ ] Performance monitoring
- [ ] Bug tracking and fixes
- [ ] Feature enhancements
- [ ] Mobile responsiveness
- [ ] Additional languages (FR, DE, SQ)
- [ ] More stores integration (20+ stores)
- [ ] API rate limiting review
- [ ] Caching strategy optimization

---

**Last Updated:** 2026-07-02  
**Next Review:** Before starting Phase 2  
**Owner:** Serhii Riabko
