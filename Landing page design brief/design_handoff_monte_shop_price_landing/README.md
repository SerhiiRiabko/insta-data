# Handoff: Monte-Shop-Price — Landing page

## Overview
Landing page for **Monte-Shop-Price**, a real-time grocery price-comparison platform for Montenegrin supermarkets. The page lets a shopper search a product and read a **price-comparison matrix** (products as rows, supermarkets as columns) where the cheapest price for each product is highlighted. Copy is multilingual: **Russian / Ukrainian / English**, switched from the header.

This bundle contains **three layout variations** of the same landing page so the team can pick a direction.

## About the Design Files
The files in this bundle are **design references created in HTML** — prototypes that show the intended look, layout, and behavior. They are **not production code to copy directly**. The task is to **recreate these designs in the target codebase's environment** (per the design extract that is Next.js 15 + React 19 + Tailwind CSS 4) using its established patterns, components, and i18n setup. If no environment exists yet, choose the most appropriate framework and implement there.

> Note on file format: the `.dc.html` files are authored in an internal "Design Component" format and rely on `support.js` (included) to run in a browser. Treat them as **visual + behavioral references**, not as a code module to import. The exact styles, measurements, copy, and data are all transcribed in this README so you can implement without reverse-engineering the runtime.

## Fidelity
**High-fidelity (hifi).** Final colors, typography, spacing, copy, and the cheapest-cell highlight logic are all specified. Recreate the UI pixel-closely with the codebase's libraries. The three variations share one identical price matrix; only the hero/photo treatment differs.

---

## Screens / Views

All three variations are the **same page** at design width **1280 px**. Each = header → hero (with search) → price matrix. No footer (out of scope for this round).

### Variation A — Floating panel over photo
- **Purpose**: Photo-forward hero; the matrix "floats" up over the bottom of the hero photo.
- **Layout**:
  - Full-width **hero block**, background = Kotor Bay photo with a vertical green gradient overlay (`linear-gradient(180deg, rgba(6,78,59,0.5) 0%, rgba(6,78,59,0.22) 38%, rgba(6,78,59,0.82) 100%)`), `background-size:cover`, `background-position:center 38%`. Hero has `padding-bottom: 150px`.
  - **Top bar** inside hero: `display:flex; justify-content:space-between; align-items:center; padding:24px 44px`. Left = logo (monogram + wordmark, white). Center = nav links (white). Right = language pills (light style).
  - **Hero center** (`text-align:center; padding:72px 44px 0`): kicker pill → H1 → tagline → search bar (max-width 640px).
  - **Matrix** pulled up over the photo: container `margin-top:-118px; padding:0 44px 52px; position:relative; z-index:2`.

### Variation B — Split hero, matrix on light
- **Purpose**: Calmer, editorial split; photo is a side panel.
- **Layout**:
  - **White header bar**: `padding:20px 44px; border-bottom:1px solid #eef4f1`. Logo (dark), nav (dark `#33524a`), language pills (paper style).
  - **Split hero**: `display:grid; grid-template-columns:1fr 1fr`.
    - Left cell: `padding:72px 56px; background:#f4faf7`, vertically centered. Kicker → H1 (50px) → tagline → search bar (bordered input variant).
    - Right cell: `min-height:440px`, Kotor photo, overlay `linear-gradient(110deg, rgba(6,78,59,0.28) 0%, rgba(6,78,59,0.05) 60%)`.
  - **Matrix section**: `padding:52px 56px; background:#fff`. Section title (`tableTitle`, 24px/800) + subtitle, then the matrix.

### Variation C — Immersive header band, matrix close-up
- **Purpose**: Compact immersive photo band; matrix is the dominant element on a mint field.
- **Layout**:
  - **Photo band**: `background` = Kotor photo + `linear-gradient(125deg, rgba(6,78,59,0.88) 0%, rgba(6,78,59,0.5) 55%, rgba(11,110,79,0.35) 100%)`, `background-position:center 42%`, `padding:26px 44px 60px`.
    - Top bar (logo monogram is **white bg / green "M"** here), nav (white), language pills (light style).
    - Left-aligned hero (`max-width:680px; padding-top:40px`): kicker → H1 (52px, uses `heroLine` copy) → tagline → search bar.
  - **Matrix section**: `padding:48px 44px 56px; background:#edf6f1`. A row of **store chips** (rounded-pill, white bg, 1px `#dceae3` border, colored initial badge + name) above the matrix.

---

## Component: Price Comparison Matrix (shared by all 3 variations)

A bordered white card containing a table. **Products = rows, stores = columns**; the cheapest cell per row is highlighted; a trailing "Cheapest" summary column repeats the best price + store.

