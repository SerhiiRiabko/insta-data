# 🎨 Monte-Shop-Price Design System — Complete Extract

## 📋 Project Overview
**Monte-Shop-Price** — Real-time price comparison platform for Montenegrin grocery stores.
- **Type**: Price comparison marketplace with product table
- **Target**: Shoppers looking for best deals on groceries
- **Status**: Phase 1 ✅ (Beautiful UI + Mock data + Multi-language)
- **Tech**: Next.js 15 + React 19 + Tailwind CSS 4 + FastAPI backend
- **Ports**: Frontend 3001, Backend 8001

---

## 🎨 Color Palette

| **Role** | **Color** | **Hex** | **Usage** |
|----------|-----------|---------|----------|
| **Primary Dark** | Slate-900 | `#0f172a` | Main background |
| **Primary Medium** | Emerald-900 | `#064e3b` | Accent areas |
| **Primary Gradient** | Slate→Emerald→Slate | `gradient` | Page backdrop |
| **Primary Action** | Emerald-500 | `#10b981` | Buttons, highlights |
| **Secondary** | Cyan-500 | `#06b6d4` | Accent glow |
| **Text Primary** | White | `#ffffff` | Main text |
| **Text Secondary** | Emerald-100 | `#d1fae5` | Supporting text |
| **Text Muted** | White/70% | `rgba(255,255,255,0.7)` | Hints |
| **Border Light** | White/10% | `rgba(255,255,255,0.1)` | Cards |
| **Price Color** | Emerald-300 | `#6ee7b7` | Price highlights |
| **Store Badge** | White/5% | `rgba(255,255,255,0.05)` | Store pills |

**Background Gradient:**
```css
background: linear-gradient(180deg, #0f172a 0%, #064e3b 50%, #0f172a 100%);
```

**Animated Accent Orbs:**
```css
emerald-500 blur-3xl opacity-10 (top-right)
cyan-500 blur-3xl opacity-10 (bottom-left)
```

---

## 📐 Layout Architecture

### **Screen Layout**
```
┌──────────────────────────────────────┐
│  HEADER (Navigation + Language)      │ ← Translucent
├──────────────────────────────────────┤
│                                      │
│  HERO SECTION                        │
│  • Title "Monte-Shop-Price"          │
│  • Description                       │
│  • Search Bar                        │
│                                      │
├──────────────────────────────────────┤
│  • Tab Switcher (Instagram/Official) │
├──────────────────────────────────────┤
│                                      │
│  PRODUCTS SECTION                    │
│  • Trending Products (Grid)          │
│  • Search Results (Table Rows)       │
│                                      │
├──────────────────────────────────────┤
│  FOOTER                              │
└──────────────────────────────────────┘
```

### **Spacing Scale**
- **px-2, px-3**: Button padding
- **px-4**: Default input/card padding
- **px-6, px-8**: Section padding
- **py-2, py-4**: Vertical spacing
- **gap-2, gap-3, gap-4**: Component gaps
- **mb-4, mb-6, mb-8, mb-12**: Margin between sections

---

## 🔤 Typography

| **Element** | **Font** | **Size** | **Weight** | **Usage** |
|-----------|---------|---------|-----------|----------|
| **H1/Brand** | Sans-serif | 3rem–4rem | Black (900) | "Monte-Shop-Price" main |
| **H2/Section** | Sans-serif | 1.5rem–2rem | Bold (700) | "Популярные товары" |
| **H3/Subtitle** | Sans-serif | 1.25rem | Regular (400) | Description text |
| **Body/Default** | Sans-serif | 0.875rem–1rem | Regular (400) | Product info |
| **Small** | Sans-serif | 0.75rem | Regular (400) | Badges, timestamps |
| **Button** | Sans-serif | 0.875rem–1rem | Medium (500) | Action text |

**Letter Spacing:**
- Normal for body text
- Slightly tighter for headlines (better visual impact)

---

## 🧩 Component Library

### **1. Header / Navigation**
```jsx
<header className="relative z-10">
  <Header lang={lang} />
</header>
```
- Translucent background
- Language selector
- Clean, minimal design

