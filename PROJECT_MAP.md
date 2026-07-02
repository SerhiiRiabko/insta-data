# Insta-Data (Monte-Shop-Price) — Project Map

**Статус:** Phase 1 ✅ (Landing Page) → Phase 2 🚀 (Features & Real Data) (2026-06-23)

---

## 📋 Реалізовано (Fase 1)

### Frontend — Landing Page Variations
- ✅ **3 дизайн-варіації** (A, B, C)
  - **Variant A** — Photo-forward (full-width hero + table below)
  - **Variant B** — Split layout (50/50 photo + content)
  - **Variant C** — Immersive (Kotor Bay background + floating matrix)
  
- ✅ **Variant C доопрацьована:**
  - Kotor Bay фоновий образ з gradient overlay
  - Immersive header band (50% темнозелений overlay)
  - Mint background (brand-mint/80) для секції таблиці
  - Магазини (Aroma, Voli, HDL, IDEA) — горизонтальні чіпси
  - Price matrix таблиця з:
    - **HTML <table>** структура
    - **4 стовпці магазинів** (+ cheapest column)
    - **10 товарів** (молоко, хлеб, яйця, сыр, бананы, кофе, масло, вода, бургеры, сыр)
    - **Виділення найдешевшого** — зелене фонування + інтенсивний бордер
    - **Null prices** — відображаються як "—" для недоступних товарів
    - **Горизонтальні линии** (border-bottom) між строками
    - **Вертикальні линии** (border-right) між колонками

- ✅ **Localization (i18n)**
  - RU (Русский)
  - UK (Українська)
  - EN (English)
  - Language switcher на кожному варіанті

