# INSTA-DATA — Phased Implementation Plan

**Created:** 2026-06-16  
**Status:** Phase 0 ✅ → Phase 1 NEXT

---

## 📊 PHASE 0: Documentation Discovery ✅

### Findings Summary

| Component | Tech | Status | Version | Notes |
|-----------|------|--------|---------|-------|
| **Backend Framework** | FastAPI + Uvicorn | Ready | 0.104.1 | Async-first, lifespan management ✓ |
| **Instagram Scraping** | instagrapi | Ready | 2.0.0 | Installed, needs session handling |
| **Web Scraping** | Playwright + BeautifulSoup4 | Ready | 1.40.0 + latest | JS rendering + HTML fallback |
| **Image Processing** | Pillow + pytesseract | Ready | 10.1.0 + 0.3.10 | OCR for price extraction |
| **MongoDB** | Motor (async) | Ready | 3.3.2 | Global state pattern with `_mongo_db` |
| **PostgreSQL** | SQLAlchemy 2.0 + Alembic | Ready | 2.0.23 + 1.12.1 | Sync engine, no migrations yet |
| **Docker** | Docker Compose | Ready | V3 | All services connected: Mongo, PG, Redis, Backend, Frontend |
| **Endpoints** | API v1 router | Stub only | - | `/api/v1/status` only, no actual endpoints |

### Critical Decisions Made