### **2. Hero Section**
```jsx
<section className="flex-1 flex flex-col items-center justify-center py-16 px-4">
  <h1 className="text-5xl md:text-6xl font-black text-white drop-shadow-lg">
    {t('app.name')}
  </h1>
  <p className="text-xl md:text-2xl text-emerald-100 mb-12 drop-shadow-md">
    {t('app.description')}
  </p>
  {/* SearchBar + TabSwitcher */}
</section>
```
- Centered, full viewport height
- Large bold headline
- Drop shadow for text clarity
- Responsive font sizes

### **3. Search Bar**
```jsx
<form className="w-full max-w-2xl mx-auto">
  <div className="flex gap-2">
    <input 
      type="text"
      placeholder={t('search.placeholder')}
      className="input w-full pr-10"
    />
    <button className="btn btn-primary px-6">
      {t('search.button')}
    </button>
  </div>
</form>
```
- Full width, responsive max-width
- Debounced search (500ms)
- Loading spinner on input

### **4. Tab Switcher (Radio Buttons)**
```jsx
<div className="flex gap-2 flex-wrap justify-center">
  {tabs.map((tab) => (
    <button
      onClick={() => handleTabChange(tab.id)}
      className={`px-4 py-2 rounded-lg font-medium transition-all ${
        activeTab === tab.id
          ? 'bg-emerald-600 text-white shadow-lg'
          : 'bg-white/10 text-emerald-100 hover:bg-white/20'
      }`}
    >
      {emoji} {tab.label}
    </button>
  ))}
</div>
```
- Icon + text buttons
- Active state: Solid green background
- Inactive state: Transparent with hover
- Options: 📸 Instagram, 🏪 Official Sites, 📊 All

### **5. Product Card (Table Row)**
```jsx
<div className="bg-white/5 backdrop-blur-sm hover:bg-white/10 
                border border-white/10 hover:border-emerald-400/50 
                rounded-xl p-4 transition-all duration-300">
  <div className="flex items-center gap-4">
    {/* Image (16×16) */}
    {/* Product Info (Name + Store Badge) */}
    {/* Prices (Per Store Grid) */}
    {/* Best Price + Wishlist */}
  </div>
</div>
```

**Product Image:**
- 64×64px rounded thumbnail
- Placeholder: `📦` emoji
- Hover: Slight scale effect (via parent)

**Product Info:**
- Product name (line-clamp-1)
- Store badge: `🟦 AROMA` (colored pill)
- Source emoji: Instagram `🎵`, Store `🏪`

**Price Display:**
- Hidden on mobile (`hidden sm:flex`)
- Per-store grid: 3-4 columns
- Best price highlighted: `bg-emerald-500/30 border-emerald-400`

**Best Price + Wishlist:**
- Large bold price: `text-xl font-bold text-emerald-300`
- Label: "Найдешевше"
- Wishlist toggle: Heart emoji `❤️` / `🤍`

### **6. Products Grid/List**
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {products.map((product) => (
    <ProductCard key={product.id} product={product} />
  ))}
</div>
```
- Responsive: 1 col mobile, 2 tablet, 3 desktop
- Gap: 1rem between cards
- Maintains aspect ratio

### **7. Empty State**
```jsx
<div className="text-center py-12">
  <p className="text-emerald-200">{t('noData')}</p>
</div>
```
- Centered text
- Ample padding
- Subtle color

### **8. Loading State**
```jsx
<div className="flex justify-center items-center py-12">
  <div className="animate-spin w-8 h-8 border-4 border-emerald-500 
                  border-t-transparent rounded-full" />
  <p className="text-emerald-200 ml-3">{t('loading')}</p>
</div>
```
- Spinner animation (CSS `animate-spin`)
- Loading text beside

### **9. Footer**
```jsx
<footer className="bg-black/30 backdrop-blur-sm border-t border-white/10 py-8">
  <div className="text-center text-emerald-200 text-sm">
    <p>© 2026 {t('app.name')}. All rights reserved.</p>
  </div>
