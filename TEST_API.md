# 🧪 API TESTING GUIDE

**Тестування API та запуск Aroma scraper'а**

---

## 📋 Передумови

### 1. Docker повинен бути запущений

```powershell
# Перевірити статус Docker
docker ps

# Якщо не запущений - запустити Docker Desktop
# (Шукайте в Windows меню "Docker Desktop")
```

### 2. Сервіси повинні бути запущені

```powershell
cd "C:\Users\Serhii\OneDrive\Рабочий стол\Insta-data"

# Запустити
docker-compose up -d

# Чекати 30 сек
Start-Sleep -Seconds 30

# Перевірити
docker-compose ps
```

**Всі сервіси повинні мати статус "Up"**

---

## 🧪 КРОК 1: Тестування API (Unit Tests)

### Запустити тести
```powershell
# Увійти в backend контейнер
docker exec -it insta-data-backend bash

# Всередині контейнера:
pytest tests/unit/ -v

# Або з coverage:
pytest tests/unit/ --cov=app --cov-report=term-missing
```

### Очікуваний результат
```
===== test session starts =====
tests/unit/test_product_service.py::test_... PASSED
tests/unit/test_price_extractor.py::test_... PASSED
...
===== 65 passed in 2.34s =====
```

---

## 🌐 КРОК 2: Тестування API Endpoints (Interactive)

### Відкрити Swagger UI
```
http://localhost:8001/docs
```

### Перевірити здоров'я API
```powershell
curl -X GET "http://localhost:8001/api/v1/status"
```

**Очікуваний відповідь:**
```json
{"status":"ok","version":"0.1.0"}
```

---

### Тест 1: Пошук (без даних - OK)
```powershell
curl -X GET "http://localhost:8001/api/v1/search/products?q=млеко" | ConvertFrom-Json | ConvertTo-Json
```

**Результат:**
```json
{
  "query": "млеко",
  "count": 0,
  "results": [],
  "source_filter": null
}
```

✅ **OK** - Це нормально (БД ще порожня)

---

### Тест 2: Статистика
```powershell
curl -X GET "http://localhost:8001/api/v1/search/stats" | ConvertFrom-Json | ConvertTo-Json
```

**Результат:**
```json
{
  "total_products": 0,
  "by_source": {
    "instagram": 0,
    "aroma": 0,
    "voli": 0,
    "hdl": 0,
    "idea": 0
  },
  "most_expensive": null,
  "cheapest": null
}
```

✅ **OK** - БД порожня

---

### Тест 3: Scraper Status
```powershell
curl -X GET "http://localhost:8001/api/v1/scrapers/status" | ConvertFrom-Json | ConvertTo-Json
```

**Результат:**
```json
{
  "scrapers": {
    "instagram": {"status": "ready", "last_run": null},
    "aroma": {"status": "ready", "last_run": null},
    "voli": {"status": "ready", "last_run": null},
    "hdl": {"status": "ready", "last_run": null},
    "idea": {"status": "ready", "last_run": null}
  },
  "scheduler_running": true,
  "timestamp": "2026-06-16T12:00:00"
}
```

✅ **OK** - Всі скрейпери готові

---

## 🔪 КРОК 3: Запустити Aroma Scraper