- **Card**: `background:#fff; border-radius:18px; border:1px solid #e3eee8; box-shadow:0 28px 64px -30px rgba(6,78,59,0.4); overflow:hidden`.
- **Card header**: `display:flex; justify-content:space-between; padding:20px 24px; border-bottom:1px solid #eef4f1`. Left = 9px accent dot (`#0b6e4f`) + `tableTitle` (17px/700, `#0f3d2e`). Right = `updated` (13px, `#7d9a8d`, mono).
- **Table**: `width:100%; border-collapse:collapse`.
  - **Head row** background `#f6faf8`, bottom border `1px solid #d9e7df`:
    - Product column header: left-aligned, 12px/600 uppercase, letter-spacing 0.06em, color `#6b8a7d`, padding `16px 22px`.
    - Each store header: right-aligned, padding `16px 18px`. Cell content = flex row (justify end, gap 8px): **initial badge** (24×24, `border-radius:7px`, store color bg, white mono 12px/700) + **store name** (13px/600, `#33524a`).
    - Cheapest header: right-aligned, 12px/700 uppercase, color `#0b6e4f`, background `#eafaf1`, left border `1px solid #e3eee8`.
  - **Body rows** (`border-bottom:1px solid #eef4f1` per cell):
    - Product name cell: left, padding `15px 22px`. Name (15px/600, `#0f3d2e`) + unit (12px mono, `#94aea3`).
    - Normal price cell: right, padding `15px 18px`, **Space Grotesk** 15px, color `#52736a`, `font-variant-numeric:tabular-nums`.
    - **Cheapest price cell**: same but `font-weight:700; color:#05603a; background:#d8f3e3; box-shadow:inset 3px 0 0 #0b6e4f`.
    - Cheapest summary cell: right, padding `13px 22px`, left border `1px solid #f0f5f2`, background `#fafdfb`. Best price (Space Grotesk 17px/700, accent `#0b6e4f`) + store name (11px uppercase, `#94aea3`).

**Cheapest logic**: for each product, `min = Math.min(...prices)`; the cell whose value equals `min` gets the highlight; the summary column shows `min` and the store at that index. (If two stores tie for min, the current implementation highlights the first match — confirm desired tie-handling.)

---

## Interactions & Behavior
- **Language switcher** (RU / UK / EN pills in every header): clicking sets the active language and re-renders **all copy and product/unit names + price formatting** instantly. In the prototype all three variation frames share one language state so they stay in sync; in production this is a single app-level locale.
- **Search form**: present and styled; `onSubmit` is prevented (no live search wired in the mock). Hook to the search/results flow in production (the source extract debounces at 500 ms).
- **Language pills**: active pill = filled; inactive = outline. Two themes — "on photo" (light: active white bg / green text, inactive translucent white border) and "on paper" (dark: active green bg / white text, inactive `#cddfd6` border).
- **Motion**: pills transition `all 120ms cubic-bezier(0.2,0,0,1)`. Numbers/prices appear instantly (no count-up).
- **Responsive**: design is specified at 1280px desktop. The matrix card has `overflow-x:auto`. Per the source extract, mobile collapses price columns and stacks; recreate with the codebase's responsive utilities.

## State Management
- `locale`: `'ru' | 'uk' | 'en'` — drives all copy, product names, units, and price formatting. (Prototype prop `defaultLang` seeds the initial value.)
- `searchQuery`: bound to the hero input (not wired in mock).
- Product data is static mock data here; in production it comes from the price API.

## Price formatting
- RU / UK: `"€ " + value.toFixed(2)` with the decimal **comma** (e.g. `€ 1,49`).
- EN: `"€" + value.toFixed(2)` with the decimal **point** (e.g. `€1.49`).

---

## Design Tokens

### Colors
| Token | Hex | Use |
|---|---|---|
| Accent / Probe green | `#0b6e4f` | Buttons, wordmark dot, brand monogram, cheapest inset bar, best price, active pills |
| Deep green (ink) | `#0f3d2e` | Headings, primary text |
| Green text muted | `#52736a` | Normal price cells |
| Cheapest text | `#05603a` | Cheapest price cell text |
| Cheapest cell bg | `#d8f3e3` | Cheapest price cell background |
| Cheapest header bg | `#eafaf1` | Cheapest column header |
| Subtle green text | `#6b8a7d` / `#7d9a8d` / `#94aea3` | Labels, units, captions |
| Card border | `#e3eee8` | Matrix card border |
| Hairline | `#eef4f1` / `#d9e7df` / `#f0f5f2` | Row/section dividers |
| Head fill | `#f6faf8` | Table header background |
| Section mint (Var C) | `#edf6f1` | Matrix section background |
| Split panel mint (Var B) | `#f4faf7` | Hero left cell |
| Canvas gray | `#e7ece9` | Presentation backdrop (not part of the page) |
| Page white | `#ffffff` | Page background |
| Gradient overlay green | `rgba(6,78,59, a)` | Photo overlays (a = 0.05–0.88, see each variation) |
| Store: Aroma | `#e11d48` | Initial badge |
| Store: Voli | `#2563eb` | Initial badge |
| Store: HDL | `#d97706` | Initial badge |
| Store: IDEA | `#0891b2` | Initial badge |

