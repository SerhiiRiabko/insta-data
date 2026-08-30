# Shop Price Online — Frontend

**Real-time grocery price comparison across Montenegro (ME) and Ukraine (UA).**

> ⚠️ This file used to describe a Phase-1 mock-data prototype (3 design
> variations, 10 hardcoded products, /ru /uk /en routes). None of that is
> current. See [`../CLAUDE.md`](../CLAUDE.md) for the actual day-by-day
> changelog and [`../PROJECT_MAP.md`](../PROJECT_MAP.md) for architecture.

---

## 🎯 Overview

Next.js 15 / React 19 app. Only one landing design (`VariationA` inside
`LandingPageDesignBrief.tsx`) is actually rendered — the "3 variations"
mentioned in old docs exist only as static `.dc.html` design references,
never built in React.

Live data comes from the backend's `/products/matrix-cached` (fast, cached)
and `/products/matrix-live` (real scrape, slow — used by the "Оновити ціни"
button and the country-switch trigger). A country `<select>` next to the
language switcher (persisted in `localStorage`) picks ME or UA; the store
columns and currency symbol (€/₴) update accordingly.

---

## 🚀 Quick Start

```bash
npm install
npm run dev
```

Needs `.env.local` with `NEXT_PUBLIC_API_URL` pointing at a running backend
(see `../backend/`). Real routes: `/[lang]` where `lang` is one of
`ukr rus mne srb bos eng` (URL locale = single source of truth, matches
`next-intl` config) — e.g. `http://localhost:3001/ukr`.

```bash
npm run build
npm start
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/components/LandingPageDesignBrief.tsx` | The one actually-rendered landing page (country/lang state, data fetching, header) |
| `src/components/PriceMatrixLanding.tsx` | Desktop price table (`<table>`, sticky header + sticky category labels, cheapest/promo highlighting) |
| `src/components/PriceCardsMobile.tsx` | Mobile card list (same data, different layout) |
| `src/lib/productMatrix.ts` | Shared types (`MatrixProduct`, `Country`, `Lang`), `formatPrice()` (€/₴), category grouping + sort |
| `src/lib/api.ts` | Axios client, all backend API calls |
| `src/app/[lang]/admin/AdminPageClient.tsx` | Admin panel (stores incl. country, scraper agents, tiers, users) |
| `src/app/[lang]/list/[id]/ShoppingListView.tsx` | Shared/saved shopping list page |

---

## 🌐 Localization

6 locales (`ukr rus mne srb bos eng`), URL-segment-driven via `next-intl`.
Landing-page copy lives in `TRANSLATIONS` inside
`LandingPageDesignBrief.tsx`; shared table/category strings live in
`translations` inside `lib/productMatrix.ts`.

---

## 🛠️ Tech Stack

Next.js 15 · React 19 · TypeScript · Tailwind CSS 4 (inline styles used
heavily in the price table for guaranteed rendering) · next-intl · Axios ·
Google Fonts (Plus Jakarta Sans, Space Grotesk)

---

**Last Updated:** 2026-08-30
