# 🛒 Shop Price Online — Price Comparison Platform

[![Status](https://img.shields.io/badge/Status-Live%20in%20Production-brightgreen)](http://138.199.204.107:3010/ukr)

**Real-time grocery price comparison across two countries: Montenegro (4 chains) and Ukraine (4 live chains, growing).**

Live: **http://138.199.204.107:3010/ukr** (also `/rus /mne /srb /bos /eng`)
Admin: **http://138.199.204.107:3010/ukr/admin**
API/Swagger: **http://138.199.204.107:8010/docs**

> ⚠️ **This README describes what's actually running**, not an aspirational
> spec. The day-by-day changelog with full technical detail (bugs found,
> root causes, what was tried and rejected) is in **[CLAUDE.md](CLAUDE.md)**
> — that's the primary source of truth for this project. This file is a
> summary for someone new to the codebase.

---

## 🎯 What it does

A price-comparison table, per country:

- **🇲🇪 Montenegro** — Aroma, Voli, HDL, IDEA. Prices come from **cijene.me**,
  a third-party aggregator that already covers all 4 chains from one scrape
  (`cijene_scraper.py`).
- **🇺🇦 Ukraine** — Novus, Varus, Сільпо, Фора, each scraped independently
  (no shared aggregator exists for Ukraine). АТБ is written but disabled
  (blocked by a Cloudflare managed challenge — see CLAUDE.md #26). Коло has
  no online catalog at all, so it can't be scraped.

For each product, the table shows every store's price side by side, with:
- the cheapest cell highlighted green
- discounted ("акційна") cells highlighted in a lighter green, independent
  of whether they're also the cheapest
- rows sorted so genuine multi-store comparisons float to the top of each
  category, instead of being buried among the (far more numerous)
  single-store listings — see CLAUDE.md #29
- category and product-name **synonym normalization** so e.g. "томат" and
  "помідор" (different stores, same vegetable) are recognized as the same
  product (CLAUDE.md #28–29)

A guest can build a shareable shopping list (no login) or create an account
(email+password or magic link) to save/manage multiple lists. An
admin-only panel manages the store list (with a country field), scraper
agents, tier limits, and users.

---

## 🌍 6 languages

🇺🇦 Ukrainian · 🇷🇺 Russian · 🇲🇪 Montenegrin · 🇷🇸 Serbian · 🇧🇦 Bosnian · 🇬🇧 English
(URL-locale is the single source of truth — `/ukr/...`, `/eng/...`, etc.)

---

## 🏗️ Actual architecture (not Docker in production)

```
Browser
  │
  ▼
Next.js 15 / React 19 frontend  (supervisord: insta-data-frontend, :3010)
  │  axios, withCredentials (HttpOnly JWT session cookie)
  ▼
FastAPI backend  (supervisord: insta-data-backend, :8010)
  │
  ├── MongoDB (primary datastore: products, stores, users, lists)
  ├── PostgreSQL (connected, not actually used for anything live)
  └── Scraper orchestrator (app/services/scrapers/orchestrator.py)
        ├── cijene.me aggregator      → ME: Aroma/Voli/HDL/IDEA
        ├── Playwright: silpo_scraper.py   → UA: Сільпо
        ├── Playwright: varus_scraper.py   → UA: Varus
        ├── Playwright: fora_scraper.py    → UA: Фора
        ├── Playwright: novus_scraper.py   → UA: Novus
        └── Playwright: atb_scraper.py     → UA: АТБ (written, NOT registered - Cloudflare)
```

- **No Docker in production.** `docker-compose.yml` exists (useful for a
  from-scratch local Mongo/Postgres if you want it) but the live deployment
  runs directly on a shared Hetzner VPS (also hosting the unrelated
  `hrd-minion` bot) via `supervisord`, `git pull` + `npm run build` /
  `venv` restarts. See `CLAUDE.md` for the actual deploy commands used.
- **No Instagram/OCR pipeline.** Early phases (see `PHASE_1-3` docs)
  prototyped an Instagram-post OCR scraper (`instagrapi` + Tesseract) - it
  never became part of the live pipeline and `instagrapi` was later removed
  from `requirements.txt` entirely (it hard-pinned an incompatible
  `pydantic` version and broke `pip install`).
- **No Redis.** Not wired into anything that's actually running.
- **Playwright, not aiohttp, for the Ukrainian scrapers.** A plain HTTP GET
  gets blocked (HTTP 403, likely TLS/JA3 fingerprinting) on Сільпо/Varus/
  Фора/Novus even with realistic headers; a real Playwright-driven
  Chromium passes. АТБ needs Playwright too, but its Cloudflare managed
  challenge blocks Playwright as well (tried: `navigator.webdriver` patch,
  headed mode, real installed Chrome via `channel="chrome"` — none
  cleared it) — that scraper is written but not registered.

---

## 📚 Documentation

| Document | What it actually is |
|----------|---------------------|
| **[CLAUDE.md](CLAUDE.md)** | **Primary source of truth.** Dated changelog with full technical detail - bugs found, root causes, what was tried and rejected. Read this first for "what's the current state and why." |
| **[PROJECT_MAP.md](PROJECT_MAP.md)** | Architecture reference, updated per phase (less granular than CLAUDE.md). |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | Point-in-time snapshots, updated occasionally - not always current. |
| **[PHASE_4_PLAN.md](PHASE_4_PLAN.md)** | Detailed plan/log for accounts, shopping lists, admin panel, localization (Phase 4). |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | ⚠️ Describes a Docker+Nginx+SSL deployment that was never actually used - the real deploy is simpler (see CLAUDE.md). Kept for the parts that are still accurate (env var reference, etc.) but don't follow it end-to-end. |
| `PHASE_1_COMPLETION.md`, `PHASE_2_COMPLETION.md`, `PHASE_3_PLAN.md`, `PHASE_3_PROGRESS.md` | Historical - describe the mock-scraper/Instagram-OCR prototype phase, superseded by the real cijene.me pipeline. Kept as history, not current. |
| `PLAN.md`, `DESIGN_EXTRACT.md`, `PORTS.md`, `PORTS_STATUS.md`, `TEST_API.md`, `QUICK_REFERENCE.md`, `LOCAL_SETUP.md`, `INDEX.md`, `FINAL_SUMMARY.md`, `ARCHITECTURE.md` | Earlier planning/reference docs, written before the country selector and Ukraine scrapers existed - accurate for the Montenegro-only, single-country era, not fully current. |

---

## 🛠️ Tech stack (as actually running)

**Backend:** FastAPI (async) · Python · MongoDB (Motor/async driver) ·
Playwright (Chromium) + aiohttp + BeautifulSoup4 · APScheduler (weekly ME
refresh) · passlib/bcrypt (auth) · Resend (magic-link email, reused from a
sibling project)

**Frontend:** Next.js 15 + React 19 · Tailwind CSS 4 · next-intl (6
locales) · Axios

**Infra:** Hetzner VPS · supervisord · git-based deploy (no CI/CD)

---

## 🚀 Local development

```bash
# Backend
cd backend
venv/Scripts/uvicorn app.main:app --reload --port 8001   # Windows venv
# needs a local MongoDB (native service, mongodb://localhost:27017 - see
# backend/.env for the exact local override) and backend/.env with a
# SECRET_KEY etc.

# Frontend
cd frontend
npm run dev
# needs frontend/.env.local with NEXT_PUBLIC_API_URL=http://localhost:8001
```

See `LOCAL_SETUP.md` for more detail (written for the Montenegro-only era,
but the local-dev mechanics are still accurate).

---

## 👤 Author

**Serhii Riabko** — Telegram: @adyvan_2008

---

**Last Updated:** 2026-08-30