✅ **Async-First MongoDB:** Use Motor async client (already in requirements + main.py)  
✅ **Sync PostgreSQL:** Keep synchronous SQLAlchemy (simpler, sufficient for timeseries)  
✅ **Session Management:** Store instagrapi session file locally in `backend/sessions/` (.gitignore'd)  
✅ **Docker Services:** All running on internal network (mongo:27017, postgres:5432, redis:6379)  
✅ **Environment Config:** Pydantic BaseSettings in `core/config.py` (no hardcoded secrets)

---

## 🚀 PHASE 1: Instagram Parser POC (Week 1-2)

### Goal
Create working Instagram post scraper → extract products/prices → save to MongoDB

### Tasks

#### 1.1: Create Data Models (Pydantic + SQLAlchemy)

**Files to create:**

**`backend/app/models/product.py`**
```python
# Pydantic models for validation + FastAPI responses
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PricePoint(BaseModel):
    store: str  # "instagram", "aroma", "voli", etc
    price: float
    currency: str = "EUR"
    timestamp: datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    prices: List[PricePoint]
    source: str  # "instagram" or "web"

class Product(ProductBase):
    id: str  # MongoDB ObjectId as string
    prices: List[PricePoint]
    created_at: datetime
    updated_at: datetime
    source: str
```

**`backend/app/models/mongo_schema.py`**
```python
# MongoDB document schemas (for reference, not strict typing)
PRODUCT_SCHEMA = {
    "_id": ObjectId,
    "name": str,
    "description": str,
    "category": str,
    "image_url": str,
    "source": str,  # "instagram" | "aroma" | "voli" | "hdl" | "idea"
    "prices": [
        {
            "store": str,
            "price": float,
            "currency": str,  # "EUR"
            "timestamp": datetime
        }
    ],
    "created_at": datetime,
    "updated_at": datetime,
    "dedup_hash": str  # MD5(name + store) for deduplication
}
```

**Documentation Reference:**
- Pydantic v2: https://docs.pydantic.dev/latest/
- Motor (async MongoDB): https://motor.readthedocs.io/
- Copy pattern from: existing `core/config.py` (BaseModel usage)

**Verification Checklist:**
- [ ] Models compile without errors
- [ ] Pydantic validation works (test with invalid data)
- [ ] MongoDB insertion preserves all fields

---

#### 1.2: Implement Instagrapi Session Manager

**Files to create:**

**`backend/app/services/instagram_auth.py`**
```python
# Safe session handling for instagrapi
import os
from pathlib import Path
from instagrapi import Client
from structlog import get_logger

logger = get_logger(__name__)

SESSION_DIR = Path(__file__).parent.parent.parent / "sessions"

class InstagramSessionManager:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.client = Client()
        self.session_file = SESSION_DIR / f"{email}.session"

    def load_or_create_session(self):
        """Load existing session or create new login"""
        if self.session_file.exists():
            try:
                self.client.load_settings(str(self.session_file))
                logger.info("loaded_session", email=self.email)
                return True
            except Exception as e:
                logger.warning("session_load_failed", error=str(e))
        
        # Create new session
        try:
            self.client.login(self.email, self.password)
            SESSION_DIR.mkdir(parents=True, exist_ok=True)
            self.client.dump_settings(str(self.session_file))
            logger.info("created_session", email=self.email)
            return True
        except Exception as e:
            logger.error("login_failed", error=str(e))
            return False

    def get_client(self):
        return self.client
```

**`.gitignore` addition:**
```
backend/sessions/
*.session
```

**Documentation Reference:**
- instagrapi docs: https://subzeroid.github.io/instagrapi/
- Session handling: https://subzeroid.github.io/instagrapi/usage-guide/session.html
- Copy pattern: existing FastAPI middleware pattern from `main.py`

**Verification Checklist:**
- [ ] Session file saved to `backend/sessions/email.session`
- [ ] Session file is NOT in git (check .gitignore)
- [ ] Subsequent calls load cached session (faster)
- [ ] Login error caught and logged properly

---

#### 1.3: Implement Post Scraper

**Files to create:**

**`backend/app/services/instagram_scraper.py`**
```python
# Scrape recent posts from Instagram account
from datetime import datetime, timedelta
from structlog import get_logger
import asyncio
from motor.motor_asyncio import AsyncClient
from .instagram_auth import InstagramSessionManager

logger = get_logger(__name__)

class InstagramPostScraper:
    def __init__(self, session_manager: InstagramSessionManager, mongo_db):
        self.client = session_manager.get_client()
        self.mongo_db = mongo_db
    
    async def scrape_recent_posts(self, username: str, hours_back: int = 48):
        """
        Scrape posts from past N hours
        Returns: List[{caption, image_urls, timestamp}]
        """
        try:
            medias = self.client.user_medias(user_id=self.client.user_id, amount=30)
            
            cutoff = datetime.now() - timedelta(hours=hours_back)
            recent_posts = [
                m for m in medias 
                if m.taken_at > cutoff
            ]
            
            logger.info("scraped_posts", count=len(recent_posts), hours_back=hours_back)
            return recent_posts
        except Exception as e:
            logger.error("scrape_failed", error=str(e))
            return []
    
    async def process_posts(self, posts):
        """Convert posts to standardized format"""
        processed = []
        for post in posts:
            item = {
                "caption": post.caption,
                "images": [m.url for m in post.resources],  # image URLs
                "timestamp": post.taken_at,
                "url": f"https://instagram.com/p/{post.code}/"
            }
            processed.append(item)
        return processed
```

**Documentation Reference:**
- instagrapi Media object: https://subzeroid.github.io/instagrapi/types.html#media
- Motor async patterns: https://motor.readthedocs.io/en/stable/tutorial-asyncio.html

**Verification Checklist:**
- [ ] Scraper returns posts from past 48 hours
- [ ] Post object has caption, images, timestamp
- [ ] Handles rate-limit errors gracefully (add retry logic)
- [ ] Logs all operations

---

#### 1.4: Implement OCR + Price Extraction

**Files to create:**

**`backend/app/services/price_extractor.py`**
```python
# Extract product names and prices from images using OCR
import pytesseract
from PIL import Image
import re
from io import BytesIO
import requests
from structlog import get_logger

logger = get_logger(__name__)

class PriceExtractor:
    def __init__(self):
        # Tesseract patterns for EUR prices: 0.99€ or 0,99€ or €0.99
        self.price_pattern = r'[\d,\.]+\s*€|€\s*[\d,\.]+'
        self.product_keywords = [
            'mleko', 'maslac', 'sir', 'jajta',  # Montenegrin dairy
            'hleb', 'pecel', 'kolac',  # Bread
            'jogurt', 'kefir', 'pavlaka'  # Dairy
        ]
    
    async def extract_from_image_url(self, image_url: str):
        """Download image and run OCR"""
        try:
            response = requests.get(image_url, timeout=10)
            img = Image.open(BytesIO(response.content))
            return self.extract_from_image(img)
        except Exception as e:
            logger.error("image_download_failed", url=image_url, error=str(e))
            return None
    
    def extract_from_image(self, img: Image.Image):
        """Run Tesseract OCR on PIL Image"""
        try:
            # Preprocess: convert to grayscale, increase contrast
            img = img.convert('L')
            
            # Run OCR
            text = pytesseract.image_to_string(img, lang='srp+eng+ces')
            logger.info("ocr_complete", chars=len(text))
            
            # Extract prices
            prices = re.findall(self.price_pattern, text)
            
            # Extract product name (simple: take first line before first price)
            lines = text.split('\n')
            product_name = lines[0] if lines else "Unknown"
            
            return {
                "product_name": product_name.strip(),
                "prices": [float(p.replace('€', '').replace(',', '.')) for p in prices],
                "raw_text": text[:500]  # Store first 500 chars for debugging
            }
        except Exception as e:
            logger.error("ocr_failed", error=str(e))
            return None
```

**Documentation Reference:**
- pytesseract: https://github.com/madmaze/pytesseract
- Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
- PIL Image preprocessing: https://pillow.readthedocs.io/

**Verification Checklist:**
- [ ] OCR extracts text from sample Instagram image
- [ ] Price regex matches EUR format (0.99€, €0.99, 0,99€)
- [ ] Product name extracted (first non-empty line)
- [ ] Handles corrupt/unreadable images gracefully

---

#### 1.5: Create Product Storage Service

**Files to create:**

**`backend/app/services/product_service.py`**
```python
# Save/deduplicate products in MongoDB
from motor.motor_asyncio import AsyncClient
from datetime import datetime
import hashlib
from structlog import get_logger

logger = get_logger(__name__)

class ProductService:
    def __init__(self, mongo_db):
        self.db = mongo_db
    
    async def save_product(self, product_data: dict):
        """Save product with deduplication"""
        collection = self.db.products
        
        # Create dedup hash: MD5(product_name + store)
        store = product_data.get("source", "unknown")
        name = product_data.get("name", "")
        dedup_hash = hashlib.md5(f"{name}_{store}".encode()).hexdigest()
        
        # Check if exists
        existing = await collection.find_one({"dedup_hash": dedup_hash})
        
        if existing:
            # Update: append new price point
            new_price = {
                "store": store,
                "price": product_data["price"],
                "currency": "EUR",
                "timestamp": datetime.now()
            }
            await collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$push": {"prices": new_price},
                    "$set": {"updated_at": datetime.now()}
                }
            )
            logger.info("product_updated", dedup_hash=dedup_hash)
        else:
            # Insert new
            doc = {
                "name": product_data["name"],
                "description": product_data.get("description"),
                "category": product_data.get("category"),
                "image_url": product_data.get("image_url"),
                "source": store,
                "prices": [{
                    "store": store,
                    "price": product_data["price"],
                    "currency": "EUR",
                    "timestamp": datetime.now()
                }],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "dedup_hash": dedup_hash
            }
            result = await collection.insert_one(doc)
            logger.info("product_created", id=str(result.inserted_id))
        
        return dedup_hash
```

**Documentation Reference:**
- Motor async operations: https://motor.readthedocs.io/en/stable/tutorial-asyncio.html
- MongoDB update operators: https://docs.mongodb.com/manual/reference/operator/update/

**Verification Checklist:**
- [ ] Products inserted into MongoDB
- [ ] Duplicate products found by dedup_hash
- [ ] Price history appended correctly
- [ ] Timestamps recorded

---

#### 1.6: Create API Endpoint for Instagram Scraping

**Files to create/modify:**

**`backend/app/api/v1/endpoints/instagram.py`** (NEW)
```python
# API endpoint to trigger Instagram scraping
from fastapi import APIRouter, Depends, HTTPException
from structlog import get_logger
from ...database.mongodb import get_mongo_db
from ...services.instagram_auth import InstagramSessionManager
from ...services.instagram_scraper import InstagramPostScraper
from ...services.price_extractor import PriceExtractor
from ...services.product_service import ProductService

logger = get_logger(__name__)
router = APIRouter(prefix="/instagram", tags=["instagram"])

@router.post("/scrape")
async def trigger_instagram_scrape(mongo_db = Depends(get_mongo_db)):
    """
    Endpoint: POST /api/v1/instagram/scrape
    - Loads Instagram session
    - Scrapes posts from past 48 hours
    - Extracts prices from images
    - Saves to MongoDB
    """
    try:
        # Init services
        session_mgr = InstagramSessionManager(
            email="Niobium_Runas",
            password="<from .env>"  # TODO: pass from config
        )
        session_mgr.load_or_create_session()
        
        scraper = InstagramPostScraper(session_mgr, mongo_db)
        extractor = PriceExtractor()
        product_svc = ProductService(mongo_db)
        
        # Scrape
        posts = await scraper.scrape_recent_posts("hrd_minion", hours_back=48)
        processed_posts = await scraper.process_posts(posts)
        
        # Extract prices
        saved_count = 0
        for post in processed_posts:
            for image_url in post["images"]:
                extraction = await extractor.extract_from_image_url(image_url)
                if extraction:
                    await product_svc.save_product({
                        "name": extraction["product_name"],
                        "price": extraction["prices"][0] if extraction["prices"] else 0,
                        "source": "instagram",
                        "image_url": image_url
                    })
                    saved_count += 1
        
        logger.info("scrape_complete", posts=len(posts), products=saved_count)
        return {"posts_scraped": len(posts), "products_saved": saved_count}
    
    except Exception as e:
        logger.error("scrape_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

**Modify `backend/app/api/v1/router.py`:**
```python
from .endpoints import instagram

router = APIRouter(prefix="/api/v1")
router.include_router(instagram.router)
```

**Verification Checklist:**
- [ ] POST /api/v1/instagram/scrape returns 200
- [ ] Response includes `posts_scraped` and `products_saved` counts
- [ ] Database contains new products after call
- [ ] Errors are caught and logged

---

#### 1.7: Write Unit Tests

**Files to create:**

**`backend/tests/unit/test_price_extractor.py`**
```python
import pytest
from app.services.price_extractor import PriceExtractor

@pytest.fixture
def extractor():
    return PriceExtractor()

def test_price_pattern_matching(extractor):
    """Test EUR price regex"""
    assert extractor.price_pattern  # Pattern exists
    
    test_strings = [
        ("Cost: 5.99€", ["5.99€"]),
        ("Price: €12,50", ["€12,50"]),
        ("0,99 € per item", ["0,99 €"])
    ]
    
    for text, expected in test_strings:
        prices = extractor.extract_from_text(text)
        assert len(prices) > 0

def test_missing_image_handling(extractor):
    """Test graceful handling of missing image"""
    result = extractor.extract_from_image_url("https://invalid.url/404")
    assert result is None  # Should return None, not crash
```

**Run tests:**
```bash
cd backend
pytest tests/unit/test_price_extractor.py -v
```

**Verification Checklist:**
- [ ] Tests run without errors
- [ ] Coverage >= 80% for new modules
- [ ] Edge cases handled (missing images, invalid prices)

---

### Phase 1 Summary

| Task | File | Status | Dependencies |
|------|------|--------|--------------|
| Data Models | `models/product.py` | To do | Pydantic v2 docs |
| Instagram Auth | `services/instagram_auth.py` | To do | instagrapi 2.0 |
| Post Scraper | `services/instagram_scraper.py` | To do | Instagram Auth ✓ |
| OCR + Extraction | `services/price_extractor.py` | To do | Pillow + pytesseract |
| Product Storage | `services/product_service.py` | To do | Motor + MongoDB |
| API Endpoint | `api/v1/endpoints/instagram.py` | To do | FastAPI + all services |
| Unit Tests | `tests/unit/*.py` | To do | pytest |

**Estimated Time:** 4-6 days  
**Deliverable:** Working POST /api/v1/instagram/scrape endpoint

---

## 🕸️ PHASE 2: Web Scrapers (Week 2-3)

### Goal
Create scrapers for 4 Montenegrin grocery stores → normalize prices → save to PostgreSQL history

### Tasks (same structure as Phase 1)

#### 2.1: Store Scraper Base Class

**`backend/app/services/store_scrapers.py`**
```python
# Abstract base + concrete implementations for 4 stores
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Browser
from bs4 import BeautifulSoup
import asyncio

class StoreScraper(ABC):
    def __init__(self, store_name: str):
        self.store_name = store_name
        self.base_url = None
        self.browser = None
    
    @abstractmethod
    async def scrape_products(self) -> list[dict]:
        """Return [{name, price, url, timestamp}]"""
        pass
    
    async def setup_browser(self):
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(headless=True)
    
    async def cleanup(self):
        if self.browser:
            await self.browser.close()

class AromaScraper(StoreScraper):
    # Implementation for aromamarketi.me
    pass

class VoliScraper(StoreScraper):
    # Implementation for voli.me
    pass

class HDLScraper(StoreScraper):
    # Implementation for digitalniletak.me/hd-lakovic
    pass

class IdeaScraper(StoreScraper):
    # Implementation for idea.co.me
    pass
```

#### 2.2-2.5: Implement Each Store (4 tasks, similar to above)

For each store:
1. Analyze HTML/API structure
2. Write Playwright or BeautifulSoup scraper
3. Extract product name + price + URL
4. Normalize price (EUR, 2 decimal places)
5. Test with real data

#### 2.6: Price Normalization Service

**`backend/app/services/price_normalizer.py`**
```python
import re
from decimal import Decimal

class PriceNormalizer:
    @staticmethod
    def normalize_eur(price_str: str) -> float:
        """Convert various EUR formats to float"""
        # Remove whitespace
        price_str = price_str.strip()
        # Handle "1.234,50€" or "1,234.50 EUR" etc
        # Replace comma if it's decimal separator
        price_str = price_str.replace(',', '.')
        # Extract first number
        match = re.search(r'\d+\.?\d*', price_str)
        if match:
            return float(match.group())
        return 0.0
```

#### 2.7: PostgreSQL Schema & Alembic Migration

**`backend/alembic/versions/001_create_price_history.py`**
```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('product_id', sa.String, nullable=False),  # from MongoDB
        sa.Column('store', sa.String, nullable=False),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('currency', sa.String, default='EUR'),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_product_store_time', 'product_id', 'store', 'timestamp')
    )

def downgrade():
    op.drop_table('price_history')
```

#### 2.8: Background Task Scheduler

**`backend/app/services/scraper_scheduler.py`**
```python
# Use APScheduler to run scrapers daily
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def run_all_scrapers():
    """Called daily at 6 AM Kyiv time"""
    scrapers = [AromaScraper(), VoliScraper(), HDLScraper(), IdeaScraper()]
    
    for scraper in scrapers:
        try:
            await scraper.setup_browser()
            products = await scraper.scrape_products()
            # Save to PostgreSQL
            # ...
        finally:
            await scraper.cleanup()

scheduler.add_job(run_all_scrapers, 'cron', hour=6, minute=0)
```

### Phase 2 Summary

| Task | Status | Time |
|------|--------|------|
| Store scraper base class | To do | 1 day |
| Aroma scraper | To do | 1 day |
| Voli scraper | To do | 1 day |
| HDL scraper | To do | 1 day |
| IDEA scraper | To do | 1 day |
| Price normalizer | To do | 0.5 days |
| PostgreSQL schema + migration | To do | 0.5 days |
| Scheduler integration | To do | 1 day |
| Tests | To do | 1 day |

**Estimated Time:** 6-8 days  
**Deliverable:** Automated daily scraping of 4 stores → PostgreSQL history

---

## ✅ PHASE 3: Verification & Integration

### Checklist
- [ ] All endpoints documented in `/docs`
- [ ] Unit test coverage >= 80%
- [ ] Integration tests (E2E scraping)
- [ ] Performance: page load < 2s, API < 500ms
- [ ] Database migrations run successfully
- [ ] Error handling + logging comprehensive
- [ ] Docker services all healthy
- [ ] Frontend connects to backend APIs

### Deliverables
- README with setup instructions
- API docs (Swagger)
- Performance metrics
- Deployment guide

---

## 📅 Timeline

| Phase | Duration | Parallel Work |
|-------|----------|---|
| Phase 0 (Discovery) | 1 day | ✓ |
| Phase 1 (Instagram) | 4-6 days | Frontend skeleton |
| Phase 2 (Web Scrapers) | 6-8 days | Frontend PriceMatrix component |
| Phase 3 (Verification) | 2-3 days | Deploy to production |

**Total:** ~2-3 weeks for core scraping + API

---

## 🔧 Technical Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Motor (async MongoDB) | Matches FastAPI async patterns | PyMongo (slower) |
| SQLAlchemy sync | Simpler for timeseries, sufficient scale | async SQLAlchemy (complex) |
| Playwright + BeautifulSoup | JS rendering + fallback | Puppeteer (Node.js, extra complexity) |
| Tesseract OCR | Free, open-source, ~80% accuracy | Cloud Vision API (cost) |
| APScheduler | Native Python, integrates with async | Celery + Redis (overkill) |
| Docker Compose | Local dev + simple deployment | K8s (overkill) |

---

## 🚨 Known Risks

| Risk | Mitigation |
|------|-----------|
| Instagram blocks session (anti-bot) | Implement 2FA handling + backoff |
| OCR accuracy < 50% | Manual price entry UI as fallback |
| Store pages change structure | Monitor + update selectors quarterly |
| Rate limiting on scrapers | Add delays (1-2s per request) + IP rotation |

---

**Next Step:** Choose Phase 1, Task 1.1 — Create Data Models