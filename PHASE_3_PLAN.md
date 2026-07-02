# Phase 3: Real Scrapers — IMPLEMENTATION PLAN

**Status:** IN PROGRESS (Started 2026-07-02)  
**Target Completion:** 2026-07-07  
**Duration:** 3-5 days  
**Effort Estimate:** 20-25 hours

---

## 🎯 PHASE 3 DELIVERABLES

| Scraper | Status | Priority | Est. Hours | Notes |
|---------|--------|----------|-----------|-------|
| **1. Aroma.me** | ✅ ARCHITECTURE READY | HIGH | 4-5 | First scraper, template |
| **2. Voli.me** | ⏳ TODO | HIGH | 4-5 | Same pattern as Aroma |
| **3. HDL.me** | ⏳ TODO | HIGH | 4-5 | Same pattern as Aroma |
| **4. IDEA.me** | ⏳ TODO | HIGH | 4-5 | Same pattern as Aroma |
| **5. Instagram** | ⏳ TODO | MEDIUM | 5-6 | Different logic: instagrapi + OCR |
| **Integration** | ⏳ TODO | HIGH | 2-3 | Orchestrator + endpoint testing |

**Total Estimated Effort:** 20-25 hours

---

## ✅ WHAT'S DONE (Commit 744c01e)

### 1. Base Scraper Architecture
**File:** `backend/app/services/base_scraper.py` (200+ lines)

```python
# Features:
✅ BaseScraper abstract class
✅ ScrapedProduct dataclass
✅ Retry logic (exponential backoff: 1s, 2s, 4s)
✅ Fallback: Playwright → BeautifulSoup
✅ Price normalization (EUR)
✅ Error handling & logging
✅ Deduplication (MD5 hash)
```

### 2. Aroma.me Scraper (Template)
**File:** `backend/app/services/scrapers/aroma_scraper.py` (180+ lines)

```python
# Implementations:
✅ scrape_with_playwright() - JS rendering
✅ scrape_with_beautifulsoup() - HTML parsing
✅ _parse_html() - Extract products
✅ Selector detection (4 fallback selectors)
✅ Price extraction & normalization
✅ Category detection
✅ Error recovery
```

### 3. Scraper Package
**File:** `backend/app/services/scrapers/__init__.py`

```python
✅ Package exports
✅ Ready for adding Voli, HDL, IDEA, Instagram scrapers
```

---

## ⏳ IMPLEMENTATION PLAN (Day-by-Day)

### DAY 1 (Today 2026-07-02 Afternoon)
**Goal:** First scraper fully working

**Tasks:**
- [ ] Implement Aroma.me scraper (done ✅)
- [ ] Test Aroma scraper endpoint
  - `POST /api/v1/scrapers/run` with `{"store": "aroma"}`
  - Expected: Returns 20+ products with prices
- [ ] Debug and fix Aroma scraper
- [ ] Document findings (site structure, selectors)

**Commit:** `feat(aroma): implement and test Aroma.me scraper`

---

### DAY 2 (2026-07-03)
**Goal:** Voli, HDL, IDEA scrapers ready

**Tasks:**
- [ ] Analyze Voli.me site structure
- [ ] Create voli_scraper.py (copy from Aroma, update selectors)
- [ ] Test Voli scraper
- [ ] Create hdl_scraper.py
- [ ] Test HDL scraper
- [ ] Create idea_scraper.py
- [ ] Test IDEA scraper

**Pattern:**
```python
# Same structure for all 4 store scrapers:
class VoliScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            name="Voli.me",
            base_url="https://www.voli.me"
        )
    
    async def scrape_with_playwright(self): ...
    async def scrape_with_beautifulsoup(self): ...
    async def _parse_html(self, html): ...
```

**Commit:** `feat(voli-hdl-idea): implement store scrapers`

---

### DAY 3 (2026-07-04)
**Goal:** Instagram scraper + Orchestrator integration

**Tasks:**
- [ ] Create instagram_scraper.py
  - Use instagrapi for post fetching
  - OCR with Tesseract for text extraction
  - Regex for price parsing
  - Image processing
- [ ] Integrate all 5 scrapers to Orchestrator
- [ ] Update orchestrator to run all scrapers
- [ ] Test endpoint: `POST /api/v1/scrapers/run-all`
  - Expected: Runs all 5 scrapers in parallel
  - Returns results for each

**Commit:** `feat(instagram): add Instagram scraper + orchestrator`

---

### DAY 4 (2026-07-05)
**Goal:** Testing & optimization

**Tasks:**
- [ ] Test each scraper individually
  - Verify product extraction
  - Verify price parsing
  - Check error handling
- [ ] Test orchestrator (all 5 parallel)
  - Check timing
  - Verify database insertion