- ✅ **Tailwind CSS + Google Fonts**
  - Plus Jakarta Sans (UI text)
  - Space Grotesk (prices/numbers)
  - Brand color tokens (#0b6e4f accent, #0f3d2e deep, #edf6f1 mint, etc.)

- ✅ **Responsive дизайн**
  - Mobile-first approach
  - Padding/spacing adjustments для всіх екранів
  - Scrollable таблиця для малих екранів

---

## 🎨 Design Decisions — Variant C

| Аспект | Реалізація |
|--------|-----------|
| **Background** | Kotor Bay фото + linear-gradient overlay (125deg, rgba(6,78,59,0.3-0.2)) |
| **Header Band** | Темнозелений (rgba(6,78,59,0.88)) immersive hero |
| **Table Section** | Mint фон (brand-mint/80) з backdrop-blur-lg |
| **Table Container** | Сірий фон 30% opacity (bg-gray-500/30) + white box (bg-white/99) |
| **Price Cells** | Inline CSS (32px font, explicit borders, inline left accent line) |
| **Cheapest Highlight** | Зелене фонування (#d8f3e3) + 6px accent border-left |
| **Store Chips** | Horizontal (flex row) з кольоровими бейджами (A, V, H, I) |

---

## 📁 File Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── [lang]/
│   │   │   └── landing/
│   │   │       ├── page.tsx          ← Landing page wrapper
│   │   │       └── layout.tsx        ← Layout for [lang] route
│   │   ├── layout.tsx                ← Global layout
│   │   └── globals.css               ← Global styles + Google Fonts
│   │
│   ├── components/
│   │   ├── PriceMatrixLanding.tsx    ← HTML <table> component (prices grid)
│   │   └── LandingPageDesignBrief.tsx← 3 design variations (A, B, C)
│   │
│   ├── i18n.ts                       ← i18n config (next-intl)
│   └── ...
│
├── tailwind.config.ts                ← Brand colors, fonts
├── next.config.js
├── package.json
└── .env.local
```

---

## 🔄 Component Details

### **PriceMatrixLanding.tsx**
**Призначення:** Tabular price comparison grid

**Props:**
- `products: Product[]` — Array of products with prices per store
- `stores: Store[]` — Array of 4 stores (Aroma, Voli, HDL, IDEA)
- `lang: 'ru' | 'uk' | 'en'` — Current language
- `accent?: string` — Brand accent color (default: #0b6e4f)

**Функціональність:**
- HTML `<table>` з bordar-collapse
- Inline CSS styles (для гарантованого рендерингу)
- Вертикальні лінії (border-right: 4px)
- Горизонтальні лінії (border-bottom: 4px)
- Cheapest price highlight (зелено + accent border)
- Null price handling (відображається як "—")
- Format prices за мовою (EUR comma vs. period)

---

### **LandingPageDesignBrief.tsx**
**Призначення:** 3 landing page варіацій + мова/варіант селектор

**Варіації:**
1. **VariationA** — Photo-forward (top hero, bottom table)
2. **VariationB** — Split (50/50 content + photo)
3. **VariationC** — Immersive (full-screen background, floating matrix) ✅ **MAIN**

**VariationC Структура:**
```
├── Immersive Header Band (50% overlay)
│   ├── Logo + Nav + Lang buttons
│   └── Hero text + search form
│
└── Mint Background Section
    ├── Store Chips (horizontal)
    └── Price Matrix Table (gray 30% + white box)
```

**Mock Data:**
- 10 товарів (PRODUCTS array)
- 4 магазини (STORES array)
- Некоторі товари доступні не у всіх магазинах (null prices)

---

## 📝 Mock Data

### Products (10 items)
- Молоко Моя крав'ята (milk)
- Молоко Дом (house brand)
- Хлеб пшеничный (wheat bread)
- Хлеб ржаной (rye bread)
- Яйца куриные (chicken eggs)
- Сыр Гауда (Gouda cheese)
- Сыр Пармезан (Parmesan)
- Бананы эквадорские (Ecuador bananas)
- Кофе молотый (ground coffee)
- Оливковое масло (olive oil)

### Stores (4 items)
| Store | Badge | Color |
|-------|-------|-------|
| Aroma | A | #e11d48 (red) |
| Voli | V | #2563eb (blue) |
| HDL | H | #d97706 (orange) |
| IDEA | I | #0891b2 (cyan) |

---

---

## 🔧 IMPLEMENTATION ROADMAP — Фази розробки (2026-06-23 →)

### **Phase 2A: Modal Pages & Navigation** (1 неділя)
**Мета:** Реалізувати 3 сторінки при клікові на кнопки навігації

| Кнопка | Функціонал | Компонент |
|--------|-----------|-----------|
| **Товари** | Список всіх товарів із бази (cards/list) | `ProductsModal.tsx` |
| **Магазини** | Таблиця магазинів + посилання на сайти | `StoresModal.tsx` |
| **Про проект** | Інформація по проекту, технічний стек | `AboutModal.tsx` |

**Технічно:**
- [ ] Створити модалі/сторінки за маршрутами (`/uk/products`, `/uk/stores`, `/uk/about`)
- [ ] Додати навігацію в header (3 кнопки → модалі)
- [ ] Mock data (товари, магазини з URL сайтів)

---

### **Phase 2B: Real Data Integration** (2 тижні)
**Мета:** Заповнити базу реальними даними зі 4 магазинів

**Сайти для скрейпингу:**
- Aroma (URL: ???)
- Voli (URL: ???)
- HDL (URL: ???)
- IDEA (URL: ???)

**Технічно:**
- [ ] Написати скрейпери для кожного сайту (Playwright + BeautifulSoup)
- [ ] Зберігати у MongoDB (продукти)
- [ ] Нормалізація цін (EUR, decimal places)
- [ ] Дедуплікація (product_name + store_id)

---

### **Phase 2C: Shopping List Feature** (2 тижні)
**Мета:** Додати функціонал вибору товарів і порівняння магазинів

**Сценарій:**
1. **Вибір товарів** — checkbox/кард додати товар до списку покупок
2. **Обрати магазини** — toggles для вибору 1-4 магазинів
3. **Динамічна таблиця** — тільки обрані магазини + ціни
4. **Підсумок** — сума по кожному магазину + мінімум
5. **Червоні товари** — якщо товару нема в обраних магазинах

**Компоненти:**
- `ShoppingListModal.tsx` — модаль зі списком товарів
- `MagazineSelector.tsx` — вибір магазинів (toggles)
- `ShoppingListTable.tsx` — таблиця з динамічними колонками
- `ShoppingListSummary.tsx` — підсумок по магазинах

**Технічно:**
- [ ] State management (Redux/Zustand) для: selected items, selected stores
- [ ] Обчислення суми по магазинам
- [ ] Фільтрація товарів за наявністю в обраних магазинах
- [ ] Локальне збереження (localStorage)

---

### **Phase 3: Advanced Features** (後future)
- [ ] Збереження списків (БД)
- [ ] Email-уведомлення (price drops)
- [ ] Історія цін (графіки)
- [ ] Рекомендації (AI)

---

## 🚀 Наступні кроки (Phase 2+)

### Нижче — детальне розбиття у секції IMPLEMENTATION ROADMAP ↑

---

## 🛠️ Технічний стек

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15 + React 19 + TypeScript |
| **Styling** | Tailwind CSS 4 |
| **Localization** | next-intl 3.x |
| **Fonts** | Google Fonts (Plus Jakarta Sans, Space Grotesk) |
| **Backend** | FastAPI (planned Phase 2) |
| **Database** | MongoDB + PostgreSQL (planned Phase 2) |
| **Server** | Node.js dev server (localhost:3003) |

---

## 🔗 Важливі посилання

- **Landing Page:** http://localhost:3003/[lang]/landing
  - `/ru/landing` — Русский
  - `/uk/landing` — Українська
  - `/en/landing` — English

- **Figma Design:** (TBD)
- **API Docs:** (Phase 2)

---

## 📊 Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Design Variations (3) | ✅ | A, B, C complete |
| Variant C (Main) | ✅ | Immersive design finalized |
| Price Matrix Table | ✅ | HTML table + inline CSS |
| Store Chips (Horizontal) | ✅ | Color-coded badges |
| i18n (RU/UK/EN) | ✅ | Full translation coverage |
| Responsive Layout | ✅ | Mobile-optimized |
| Mock Data | ✅ | 10 products, realistic prices |
| Backend API | ⬜ | Planned Phase 2 |
| Real Data Scraping | ⬜ | Planned Phase 2-3 |
| User Features | ⬜ | Planned Phase 4+ |

---

**Last Updated:** 2026-06-23
**Developed with:** Claude Code (claude.ai/code)