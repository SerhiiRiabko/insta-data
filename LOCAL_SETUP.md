# 🚀 Local Development Setup Guide

**Platform:** Windows 11 + Docker Desktop  
**Time Required:** ~15 minutes

---

## ✅ Prerequisites

### Required
- [ ] Docker Desktop (or Docker Engine + Docker Compose)
  - **Download:** https://www.docker.com/products/docker-desktop
  - **Version:** 20.10+
  - **Status:** Must be running (check system tray)

- [ ] Git
  - **Download:** https://git-scm.com
  - **Or use:** Windows Subsystem for Linux (WSL2)

### Optional
- [ ] VS Code (for editing)
- [ ] Postman (for API testing)
- [ ] MongoDB Compass (for database browsing)

---

## 📋 Step-by-Step Setup

### Step 1: Verify Docker Installation

```powershell
# Check Docker version
docker --version
# Expected: Docker version 20.10+

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 2.0+

# Test Docker daemon
docker ps
# Expected: Empty container list (no errors)
```

If Docker isn't installed, download from: https://www.docker.com/products/docker-desktop

---

### Step 2: Clone Repository

```powershell
# Navigate to workspace
cd "C:\Users\Serhii\OneDrive\Рабочий стол"

# Clone repository (if not already cloned)
git clone https://github.com/SerhiiRiabko/insta-data.git
cd insta-data
```

Or if already on disk:
```powershell
cd "C:\Users\Serhii\OneDrive\Рабочий стол\Insta-data"
```

---

### Step 3: Setup Backend Configuration

```powershell
# Copy environment template
Copy-Item backend\.env.example backend\.env

# Edit .env with real Instagram credentials
notepad backend\.env
```

**Update these values in `backend/.env`:**
```env
# REQUIRED - Your actual Instagram account
INSTAGRAM_EMAIL=Niobium_Runas
INSTAGRAM_PASSWORD=your_actual_password_here  # ⚠️ IMPORTANT!

# Already set (can leave as-is)
SECRET_KEY=koTBD-OB_TqA0xShZ9VS81Oem1uP4sLbUPIcvM1Ubl0
MONGODB_PASSWORD=testpass123
POSTGRES_PASSWORD=testpass123
```

**Save file** (Ctrl+S)

---

### Step 4: Setup Frontend Configuration

```powershell
# Copy environment template
Copy-Item frontend\.env.example frontend\.env.local

# Edit .env.local (usually no changes needed for local dev)
notepad frontend\.env.local
```

**Expected content for Docker:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_NAME=Insta-Data
NEXT_PUBLIC_ENVIRONMENT=development
```

**Expected content for Local Dev (npm run dev):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Insta-Data
NEXT_PUBLIC_ENVIRONMENT=development
```

---

### Step 5: Start Docker Services

```powershell
# Navigate to project root
cd "C:\Users\Serhii\OneDrive\Рабочий стол\Insta-data"

# Start all services (background)
docker-compose up -d

# Expected output:
# Creating network "insta-data_default"
# Creating insta-data-mongo ...
# Creating insta-data-postgres ...
# Creating insta-data-redis ...
# Creating insta-data-backend ...
# Creating insta-data-frontend ...
```

---

### Step 6: Wait for Services to Start

```powershell
# Wait 30 seconds for everything to initialize
Start-Sleep -Seconds 30

# Check service status
docker-compose ps
```

**Expected status:**
```
NAME                COMMAND                  STATUS
insta-data-mongo       docker-entrypoint...   Up (healthy)
insta-data-postgres    docker-entrypoint...   Up (healthy)
insta-data-redis       docker-entrypoint...   Up
insta-data-backend     uvicorn main:app...    Up
insta-data-frontend    npm run dev            Up
```

---

### Step 7: Verify Backend Connection

```powershell
# Test backend health
Invoke-WebRequest -Uri http://localhost:8001/api/v1/status

# Expected response:
# StatusCode        : 200
# StatusDescription : OK
# Content           : {"status":"ok","version":"0.1.0"}
```

Or open in browser: http://localhost:8001/docs

---

### Step 8: Verify Frontend