### Typography
- **UI / prose**: **Plus Jakarta Sans** (Google Fonts), weights 400/500/600/700/800.
- **Numbers / data / prices / units**: **Space Grotesk** (Google Fonts), weights 400–700, with `font-variant-numeric:tabular-nums`.
- Key sizes: H1 58px (A) / 50px (B) / 52px (C), all weight 800, letter-spacing ≈ -0.025em; tagline 19–20px; section title 24px/800; table body 15px; labels 12–13px; captions 11–12px.

### Spacing
- Frame width 1280px. Section paddings 44–56px horizontal. Card radius 18px; pill radius 999px; input/button radius 10–12px; badge radius 6–7px.

### Shadows
- Matrix card: `0 28px 64px -30px rgba(6,78,59,0.4)`.
- Search bar (on photo): `0 24px 50px -22px rgba(6,40,28,0.55)` (A) / `0 20px 44px -20px rgba(6,40,28,0.5)` (C).
- Presentation frame cards: `0 1px 3px rgba(0,0,0,.08)` (not part of the page itself).

---

## Mock Data (products & prices, EUR)
Order = `[Aroma, Voli, HDL, IDEA]`. Cheapest is computed, shown here in **bold**.

| Product (ru / uk / en) | Unit | Aroma | Voli | HDL | IDEA |
|---|---|---|---|---|---|
| Молоко / Молоко / Milk | 1 л | 1.49 | 1.45 | 1.52 | **1.39** |
| Хлеб / Хліб / Bread | 500 г | 0.89 | 0.95 | **0.85** | 0.92 |
| Яйца / Яйця / Eggs | 10 шт | 2.49 | **2.39** | 2.55 | 2.45 |
| Сыр Гауда / Сир Гауда / Gouda cheese | 1 кг | 8.90 | 9.20 | **8.45** | 8.99 |
| Бананы / Банани / Bananas | 1 кг | 1.29 | **1.19** | 1.35 | 1.25 |
| Кофе молотый / Кава мелена / Ground coffee | 250 г | 4.49 | 4.29 | 4.59 | **4.19** |
| Оливковое масло / Оливкова олія / Olive oil | 1 л | 6.99 | 7.49 | **6.79** | 7.10 |
| Вода / Вода / Water | 1,5 л | 0.55 | 0.59 | **0.49** | 0.52 |

### Localized UI strings
| Key | RU | UK | EN |
|---|---|---|---|
| kicker | Цены в реальном времени | Ціни в реальному часі | Real-time prices |
| tagline | Сравнение цен на продукты в супермаркетах Черногории | Порівняння цін на продукти в супермаркетах Чорногорії | Real-time grocery price comparison across Montenegro |
| heroLine (Var C) | Лучшая цена на продукты в Черногории | Найкраща ціна на продукти в Чорногорії | The best grocery prices in Montenegro |
| searchPlaceholder | Поиск товара… | Пошук товару… | Search a product… |
| searchBtn | Найти | Знайти | Search |
| nav | Товары · Магазины · О проекте | Товари · Магазини · Про проєкт | Products · Stores · About |
| tableTitle | Сравнение цен | Порівняння цін | Price comparison |
| tableSub | по 4 супермаркетам | по 4 супермаркетах | across 4 supermarkets |
| product | Товар | Товар | Product |
| cheapest | Дешевле всего | Найдешевше | Cheapest |
| updated | Обновлено сегодня | Оновлено сьогодні | Updated today |

---

## Assets
- **Hero photo — Bay of Kotor, Montenegro.** Sourced from Wikimedia Commons (CC BY-SA), file *"Vista de Kotor, Bahía de Kotor, Montenegro, 2014-04-19, DD 25.JPG"* by Poco a poco. Loaded in the prototype via:
  `https://commons.wikimedia.org/wiki/Special:FilePath/Vista_de_Kotor,_Bah%C3%ADa_de_Kotor,_Montenegro,_2014-04-19,_DD_25.JPG?width=2000`
  In production, host your own licensed/optimized Montenegro photo and **attribute per CC BY-SA** if you keep this one. (Note: the in-tool screenshot preview can't show cross-origin background images, but the photo loads normally in a real browser.)
- **Fonts**: Plus Jakarta Sans + Space Grotesk via Google Fonts.
- **Icons**: none in this round (logo is a text monogram "M").

## Files
- `Monte-Shop-Price Landing.dc.html` — the three landing variations + language logic + all data.
- `MatrixTable.dc.html` — the reusable price-comparison matrix component.
- `support.js` — runtime needed to open the `.dc.html` files in a browser (reference only).