</footer>
```
- Minimal, centered
- Translucent background
- Subtle border

---

## ✨ Interactive Elements

### **Transitions**
```css
transition-all duration-300
transition-colors duration-200
```

### **Hover States**
- **Cards**: `bg-white/10` + `border-emerald-400/50` + shadow glow
- **Buttons**: Color shift + slight scale
- **Links**: Text color brightens

### **Focus States**
- Inputs: Border color to emerald
- Buttons: Outline removed, relies on background

### **Animations**
1. **Pulse** (animated orbs in background):
   ```css
   opacity-10 blur-3d (static background elements)
   ```

2. **Spin** (loading spinner):
   ```css
   @keyframes spin {
     0% { transform: rotate(0deg); }
     100% { transform: rotate(360deg); }
   }
   animation: spin 1s linear infinite;
   ```

3. **Fade-in** (page load): Natural with Next.js

---

## 📱 Responsive Breakpoints

| **Breakpoint** | **Width** | **Changes** |
|---|---|---|
| **Mobile** | < 640px | Full-width, 1-col grid, hidden price columns |
| **Tablet** | 640px–1024px | 2-col grid, show price summary |
| **Desktop** | > 1024px | 3-col grid, full price display |

**Key Tailwind Classes:**
- `hidden sm:flex` — Hide on mobile, show on tablet+
- `md:text-6xl` — Responsive text sizes
- `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` — Responsive grid

---

## 🌍 Multi-Language Support

**Supported Languages:**
- 🇺🇦 **Ukrainian** (ukr)
- 🇷🇺 **Russian** (rus)
- 🇲🇪 **Montenegrin** (mne)

**URL Structure:** `/[lang]/` (e.g., `/rus`, `/ukr`, `/mne`)

**Translation Keys:**
```javascript
{
  "app": {
    "name": "Monte-Shop-Price",
    "description": "Real-time price comparison..."
  },
  "header": { "search", "language", "menu" },
  "search": { "placeholder", "button", "results", "noResults" },
  "tabs": { "instagram", "official", "all" },
  "stores": { "aroma", "voli", "hdl", "idea" },
  "price": { "min", "max", "currency": "EUR", "cheapest", "priceHistory" },
  "products": { "name", "price", "store", "updated", "addToWishlist" },
  "trending": { "title": "Популярные товары", "subtitle": "Последние обновления" },
  "filters": { "byPrice", "byStore", "byCheapest" },
  "errors": { "loading", "search", "network" },
  "loading": "Загрузка...",
  "noData": "Нет данных"
}
```

---

## 🛍️ Mock Data

**6 Demo Products:**
```javascript
{
  id: "mock_001",
  name: "Млеко 1L",
  description: "Свежее молоко от Aroma",
  image_url: "https://via.placeholder.com/150?text=Milk",
  source: "aroma",
  current_prices: { "aroma": 1.49 },
  min_price: 1.49,
  cheapest_store: "aroma",
  updated_at: "2026-06-16T12:00:00"
}
```

**Stores:**
- 🏪 Aroma
- 🏪 Voli
- 🏪 HDL
- 🏪 IDEA

**Price Range:** €1.49 – €7.49

---

## 📡 API Endpoints

### **Backend (FastAPI on port 8001)**
```
GET  /health                              — Health check
GET  /api/v1/search/mock?q={query}       — Mock products
GET  /api/v1/search/trending?hours=24    — Trending (fallback to mock)
GET  /api/v1/search/products?q={query}   — Full search (when DB has data)
```

### **Frontend Calls**
- `TrendingProducts`: `GET /api/v1/search/mock?q=`
- `PriceMatrix`: `GET /api/v1/search/products?q={query}`
- `TabSwitcher`: Filters by `source` parameter (not yet connected)

---

## 🚀 Performance Optimizations

### **Frontend**
- Dynamic imports for components (code splitting)
- Image optimization (Next/Image)
- CSS purging (Tailwind production build)
- Debounced search (500ms)

### **Backend**
- Mock data fallback (no DB dependency)
- Health check endpoint
- CORS configured for localhost:3001

---

## 📝 Accessibility

### **WCAG AA Compliance**
- ✅ Color contrast: All text meets minimum ratio
- ✅ Focus indicators: Visible on all interactive elements
- ✅ Keyboard navigation: Tab through all controls
- ✅ Semantic HTML: Proper heading hierarchy, labels

### **Dark Mode**
- Default dark theme (no light mode toggle yet)
- High contrast for readability
- Reduced eye strain (evening use)

---

## 📦 File Structure

```
Insta-data/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css          ← Base styles
│   │   │   ├── [lang]/
│   │   │   │   ├── page.tsx         ← Hero + products
│   │   │   │   └── layout.tsx       ← i18n wrapper
│   │   │   └── favicon.ico
│   │   ├── components/
│   │   │   ├── Header.tsx           ← Nav + logo
│   │   │   ├── SearchBar.tsx        ← Search input
│   │   │   ├── TabSwitcher.tsx      ← Filter tabs
│   │   │   ├── PriceMatrix.tsx      ← Products list
│   │   │   ├── ProductCard.tsx      ← Single product row
│   │   │   └── TrendingProducts.tsx ← Grid view
│   │   ├── lib/
│   │   │   └── i18n.ts             ← next-intl config
│   │   └── locales/
│   │       ├── ukr.json            ← Ukrainian
│   │       ├── rus.json            ← Russian
│   │       └── mne.json            ← Montenegrin
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── main.py                 ← FastAPI app
│   │   ├── core/
│   │   │   └── config.py           ← Settings, CORS
│   │   ├── api/v1/
│   │   │   ├── router.py
│   │   │   └── endpoints/
│   │   │       └── search.py       ← Mock + real endpoints
│   │   ├── database/
│   │   │   ├── mongodb.py
│   │   │   └── postgres.py
│   │   └── services/
│   │       └── search_service.py
│   ├── requirements.txt
│   └── .env.example
│
└── DESIGN_EXTRACT.md (this file)
```

---

## 🎯 Key Design Decisions

### **Color Scheme**
- **Why Emerald + Cyan?** Montenegro = mountains (green) + sea (cyan)
- **Why Gradient?** Visual depth, modern aesthetic
- **Why Dark Background?** Natural grocery shopping context (stores are lit), also evening browsing

### **Typography**
- **Why Large Headings?** Eye-catching, clear hierarchy
- **Why Sans-serif?** Modern, clean, readable on screens
- **Why Drop Shadows?** Text clarity over gradient background

### **Layout**
- **Why Sidebar Removed?** Focus on products, not filters (MVP)
- **Why Cards Row Layout?** Easier comparison of prices per product
- **Why Centered Hero?** Clear primary action (search)

### **Interactions**
- **Why Hover Effects?** Visual feedback without page reload
- **Why Backdrop Blur?** Glassmorphism trend, modern feel
- **Why Emoji Icons?** Quick visual recognition, international

---

## 🔄 State Management

| **State** | **Type** | **Scope** | **Storage** |
|-----------|---------|----------|-----------|
| `lang` | String | URL param | `[lang]/` route |
| `query` | String | URL param | `?q=` query string |
| `activeTab` | String | Local state | Memory (TabSwitcher) |
| `products` | Array | Local state | Memory (PriceMatrix) |
| `isLoading` | Boolean | Local state | Memory |
| `isWishlisted` | Boolean | Local state | Memory (per card) |

---

## 🔐 Security & Privacy

- ✅ HTTPS ready (Vercel deployment)
- ✅ No API keys exposed in frontend code
- ✅ CORS configured (`http://localhost:3001` allowed)
- ✅ No user data collection (MVP)
- ✅ Mock data only (no real PII)