**Docker Setup:**
```
http://localhost:3003
```

**Local Development (npm run dev):**
```
http://localhost:3000
```

**Expected:**
- Page loads with "Інста-Дані" header or hero with Kotor Bay photo
- Search bar visible
- No JavaScript errors in console
- Price matrix displays 67 products from 5 sources (if live endpoint working)

---

## 🌐 Access Services

### Frontend (React App)
```
Docker:     🌍 http://localhost:3003
Local Dev:  🌍 http://localhost:3000
```

- Search for products
- Switch languages (UKR/RUS/MNE)
- View trending products
- **Phase 3:** View live price comparison (67 products from 5 sources)

### Backend API Documentation
```
Docker:     📚 http://localhost:8001/docs
Local Dev:  📚 http://localhost:8000/docs
```

- Interactive Swagger UI
- Test API endpoints
- View request/response schemas

### API Endpoints (for testing)
```
# Search for products
GET http://localhost:8001/api/v1/search/products?q=млеко

# Get scrapers status
GET http://localhost:8001/api/v1/scrapers/status

# Get trending products
GET http://localhost:8001/api/v1/search/trending?hours=24&limit=10

# Run Instagram scraper
POST http://localhost:8001/api/v1/instagram/scrape
Body: {"username": "groceryprice_me", "hours_back": 48}
```

---

## 📊 View Databases

### MongoDB (via Docker)
```powershell
# Access MongoDB shell
docker exec -it insta-data-mongo mongosh -u admin -p testpass123

# List databases
show dbs

# Use insta_data database
use insta_data

# View products collection
db.products.find().limit(5)
```

### PostgreSQL (via Docker)
```powershell
# Access PostgreSQL shell
docker exec -it insta-data-postgres psql -U admin -d insta_data_history

# List tables
\dt

# View price_history
SELECT * FROM price_history LIMIT 5;

# Exit
\q
```

### Redis (via CLI)
```powershell
# Access Redis
docker exec -it insta-data-redis redis-cli

# Check cached searches
KEYS cache:search:*

# Get cache value
GET cache:search:млеко:all

# Exit
EXIT
```

---

## 🐛 Troubleshooting

### Problem: "Docker is not running"
```powershell
# Solution: Start Docker Desktop
# 1. Open Windows Start menu
# 2. Type "Docker Desktop"
# 3. Click to launch
# 4. Wait for "Docker is running" in system tray
```

### Problem: "Port 3003 already in use"
```powershell
# Find what's using port 3003
Get-NetTCPConnection -LocalPort 3003 | Select-Object OwningProcess

# Kill process (replace PID with actual number)
Stop-Process -ID <PID> -Force

# Or change port in docker-compose.yml:
# Change "3003:3000" to "3004:3000"
```

### Problem: "Port 8001 already in use"
```powershell
# Kill old Python process
Get-Process python | Where-Object {$_.MainWindowTitle -eq ""} | Stop-Process -Force

# Or change port in docker-compose.yml:
# Change "8001:8000" to "8002:8000"
```

### Problem: "Backend returns 502 Bad Gateway"
```powershell
# Check backend logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend

# Wait 5 seconds
Start-Sleep -Seconds 5

# Try again
Invoke-WebRequest -Uri http://localhost:8001/api/v1/status
```

### Problem: "Frontend stuck on loading"
```powershell
# Check frontend logs
docker-compose logs -f frontend

# Restart frontend
docker-compose restart frontend

# Clear browser cache (Ctrl+Shift+Delete)
# Refresh page (Ctrl+R or F5)
```

### Problem: "MongoDB connection error"
```powershell
# Check if MongoDB is healthy
docker-compose ps mongo

# View logs
docker-compose logs mongo

# Restart MongoDB
docker-compose restart mongo

# Wait 10 seconds for startup
Start-Sleep -Seconds 10
```

### Problem: "Can't access http://localhost:3003"
```powershell
# Verify frontend is running
docker-compose ps frontend

# Check if port is mapped correctly
# Should see: 3003->3000/tcp

# Try direct Docker access
docker exec insta-data-frontend curl -s http://localhost:3000 | head -10
```

