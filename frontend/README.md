# Monte-Shop-Price Frontend

**Real-time grocery price comparison platform for Montenegro**

---

## 🎯 Overview

Monte-Shop-Price is a modern price comparison platform that tracks grocery prices across 4 Montenegrin supermarkets:
- **Aroma** (red badge)
- **Voli** (blue badge)
- **HDL** (orange badge)
- **IDEA** (cyan badge)

Frontend: Next.js 15 React app with 3 landing page design variations.

---

## ✨ Features (Phase 1 — Completed)

### Landing Page Design
- ✅ **3 design variations** (A, B, C)
- ✅ **Variant C (Main)** — Immersive design with Kotor Bay background
- ✅ **Interactive price matrix** — HTML table with 10 products × 4 stores
- ✅ **Cheapest price highlight** — Green background + accent border
- ✅ **Multi-language support** — Russian, Ukrainian, English (i18n)
- ✅ **Responsive layout** — Mobile-optimized
- ✅ **Mock data** — 10 realistic products with EUR prices

---

## 🚀 Quick Start

### Installation
```bash
cd frontend
npm install
```

### Development Server
```bash
npm run dev
```

Access: **http://localhost:3003/[lang]/landing**
- `/ru/landing` — Russian
- `/uk/landing` — Ukrainian
- `/en/landing` — English

### Build for Production
```bash
npm run build
npm start
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/components/PriceMatrixLanding.tsx` | Price comparison table (HTML <table>) |
| `src/components/LandingPageDesignBrief.tsx` | 3 design variations (A, B, C) |
| `tailwind.config.ts` | Brand colors, fonts, design tokens |
| `src/app/[lang]/landing/page.tsx` | Landing page route |
| `PROJECT_MAP.md` | Full architecture & status |

---

## 🎨 Variant C (Current)

**Immersive design with:**
- Full-screen Kotor Bay background
- Dark header band with hero content
- Mint green background section
- Store chips (horizontal: Aroma, Voli, HDL, IDEA)
- Price matrix table with:
  - 10 products (rows)
  - 4 stores (columns)
  - Cheapest column (highlighted)
  - 30% gray underlayment for readability
  - Horizontal + vertical lines

---

## 📊 Mock Data

**Products:** 10 items (milk, bread, eggs, cheese, bananas, coffee, oil, water, burgers, parmesan)

**Stores:** 4 supermarkets with color badges

**Prices:** EUR € with locale-specific formatting

---

## 🌐 Localization

Supports 3 languages (RU / UK / EN):
- Hero tagline
- Search placeholder
- Navigation
- Table headers

Edit `TRANSLATIONS` in `LandingPageDesignBrief.tsx` to add/modify.

---

## 🛠️ Tech Stack

- **Framework:** Next.js 15
- **UI:** React 19 + TypeScript
- **Styling:** Tailwind CSS 4
- **Localization:** next-intl
- **Fonts:** Google Fonts (Plus Jakarta Sans, Space Grotesk)

---

## 🚀 Phase 2+ (Planned)

- [ ] Backend API (FastAPI)
- [ ] Real price data scrapers
- [ ] Search & filtering
- [ ] Price history charts
- [ ] User authentication
- [ ] Favorites & alerts
- [ ] Admin panel

---

## 📖 Full Documentation

See `PROJECT_MAP.md` for:
- Complete architecture
- Component details
- Design decisions
- Feature roadmap

---

**Last Updated:** 2026-06-23