---

## 📊 SEO & Meta Tags

**Page Title:** "Monte-Shop-Price — Real-time Price Comparison for Montenegrin Grocery Stores"

**Meta Description:** "Find the best prices for grocery products in Montenegro. Compare prices across Aroma, Voli, HDL, IDEA stores instantly."

**OG Tags:**
- `og:title`: "Monte-Shop-Price"
- `og:description`: "Real-time price comparison..."
- `og:image`: Mountain + sea backdrop (1200×630px)
- `og:url`: `https://monteshopprice.com/[lang]`

---

## 🚀 Deployment

### **Frontend (Vercel)**
```bash
npm run build
# Deploys to monteshopprice.vercel.app
```

### **Backend (Hetzner / Local)**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### **Environment Variables**
```env
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001

# Backend
DATABASE_URL=mongodb://localhost:27017/monteshop
POSTGRES_URL=postgresql://...
CORS_ORIGINS=["http://localhost:3001", "https://monteshopprice.vercel.app"]
```

---

## 📞 Design Support & Updates

To add/modify components:
1. Update this DESIGN_EXTRACT.md
2. Create/edit component in `/src/components/`
3. Add Tailwind utilities to `globals.css` if custom
4. Test on mobile (640px), tablet (1024px), desktop
5. Push to GitHub

---

**Last Updated:** 2026-06-20  
**Design System Version:** 1.0.0  
**Status:** Phase 1 ✅ (Beautiful UI complete, API integration ready)