### Команда
```powershell
$body = @{ store = "aroma" } | ConvertTo-Json

curl -X POST "http://localhost:8001/api/v1/scrapers/run" `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body | ConvertFrom-Json | ConvertTo-Json
```

### Очікуваний результат (через 2-3 хвилини)
```json
{
  "store": "aroma",
  "status": "success",
  "products_found": 145,
  "products_saved": 135,
  "error": null,
  "duration_seconds": 120.5
}
```

### ⏱️ Час виконання
- **Очікуваний:** 2-3 хвилини
- **В залежності від:** швидкості інтернету, Aroma сайту

---

## ✅ КРОК 4: Перевірити результати

### Знову запустити пошук
```powershell
curl -X GET "http://localhost:8001/api/v1/search/products?q=млеко" | ConvertFrom-Json | ConvertTo-Json
```

**Тепер результат:**
```json
{
  "query": "млеко",
  "count": 3,
  "results": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "Млеко 1L",
      "source": "aroma",
      "current_prices": {"aroma": 1.39},
      "min_price": 1.39,
      "cheapest_store": "aroma",
      ...
    }
  ]
}
```

✅ **УСПІХ** - Товари знайдені!

---

### Перевірити статистику
```powershell
curl -X GET "http://localhost:8001/api/v1/search/stats" | ConvertFrom-Json | ConvertTo-Json
```

**Результат:**
```json
{
  "total_products": 135,
  "by_source": {
    "aroma": 135,
    "voli": 0,
    ...
  },
  "most_expensive": 25.99,
  "cheapest": 0.99
}
```

✅ **УСПІХ** - 135 товарів від Aroma!

---

## 🚀 КРОК 5: Приєднати інші магазини

Якщо все OK з Aroma, запустимо по одному:

### Voli
```powershell
$body = @{ store = "voli" } | ConvertTo-Json
curl -X POST "http://localhost:8001/api/v1/scrapers/run" `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

### HDL
```powershell
$body = @{ store = "hdl" } | ConvertTo-Json
curl -X POST "http://localhost:8001/api/v1/scrapers/run" `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

### IDEA
```powershell
$body = @{ store = "idea" } | ConvertTo-Json
curl -X POST "http://localhost:8001/api/v1/scrapers/run" `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

---

## 📊 Очікувані Результати

### Після Aroma
```
total_products: 135
by_source: {aroma: 135}
```

### Після Aroma + Voli
```
total_products: 270 (±)
by_source: {aroma: 135, voli: 135}
```

### Після Всіх 4
```
total_products: 500+ (±)
by_source: {
  aroma: 135,
  voli: 140,
  hdl: 120,
  idea: 130
}
```

---

## 🔄 Повна автоматична версія

Якщо хочешь запустити всіх одразу (⚠️ довго ~15 хв):

```powershell
curl -X POST "http://localhost:8001/api/v1/scrapers/run-all" `
  -Headers @{"Content-Type"="application/json"}
```

---

## 📋 Checklist Успіху

- [ ] Docker запущений (`docker ps` = working)
- [ ] Сервіси запущені (`docker-compose ps` = all Up)
- [ ] API health OK (`/api/v1/status` = 200)
- [ ] Unit тести PASSED (`pytest tests/unit/` = all passed)
- [ ] Aroma scraper запущений (`/scrapers/run` aroma = success)
- [ ] Товари збережені (`/search/stats` = total_products > 0)
- [ ] Пошук працює (`/search/products?q=` = results > 0)
- [ ] Інші магазини приєднані (Voli, HDL, IDEA)

---

## 🐛 Troubleshooting

### ❌ "Connection refused"
```powershell
# Перевір Docker
docker-compose ps

# Перезапустити
docker-compose restart backend
```

### ❌ "404 Not Found"
```powershell
# Перевір URL (має бути :8001, не :8000)
curl -X GET "http://localhost:8001/api/v1/status"
```

### ❌ Aroma повертає 0 товарів
```powershell
# Перевір логи
docker-compose logs backend | tail -50

# Спробуй знову
curl -X POST "http://localhost:8001/api/v1/scrapers/run" `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"store":"aroma"}'
```

### ❌ Timeout під час скрейпингу
```powershell
# Просто чекай (Aroma медленний)
# Перевір статус черед 5 хв
curl -X GET "http://localhost:8001/api/v1/scrapers/status"
```

---

## 📊 Приклад Python Script для запуску

```python
import requests
import time

BASE_URL = "http://localhost:8001/api/v1"

def test_api():
    print("🧪 Testing API...")
    
    # 1. Health check
    r = requests.get(f"{BASE_URL}/status")
    print(f"✅ API Status: {r.status_code}")
    
    # 2. Run Aroma
    print("\n🔪 Running Aroma scraper...")
    r = requests.post(f"{BASE_URL}/scrapers/run", json={"store": "aroma"})
    result = r.json()
    print(f"Status: {result['status']}")
    print(f"Products found: {result.get('products_found', 0)}")
    print(f"Products saved: {result.get('products_saved', 0)}")
    
    # 3. Check stats
    print("\n📊 Checking stats...")
    r = requests.get(f"{BASE_URL}/search/stats")
    stats = r.json()
    print(f"Total products: {stats['total_products']}")
    print(f"By source: {stats['by_source']}")
    
    # 4. Search
    print("\n🔍 Testing search...")
    r = requests.get(f"{BASE_URL}/search/products?q=млеко")
    data = r.json()
    print(f"Found: {data['count']} products")
    if data['results']:
        print(f"First: {data['results'][0]['name']}")

if __name__ == "__main__":
    test_api()
```

---

## ✅ SUCCESS CHECKLIST

Коли все готово:

```
✅ API endpoints working
✅ Aroma scraper completed
✅ Products saved to MongoDB
✅ Search returning results
✅ Statistics updated
✅ Other stores ready to add
```

---

**Статус:** 🟢 READY FOR TESTING

Почни з КРОК 1! 🚀