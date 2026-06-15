# Insta-data — Business Logic

## 📊 Бізнес Мета
Забезпечити користувачам **актуальну інформацію про ціни товарів харчування** в Чорногорії через інтеграцію Instagram (соціальні мережі) та офіційних сайтів магазинів, дозволяючи **швидко порівнювати ціни** і **отримувати найдешевші опції**.

---

## 👥 User Personas

### 1. **Знаходячи Покупець** 🏪
- **Профіль:** Звичайний покупець, що шукає найбільш вигідні пропозиції
- **Мотивація:** Заощадити гроші, знати актуальні ціни без обходу магазинів
- **Взаємодія:** Пошук товару → Порівняння цін → Вибір магазину

### 2. **Цінна Розвідка** 📈
- **Профіль:** Людина, що стежить за змінами цін, аналізує тренди
- **Мотивація:** Розуміти динаміку цін, знати найбільш/найменш дорогих періодів
- **Взаємодія:** Wishlist товарів → Моніторинг графіків → Аналіз истории

### 3. **Бізнес-користувач** 🤖 (Майбутній бот)
- **Профіль:** Інтеграція з власним ботом/системою
- **Мотивація:** Отримувати структуровані дані для свого продукту
- **Взаємодія:** API запити → Wishlist queries → Webhook'и на зміни цін

---

## 📖 User Stories

### **Feature: Переглядання Цін Товарів**

#### US-1: Переглядання матриці цін (Соціальні мережі)
```
As a: Знаходячий Покупець
I want to: Побачити товари з Instagram з цінами в усіх магазинах
So that: Я можу швидко порівняти, де найдешевше

AC (Acceptance Criteria):
1. На табі "📱 Соціальні мережі" показується таблиця:
   Рядки: Товари (з фото) з Instagram за останні 2 дні
   Стовпці: Aroma, Voli, HDL, IDEA, [найдешевша - ЗЕЛЕНА, інші - норм]
2. Найдешеваша ціна для кожного товару підсвічується ЗЕЛЕНИМ кольором
3. Якщо товару немає у магазині - показується "-"
4. Фото товару нормалізовано (один формат, один розмір)
5. Доступна для трьох мов (UKR, RUS, MNE)
```

#### US-2: Переглядання матриці цін (Офіційні сайти)
```
As a: Знаходячий Покупець
I want to: Побачити товари зі скреповитих офіційних сайтів з актуальними цінами
So that: Я знаю де найдешевше прямо з офіційного джерела

AC:
1. На табі "🏪 Офіційні сайти" показується таблиця цін від:
   - aromamarketi.me
   - voli.me
   - digitalniletak.me/hd-lakovic (HDL)
   - idea.co.me
2. Дані оновлюються щоденно в XX:XX (час TBD)
3. Найдешеваша ціна - ЗЕЛЕНА, найдорожча - червоно-підсвічена (або нейтральна)
4. Показується дата останнього оновлення
```

#### US-3: Пошук товару на табі
```
As a: Знаходячий Покупець
I want to: Ввести назву товару в пошукову строку
So that: Я можу швидко знайти його ціну

AC:
1. На кожній табі ("Соціальні мережі" + "Офіційні сайти") є пошукова строка вгорі
2. Пошук працює в реальному часі (по мірі друку)
3. Результати фільтруються по product_name (регістронезалежний)
4. Якщо товаров немає - "Товарів не знайдено"
5. Пошук відбувається на поточній мові (UKR/RUS/MNE)
```

---

### **Feature: Wishlist & Персональні Списки**

#### US-4: Створення Wishlist
```
As a: Цінна Розвідка
I want to: Додати товари в мій особистий список для моніторингу
So that: Я можу стежити за цінами на цікаві мені товари

AC:
1. На кожному товарі в матриці є кнопка "+ Додати в wishlist"
2. Wishlist зберігається локально у браузері (localStorage) або в аккаунті (якщо є auth)
3. Wishlist доступна з окремої сторінки "/wishlist"
4. На сторінці wishlist показується таблиця з товарами + цінами з обох табів
5. Можна видалити товар з wishlist
```

#### US-5: Завдання Списку Товарів для Пошуку
```
As a: Бізнес-користувач (Бот)
I want to: Надіслати список товарів, що мене цікавлять
So that: Я отримаю структуровані дані про ціни

Приклад запиту:
POST /api/v1/search/wishlist
{
  "products": ["Jaffa Biskvit", "Fanta 2L", "Mleko"],
  "language": "ukr",  // або rus, mne
  "source": "all"     // або instagram, official
}

Відповідь:
{
  "results": [
    {
      "product_name": "Jaffa Biskvit 150g",
      "image_url": "...",
      "prices": {
        "aroma": 1.39,
        "voli": 0.85,
        "hdl": 0.85,
        "idea": 1.49
      },
      "cheapest": { "store": "voli", "price": 0.85 }
    },
    ...
  ]
}
```