---

## 📝 Common Commands

```powershell
# View all service logs
docker-compose logs

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongo

# Follow logs in real-time
docker-compose logs -f backend

# Stop all services
docker-compose stop

# Start all services
docker-compose start

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend

# View container stats (CPU, memory)
docker stats

# Remove all containers and volumes (CAREFUL!)
docker-compose down -v

# Remove only containers (keep volumes)
docker-compose down

# Rebuild images if changes made to Dockerfile
docker-compose build

# Rebuild and start
docker-compose up -d --build
```

---

## 🔄 Development Workflow

### 1. Make Changes to Backend Code

```powershell
# Edit Python files in backend/app/
notepad backend\app\services\product_service.py

# Changes are auto-reloaded (uvicorn --reload)
# No container restart needed
```

### 2. Make Changes to Frontend Code

```powershell
# Edit React/TypeScript files in frontend/src/
notepad frontend\src\components\SearchBar.tsx

# Changes are auto-reloaded (next dev)
# No container restart needed
```

### 3. Test API Changes

```powershell
# Option 1: Use Swagger UI
# http://localhost:8001/docs

# Option 2: Use PowerShell/curl
curl -X POST http://localhost:8001/api/v1/instagram/scrape `
  -H "Content-Type: application/json" `
  -d '{"username":"groceryprice_me","hours_back":48}'

# Option 3: Use Postman
# Import: http://localhost:8001/openapi.json
```

### 4. Run Backend Tests

```powershell
# Enter backend container
docker exec -it insta-data-backend bash

# Inside container:
pytest tests/unit/ -v

# Or from host (if Python installed):
cd backend
python -m pytest tests/unit/ -v
```

---

## 🛑 Shutdown

### Clean Stop
```powershell
# Stop all services gracefully
docker-compose stop

# Takes ~10 seconds
```

### Force Stop
```powershell
# Kill all services immediately
docker-compose down

# All data in volumes preserved
```

### Complete Cleanup (⚠️ Removes all data)
```powershell
# Remove containers + volumes + networks
docker-compose down -v

# ⚠️ This deletes all scraped data!
# Only use if resetting database
```

---

## 📞 Getting Help

### Check Service Status
```powershell
docker-compose ps
```

### View Recent Logs
```powershell
docker-compose logs --tail=50 backend
```

### Restart Specific Service
```powershell
docker-compose restart backend
```

### Test Backend Directly
```powershell
Invoke-WebRequest -Uri http://localhost:8001/api/v1/status -Verbose
```

### Inspect Network
```powershell
docker network inspect insta-data_default
```

---

## 📚 Next Steps

1. **Try Frontend Search:**
   - Navigate to http://localhost:3003
   - Type "млеко" in search
   - View results from different sources

2. **Test API Endpoints:**
   - Visit http://localhost:8001/docs
   - Click "Try it out" on endpoints
   - See request/response data

3. **Run Scrapers:**
   - POST to `/api/v1/scrapers/run-all`
   - Wait for completion (5-10 min)
   - Check results in search

4. **Check Databases:**
   - MongoDB: See products collection
   - PostgreSQL: See price_history table
   - Redis: Check cache keys

5. **Read Documentation:**
   - ARCHITECTURE.md — System design
   - PLAN.md — Implementation details
   - QUICK_REFERENCE.md — Quick lookup

---

## ⚡ Performance Notes

**Expected Performance (Local):**
- Page load: 1-2 seconds
- Search response: 100-500ms
- API response: 50-200ms
- First Instagram scrape: 2-5 minutes
- Daily full scan: 10-30 minutes

**If Slow:**
1. Check Docker resource limits
2. Verify network connectivity
3. Check database query performance
4. Review logs for errors

---

## 🎉 You're Ready!

Everything is set up and running. Start exploring:

- 🌍 Frontend: http://localhost:3003
- 📚 API Docs: http://localhost:8001/docs
- 💾 Databases: Docker containers

**Happy developing! 🚀**

---

**Questions?** Check PROJECT_STATUS.md or ARCHITECTURE.md for more details.