- [ ] Optimize selectors if needed
- [ ] Add logging for debugging

**Commit:** `fix(scrapers): optimize selectors and error handling`

---

### DAY 5 (2026-07-06-07)
**Goal:** Production ready + documentation

**Tasks:**
- [ ] Verify all scrapers working on production-like data
- [ ] Test frontend displays scraped data correctly
- [ ] Load MongoDB with real scraped data
- [ ] Performance testing (how many products? how fast?)
- [ ] Document scraper patterns
- [ ] Create PHASE_3_COMPLETION.md

**Commit:** `docs(phase-3): completion report + testing results`

---

## 📋 SCRAPER CHECKLIST (Per Site)

When implementing each site scraper:

### Discovery Phase
- [ ] Visit site (aroma.me, voli.me, etc.)
- [ ] Open DevTools
- [ ] Find product list HTML structure
- [ ] Identify selectors for:
  - Product container
  - Product name/title
  - Product price
  - Product link
  - Category (if available)
  - Image URL (if available)
- [ ] Check if site uses JavaScript (Playwright needed?)
- [ ] Check for rate limiting or anti-scraping measures

### Implementation Phase
- [ ] Copy BaseScraper template
- [ ] Implement `scrape_with_beautifulsoup()` first
  - Test with manual HTML fetch
  - Iterate on selectors
- [ ] Implement `scrape_with_playwright()` if needed
  - Handle JS rendering
  - Wait for elements
- [ ] Test both methods
- [ ] Handle edge cases (missing prices, bad HTML, etc.)

### Testing Phase
- [ ] Test endpoint: `curl -X POST http://localhost:8000/api/v1/scrapers/run -d '{"store":"aroma"}'`
- [ ] Verify response: `{status: "success", products_found: X, products_saved: Y}`
- [ ] Check MongoDB for inserted products
- [ ] Verify prices are normalized (EUR format)
- [ ] Verify no duplicates (dedup_hash working)

### Logging Phase
- [ ] Document site selectors (for future maintenance)
- [ ] Document any special handling
- [ ] Log common errors observed

---

## 🔧 COMMON ISSUES & SOLUTIONS

| Issue | Solution |
|-------|----------|
| No products found | Try different selectors, check for JS rendering |
| Prices not parsing | Update normalize_price() for site's format |
| Rate limiting | Add delays, rotate user agents, use proxies |
| Site structure changed | Monitor logs, update selectors |
| Empty/None categories | Fallback to default category or skip |
| Missing image URLs | Mark as None, optional field |

---

## 📊 SUCCESS CRITERIA

By end of Phase 3:
- ✅ 5 working scrapers (4 stores + Instagram)
- ✅ Each scraper returns 20+ products
- ✅ All prices normalized (EUR)
- ✅ No duplicates in database
- ✅ Orchestrator runs all 5 in parallel
- ✅ Frontend displays scraped data correctly
- ✅ Comprehensive error logging
- ✅ ~100-200 products in database (from all sources)

---

## 🔗 INTEGRATION POINTS

After scrapers are ready:

1. **Orchestrator** (`orchestrator.py`)
   - Add methods to run each scraper
   - Coordinate parallel execution
   - Handle results and errors
   - Store to MongoDB

2. **Endpoint** (`endpoints/scrapers.py` - already scaffolded)
   - `POST /scrapers/run-all` - Run all scrapers
   - `POST /scrapers/run` - Run specific scraper
   - `GET /scrapers/status` - Check status
   - `GET /scrapers/logs` - View execution logs

3. **Frontend**
   - Fetch from `/api/v1/products/matrix`
   - Displays real scraped data
   - Shows all stores + prices

---

## 📝 GIT WORKFLOW

**Commits for Phase 3:**

```
744c01e feat(phase-3): base scraper architecture + Aroma scraper

[DAY 1]
xxxxxxx feat(aroma): test and debug Aroma.me scraper

[DAY 2]
xxxxxxx feat(voli-hdl-idea): implement remaining store scrapers

[DAY 3]
xxxxxxx feat(instagram): add Instagram scraper + orchestrator
xxxxxxx test(scrapers): parallel execution and integration

[DAY 4-5]
xxxxxxx fix(scrapers): optimize and production-ready
xxxxxxx docs(phase-3): completion report
```

---

## 🎯 NEXT PHASE (Phase 4)

After Phase 3 is complete:
- Phase 4: Background Tasks & Scheduler
  - Automatic 24h scrape schedule
  - APScheduler integration
  - Error notifications
  - Supervisor configuration

---

**Last Updated:** 2026-07-02  
**Status:** Starting Day 1 implementation  
**Next Milestone:** Aroma scraper fully tested