---

### **Feature: История Цін & Графіки**

#### US-6: Переглядання Графіка Цін
```
As a: Цінна Розвідка
I want to: Побачити графік зміни ціни товару за останні N днів/тижнів
So that: Я розумію тренд (зростає/падає/стабільна)

AC:
1. На кожному товарі є кнопка "📊 Графік" або клік на назву товару
2. Графік показує ціни за останні 7/14/30 днів (вибір користувачем)
3. Окремі лінії для кожного магазину (Aroma, Voli, HDL, IDEA)
4. Кольори: зелений (Aroma), синій (Voli), оранжевий (HDL), фіолетовий (IDEA)
5. Якщо ціна впала - позначається ЗЕЛЕНОЮ стрілкою ⬇️
6. Якщо ціна зросла - червоною ⬆️
```

#### US-7: Нотифікація про Зміну Цін
```
As a: Цінна Розвідка
I want to: Отримати сповіщення, коли ціна мого wishlist товару змінилася на 5%+
So that: Я знаю коли варто купувати

AC (FUTURE):
1. Email сповіщення: "Jaffa Biskvit впав на 15% в Voli!"
2. Webhook для бота: POST до webhook_url з даними зміни ціни
```

---

### **Feature: Мультимовність**

#### US-8: Перемикання Мови
```
As a: Будь-хто
I want to: Перемкнути мову з UKR → RUS → MNE
So that: Я розумію всі текст на своїй мові

AC:
1. На头部/footer є selector мови (випадаючий список або кнопки)
2. При виборі мови перезавантажується весь контент на новій мові
3. Мова зберігається в localStorage та URL параметрах (lang=ukr)
4. Всі назви магазинів, товарів, кнопок перекладаються
5. Дати показуються у форматі мови (укр: 15.06.2026, рус: 15.06.2026, мне: 15.06.2026)

Переклади:
- UKR (Українська) ← базова
- RUS (Російська)
- MNE (Чорногорська) ← локальна мова
```

---

## 🗂️ Функціональні Модулі

### **Backend (FastAPI)**

#### 1. **API Gateway** (`/api/v1/`)
```
Routes:
├── /prices/instagram         → GET товари з Instagram
├── /prices/official          → GET товари зі скреповитих сайтів
├── /prices/compare           → GET матриця товари × магазини
├── /prices/single/{product}  → GET ціни одного товару
├── /search?q=jaffa           → GET пошук товарів
├── /wishlist                 → GET/POST/DELETE wishlist
├── /history/{product}        → GET история цін для графіка
├── /health                   → GET статус сервісів
└── /webhook/price-change     → POST для бота (future)
```

#### 2. **Search Service**
```
- Full-text search у MongoDB на product_name
- Фільтри по магазинах, мовах, DateRange
- Aggregation pipeline для матриці цін
```

#### 3. **Price Tracker Service**
```
- Оновлення цін кожні N годин
- Порівняння з попередніми 3 версіями
- Вносення нових цін в SQL history (для графіків)
- Детекція аномалій (раптовий скачок цін)
```

#### 4. **Scraper Orchestrator**
```
- Запуск Instagram парсера щодня в XX:XX
- Запуск web scrapers для 4 магазинів паралельно
- Консолідація результатів в NoSQL
- Логування та error handling
```

### **Frontend (Next.js)**

#### 1. **Pages**
```
/ (index)               → Лендінг + матриця цін
/instagram              → Таб "Соціальні мережі"
/official               → Таб "Офіційні сайти"
/wishlist               → Мої товари
/product/[slug]         → Деталь товару + графік
/search?q=...           → Результати пошуку
```

#### 2. **Components**
```
PriceMatrix.tsx         → Таблиця товари × магазини × ціни
SearchBar.tsx           → Пошукова строка
WishlistButton.tsx      → +/- з wishlist
PriceChart.tsx          → Графік зміни цін (Chart.js / Recharts)
LanguageSelector.tsx    → UKR/RUS/MNE
StoreIcon.tsx           → Іконки магазинів
ResponsiveGrid.tsx      → Адаптивний layout (mobile-first)
```

#### 3. **Design System**
```
Colors:
- Primary Green:      #2D5016 (темно-зелений)
- Light Green:        #4CAF50 (світлий зелений - cheapest)
- Gold:               #D4AF37 (акцент)
- Dark Background:    #1A1A1A
- Text:               #FFFFFF / #E0E0E0

Animations:
- Price change: fade-in-out (0.3s)
- Hover effects: scale + shadow
- Tab switch: slide transition
- Wishlist add: heart animation
```

---

## 💾 Data Models

### **NoSQL (MongoDB)**

