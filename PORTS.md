# PORTS Reserved — Insta-data Project

**Оновлено:** 2026-07-02 (Phase 3 complete - actual ports documented)

---

## 📍 Зарезервовані Портови

| Service | Port | Protocol | Mode | Status | Notes |
|---------|------|----------|------|--------|-------|
| **Frontend (Dev)** | **3000** | HTTP | Local npm run dev | ✅ Active | Next.js 15 dev server (localhost:3000) |
| **Frontend (Docker)** | **3003** | HTTP | Docker Compose | ✅ Reserved | Next.js 15 (localhost:3003) |
| **Backend API (Dev)** | **8000** | HTTP | Local uvicorn | ✅ Active | FastAPI dev server (localhost:8000) |
| **Backend API (Docker)** | **8001** | HTTP | Docker Compose | ✅ Reserved | FastAPI (localhost:8001) |
| **MongoDB** | **27017** | TCP | Local | ✅ Reserved | NoSQL database |
| **PostgreSQL** | **5432** | TCP | Local | ✅ Reserved | History & analytics DB |
| **Redis** | **6379** | TCP | Local | ✅ Reserved | Cache layer |
| **Nginx** | **80** | HTTP | Production | ⏳ Future | Reverse proxy (prod only) |
| **Nginx SSL** | **443** | HTTPS | Production | ⏳ Future | TLS termination (prod only) |

---

## 🚀 Development Environment Setup

### Local (Non-Docker)
```bash
# Frontend dev server
cd frontend
npm run dev
# → http://localhost:3000  (Next.js default)
# ⚠️  Use 3001 after docker-compose up

# Backend dev server
cd backend
python -m venv venv
source venv/Scripts/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000  (local Python server)
```

### Docker Development
```bash
# Start all services
docker-compose up -d

# Access via reserved ports:
# Frontend:  http://localhost:3001  ← Use this!
# Backend:   http://localhost:8001  ← Use this!
# MongoDB:   localhost:27017
# PostgreSQL: localhost:5432
# Redis:     localhost:6379
# API Docs:  http://localhost:8001/docs
```

---

## ⚠️ Important Rules

### 1️⃣ Port Usage Rules
**For Local Development (Recommended):**
- ✅ DO use 3000 for frontend (npm run dev)
- ✅ DO use 8000 for backend (uvicorn)
- Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in frontend/.env.local

**For Docker Compose:**
- ✅ DO use 3003 for frontend (mapped from 3000)
- ✅ DO use 8001 for backend (mapped from 8000)
- Set `NEXT_PUBLIC_API_URL=http://localhost:8001` in frontend/.env.local

### 2️⃣ Port Conflicts Troubleshooting

**Error: "Port 3001 already in use"**
```bash
# Find what's using port 3001
lsof -i :3001          # Mac/Linux
netstat -ano | findstr :3001  # Windows PowerShell

# Kill process (be careful!)
kill -9 <PID>          # Mac/Linux
taskkill /PID <PID>   # Windows
```

**Error: "Port 5432 already in use" (PostgreSQL)**
```bash
# Stop Docker PostgreSQL
docker-compose down

# Or start on different port:
docker-compose up -d -p 5433:5432 postgres
```

### 3️⃣ Environment Variables

Update `.env` files with reserved ports:

**backend/.env**
```
DATABASE_URL=postgresql://user:pass@localhost:5432/insta_data
REDIS_URL=redis://localhost:6379/0
MONGODB_URL=mongodb://localhost:27017/insta_data
```

**frontend/.env.local**
```
NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
```

---

## 🐳 Docker Compose Ports Configuration

```yaml
# docker-compose.yml
services:
  frontend:
    ports:
      - "3001:3000"        # Reserve 3001 for Next.js
  
  backend:
    ports:
      - "8001:8000"        # Reserve 8001 for FastAPI
  
  mongo:
    ports:
      - "27017:27017"      # MongoDB default
  
  postgres:
    ports:
      - "5432:5432"        # PostgreSQL default
  
  redis:
    ports:
      - "6379:6379"        # Redis default
```

---

## 📊 Port Usage by Phase

### Phase 0-1 (Current - Frontend + Basic Backend)
- ✅ 3001 (Frontend)
- ✅ 8001 (Backend API)
- ✅ 27017 (MongoDB)
- ✅ 5432 (PostgreSQL)

### Phase 2+ (Web Scrapers)
- ✅ 3001, 8001, 27017, 5432 (unchanged)
- ⏳ 6379 (Redis cache - if added)

### Production (Future)
- ✅ 80 (HTTP)
- ✅ 443 (HTTPS)
- ✅ 27017, 5432 (private network)

---

## 🔐 Security Notes

**Development Ports (Local Only)**
- Ports 3001, 8001, 27017, 5432, 6379 exposed only to localhost
- Add firewall rules for production
- Use environment variables for sensitive config

**Production Ports**
- Only 80/443 exposed publicly
- MongoDB/PostgreSQL on private network only
- Use Docker secrets or environment variables

---

## ✅ Checklist

- [x] Reserve ports 3001 (frontend), 8001 (backend)
- [x] Document port assignments in PORTS.md
- [x] Update docker-compose.yml with port mappings
- [ ] Update .env.example with DATABASE_URL using correct ports
- [ ] Update CI/CD workflows to use reserved ports
- [ ] Test all services with reserved ports
- [ ] Document in project README

---

**Last Updated:** 2026-06-30  
**Maintained By:** Serhii Riabko