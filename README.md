# 🛒 Insta-Data — Price Comparison Platform

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](.)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue)](.)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Real-time price comparison platform for Montenegrin grocery stores monitoring Instagram and 4 official retail websites.**

[📚 Full Documentation](#-documentation) • [🚀 Quick Start](#-quick-start) • [🏗️ Architecture](#-architecture) • [📊 Status](#-project-status)

---

## 🎯 Features

### 🔍 Smart Search
- Real-time full-text search across 5 sources
- Price filtering and comparison
- Trending products (recent updates)
- Redis caching (< 100ms response)

### 📱 Multi-Source Monitoring
- **Instagram** — Live prices from posts via instagrapi + Tesseract OCR
- **Aroma** — Official website via Playwright
- **Voli** — Official website via Playwright
- **HDL** — Official website via BeautifulSoup
- **IDEA** — Official website via BeautifulSoup

### 🌍 3 Languages
- 🇺🇦 Ukrainian (Українська)
- 🇷🇺 Russian (Русский)
- 🇲🇪 Montenegrin (Crnogorski)

### 💾 Intelligent Data Management
- MongoDB for product catalog
- PostgreSQL for price history
- Redis for caching
- Automatic deduplication
- 365-day data retention

### ⏰ Automated Scraping
- Daily automatic scraping at 06:00 UTC
- Parallel execution (5 sources)
- Exponential backoff retry logic
- Error tracking & notifications

### 📊 Responsive UI
- Mobile-first design
- Real-time search suggestions
- Price comparison matrix
- Wishlist functionality
- Dark theme optimized

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Git
- 2GB free disk space

### 2. Setup (3 minutes)
```bash
# Clone repository
git clone https://github.com/SerhiiRiabko/insta-data.git
cd insta-data

# Configure Instagram credentials
cp backend/.env.example backend/.env
nano backend/.env  # Add INSTAGRAM_PASSWORD

# Start services
docker-compose up -d

# Wait for startup
sleep 30

# Verify all services
docker-compose ps
```

### 3. Access Services
- **Frontend:** http://localhost:3003
- **Backend Docs:** http://localhost:8001/docs
- **API:** http://localhost:8001/api/v1

### 4. Test It
```bash
# Search for products
curl "http://localhost:8001/api/v1/search/products?q=млеко"

# Get scraper status
curl "http://localhost:8001/api/v1/scrapers/status"

# View documentation
open http://localhost:8001/docs
```

---

## 📚 Documentation

### Getting Started
| Document | Purpose |
|----------|---------|
| **[LOCAL_SETUP.md](LOCAL_SETUP.md)** | Local development setup (15 min) |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Quick command reference |
| **[PORTS_STATUS.md](PORTS_STATUS.md)** | Port mapping & troubleshooting |

### System Design
| Document | Purpose |
|----------|---------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Complete system architecture (START HERE!) |
| **[PLAN.md](PLAN.md)** | Implementation roadmap |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | Current development status |

### Deployment
| Document | Purpose |
|----------|---------|
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Production deployment guide (Hetzner VPS) |
| **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** | Project completion summary |

### Service Documentation
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser                             │
│              http://localhost:3003                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                    REST API (JSON)
                         │
┌────────────────────────▼────────────────────────────────────┐
│          Nginx Reverse Proxy (Port 80/443)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐ ┌──────▼───────┐ ┌─────▼───────┐
│  Frontend    │ │   Backend    │ │   Swagger   │
│ Next.js 3000 │ │ FastAPI 8000 │ │   Docs      │
└──────────────┘ └──────┬───────┘ └─────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
    ┌───▼───┐      ┌───▼────┐      ┌──▼────┐
    │MongoDB│      │Postgres│      │ Redis │
    │27017  │      │ 5432   │      │ 6379  │
    └───────┘      └────────┘      └───────┘
        │
    ┌───▼────────────────────────────────────┐
    │   Scrapers (Daily 06:00 UTC)           │
    ├─────────────────────────────────────────┤
    │ • Instagram (instagrapi + Tesseract)   │
    │ • Aroma (Playwright)                   │
    │ • Voli (Playwright)                    │
    │ • HDL (BeautifulSoup)                  │
    │ • IDEA (BeautifulSoup)                 │
    └────────────────────────────────────────┘
```

---

## 📊 Project Status

### Completion
- ✅ **Phase 1:** Instagram Parser POC (100%)
- ✅ **Phase 2:** Web Scrapers (100%)
- ✅ **Phase 3:** Frontend UI (100%)
- ✅ **Phase 4:** Integration & Deployment (100%)

### Statistics
| Metric | Value |
|--------|-------|
| Total Files | 80+ |
| Lines of Code | 10,000+ |
| API Endpoints | 20+ |
| React Components | 6 |
| Service Classes | 12 |
| Unit Tests | 65+ |
| Test Coverage | 80%+ |
| Languages | 3 |

### Performance Targets
| Metric | Target | Status |
|--------|--------|--------|
| Page Load | < 2s | ✅ Ready |
| Search Response | < 100ms | ✅ Ready |
| API Response | < 500ms | ✅ Ready |
| Daily Scan | < 30min | ✅ Ready |
| OCR/Image | < 3s | ✅ Ready |

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI 0.104
- **Language:** Python 3.11
- **Databases:** MongoDB 7.0, PostgreSQL 16, Redis 7.0
- **Scraping:** instagrapi, Playwright, BeautifulSoup4
- **OCR:** Tesseract
- **Testing:** pytest + AsyncIO

### Frontend
- **Framework:** Next.js 15 + React 19
- **Styling:** Tailwind CSS 4 + Framer Motion
- **i18n:** next-intl
- **HTTP:** Axios
- **Charts:** Recharts

### Infrastructure
- **Containers:** Docker 20.10+
- **Orchestration:** Docker Compose 2.0+
- **Reverse Proxy:** Nginx
- **Process Manager:** Supervisor
- **SSL:** Let's Encrypt

---

## 📋 Supported Endpoints

### Search API
```
GET  /api/v1/search/products?q=...     Search products
GET  /api/v1/search/trending           Trending products
GET  /api/v1/search/price?min=...      Price filter
GET  /api/v1/search/cheapest/{store}   Cheapest in store
GET  /api/v1/search/source/{source}    By source
GET  /api/v1/search/stats              Statistics
```

### Scraper API
```
GET  /api/v1/scrapers/status           Scraper status
POST /api/v1/scrapers/run-all          Run all scrapers
POST /api/v1/scrapers/run              Run specific scraper
GET  /api/v1/scrapers/schedule         Schedule info
POST /api/v1/scrapers/pause            Pause scheduler
POST /api/v1/scrapers/resume           Resume scheduler
```

### Instagram API
```
POST /api/v1/instagram/scrape          Scrape Instagram account
GET  /api/v1/instagram/status          Instagram status
POST /api/v1/instagram/test-connection Test credentials
```

---

## 🚀 Deployment

### Local
```bash
# 1. Setup
cp backend/.env.example backend/.env
nano backend/.env  # Add credentials

# 2. Start
docker-compose up -d

# 3. Access
# http://localhost:3003 (Frontend)
# http://localhost:8001/docs (API)
```

### Production
```bash
# Follow DEPLOYMENT.md guide
# Target: Hetzner VPS

# Steps:
1. SSH into VPS
2. Install Docker
3. Clone repository
4. Configure environment
5. Start services
6. Setup Nginx + SSL
7. Configure backups
```

---

## 🧪 Testing

```bash
# Run all tests
docker exec insta-data-backend pytest tests/ -v

# Run with coverage
docker exec insta-data-backend pytest tests/ --cov=app --cov-report=html

# Test specific module
docker exec insta-data-backend pytest tests/unit/test_product_service.py -v
```

---

## 📞 Support

### Resources
- 📖 [Full Architecture](ARCHITECTURE.md)
- 🚀 [Local Setup Guide](LOCAL_SETUP.md)
- 🌐 [Production Deployment](DEPLOYMENT.md)
- 🐛 [Troubleshooting](PORTS_STATUS.md)
- 📊 [Project Status](PROJECT_STATUS.md)

### Issues & Feedback
- GitHub Issues: https://github.com/SerhiiRiabko/insta-data/issues
- Discussions: https://github.com/SerhiiRiabko/insta-data/discussions

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 👤 Author

**Serhii Riabko**
- GitHub: [@SerhiiRiabko](https://github.com/SerhiiRiabko)
- Email: serhii.riabko@example.com
- Telegram: @adyvan_2008

---

## 🎉 Acknowledgments

Built with:
- ❤️ FastAPI Community
- 🚀 Next.js & React
- 🐳 Docker & Docker Compose
- 📊 MongoDB & PostgreSQL

---

## 🌟 Star Us!

If you find this project useful, please consider giving it a ⭐ on GitHub!

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2026-06-16

---

## Quick Links

- [👨‍💻 Get Started](LOCAL_SETUP.md)
- [📐 System Design](ARCHITECTURE.md)
- [🚀 Deploy Now](DEPLOYMENT.md)
- [📚 Full Docs](.)
- [🐛 Report Issue](https://github.com/SerhiiRiabko/insta-data/issues)