#### Collection: `products`
```json
{
  "_id": ObjectId,
  "product_name": "Jaffa Biskvit 150g",
  "slug": "jaffa-biskvit-150g",
  "image_url": "s3://bucket/jaffa-biskvit-150g.jpg",
  "image_normalized": true,
  "source": ["instagram", "official"], // або ['instagram'], ['official']
  "current_prices": {
    "aroma": 1.39,
    "voli": 0.85,
    "hdl": 0.85,
    "idea": 1.49
  },
  "price_history": [
    { "timestamp": "2026-06-15T14:00:00Z", "prices": {...} },
    { "timestamp": "2026-06-15T10:00:00Z", "prices": {...} },
    { "timestamp": "2026-06-14T14:00:00Z", "prices": {...} }
  ],
  "last_updated": "2026-06-15T14:35:22Z",
  "created_at": "2026-06-01T00:00:00Z"
}
```

#### Collection: `scraped_data`
```json
{
  "_id": ObjectId,
  "source": "instagram", // або official
  "raw_data": {...},      // Сирі дані з парсера
  "extracted_products": ["product_id_1", "product_id_2"],
  "timestamp": "2026-06-15T14:00:00Z"
}
```

#### Collection: `wishlist`
```json
{
  "_id": ObjectId,
  "user_id": "uuid", // або email, або анонімно (client_id)
  "product_ids": ["pid1", "pid2", "pid3"],
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": "2026-06-15T14:00:00Z"
}
```

### **SQL (PostgreSQL)**

#### Table: `price_history`
```sql
CREATE TABLE price_history (
  id SERIAL PRIMARY KEY,
  product_id VARCHAR(255) NOT NULL,
  store_name VARCHAR(100) NOT NULL,  -- aroma, voli, hdl, idea
  price DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'EUR',
  timestamp TIMESTAMP DEFAULT NOW(),
  UNIQUE(product_id, store_name, timestamp)
);
```

#### Table: `products_meta` (optional)
```sql
CREATE TABLE products_meta (
  product_id VARCHAR(255) PRIMARY KEY,
  product_name TEXT NOT NULL,
  first_seen TIMESTAMP DEFAULT NOW(),
  sources TEXT[], -- ['instagram', 'official']
  is_active BOOLEAN DEFAULT TRUE
);
```

---

## 🔄 Процеси & Workflows

### **Daily Price Update Workflow**
```
1. 🕐 [Scheduled] 08:00 UTC+1
   ↓
2. 📱 Instagram Parser запускається
   ├─ Логін в Instagram
   ├─ Пошук постів за 48 годин
   ├─ OCR + regex витяг товарів + цін
   └─ Збереження в `scraped_data`
   ↓
3. 🌐 Web Scrapers запускаються паралельно
   ├─ Aroma Scraper (Playwright)
   ├─ Voli Scraper (BeautifulSoup)
   ├─ HDL Scraper (BeautifulSoup)
   └─ IDEA Scraper (BeautifulSoup)
   ↓
4. 🔄 Merge & Deduplicate
   ├─ Консолідація з попередніх 3 версій (shift history)
   ├─ Дедублікація по product_name
   └─ Вноситися в `products` collection
   ↓
5. 📊 SQL History Update
   ├─ INSERT в `price_history` кожну нову ціну
   └─ Вичисляются тренди (↑/↓/→)
   ↓
6. 🔔 [Webhooks] Notify Subscribers
   └─ POST до webhook URLs з новими цінами (FUTURE)
```

### **User Search Workflow**
```
1. Користувач вводить "jaffa" в SearchBar
   ↓
2. GET /api/v1/search?q=jaffa&language=ukr&source=instagram
   ↓
3. Backend:
   ├─ MongoDB full-text search на `product_name` (регістронезалежний)
   ├─ Фільтруванням по `source`
   └─ Повертає 10-20 результатів
   ↓
4. Frontend отримує результати, показує в таблиці
   ↓
5. Користувач клікає на товар → /product/[slug] → Деталь + Графік
```

---

## 🎯 Success Metrics

| Метрика | Ціль | Як вимірюється |
|---------|------|--------|
| **Page Load** | < 2s | Lighthouse, user analytics |
| **Search** | < 100ms | Backend timing logs |
| **Price Accuracy** | 99% | Manual spot checks vs sites |
| **Mobile UX** | ≥ 95 CLS | Lighthouse PageSpeed |
| **Uptime** | ≥ 99% | StatusPage |
| **Data Freshness** | < 24h | `last_updated` timestamp |

---

## 🚀 Launch Checklist

- [ ] Instagram парсер готовий та тестований
- [ ] 4 web scrapers готові та тестовані
- [ ] Frontend матриця працює (UKR, RUS, MNE)
- [ ] Wishlist функціональність готова
- [ ] БД schema створена та мігрована
- [ ] Search API вирішена
- [ ] Mobile responsive протестована на 5+ пристроїв
- [ ] UI дизайн готовий (зелений + золото)
- [ ] Анімації додані
- [ ] CI/CD налаштований
- [ ] Помилки залогіровані та забезпечене відновлення
- [ ] Документація готова