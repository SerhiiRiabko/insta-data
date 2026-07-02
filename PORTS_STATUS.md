# 🔌 PORTS & SERVICES STATUS

**Updated:** 2026-06-16  
**Environment:** Windows 11 + Docker Desktop + MonteLand local dev

---

## 📊 Port Allocation

| Port | Service | Status | Container | Local Process | Notes |
|------|---------|--------|-----------|---------------|-------|
| **3000** | Node.js | 🟢 RUNNING | - | `node.exe` | **MonteLand frontend** (DO NOT TOUCH) |
| **3003** | Insta-data Frontend | 🟡 READY | `insta-data-frontend` | - | Docker maps 3003:3000 |
| **8000** | Python Local | 🟢 RUNNING | - | `python.exe` | Previous FastAPI (можна завершити) |
| **8001** | Insta-data Backend | 🟡 READY | `insta-data-backend` | - | Docker maps 8001:8000 |
| **27017** | MongoDB (Local) | 🟢 RUNNING | `insta-data-mongo` | - | Docker service (внутрішня мережа) |
| **5432** | PostgreSQL (Local) | 🟢 RUNNING | Both! | `postgres` | **LOCAL + Docker** (CONFLICT!) |
| **6379** | Redis | 🟡 READY | `insta-data-redis` | - | Docker service (внутрішня мережа) |

---

## ⚠️ PORT CONFLICTS DETECTED

### **5432 (PostgreSQL) — LOCAL + DOCKER**
```
Local: postgres.exe (Windows service)
Docker: insta-data-postgres container
```

**SOLUTION:**
```powershell
# Option 1: Stop local PostgreSQL
Stop-Service -Name PostgreSQL -Force

# Option 2: Map Docker PostgreSQL to different port
# Edit docker-compose.yml: ports: ["5433:5432"]
```

### **8000 (Python) — Old FastAPI**
```
Process: python.exe (PID 16024)
```

**SOLUTION:**
```powershell
# Find and kill old Python process
Stop-Process -ID 16024 -Force
# OR terminate cleanly
Get-Process python | Where-Object {$_.Name -eq "python"} | Stop-Process
```

---

## 🚀 Quick Start Commands

### Start Insta-data Docker Services
```powershell
cd "C:\Users\Serhii\OneDrive\Рабочий стол\Insta-data"

# Start all services
docker-compose up -d

# Wait 30 seconds for services to start
Start-Sleep -Seconds 30

# Check status
docker-compose ps
```

### Access Services

```
Frontend:    http://localhost:3003
Backend API: http://localhost:8001
API Docs:    http://localhost:8001/docs
Swagger:     http://localhost:8001/redoc
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Follow logs with timestamps
docker-compose logs -f --timestamps
```

### Stop Services
```powershell
# Stop all
docker-compose down

# Stop and remove volumes (careful!)
docker-compose down -v
```

---

## 🐳 Docker Network

**Network Name:** `insta-data-network`  
**Driver:** bridge  

**Internal Service Addresses:**
| Service | Address | Port |
|---------|---------|------|
| MongoDB | `mongo` | 27017 |
| PostgreSQL | `postgres` | 5432 |
| Redis | `redis` | 6379 |
| Backend | `backend` | 8000 |
| Frontend | `frontend` | 3000 |

**Frontend → Backend Communication:**
- Inside Docker: `http://backend:8000`
- From Host: `http://localhost:8001`

---

## 📝 Environment Variables

**Set in `.env` (not .env.example):**

```bash
# Core
ENVIRONMENT=development
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Databases
MONGODB_USER=admin
MONGODB_PASSWORD=testpass123
POSTGRES_USER=admin
POSTGRES_PASSWORD=testpass123

# Instagram (YOUR CREDENTIALS)
INSTAGRAM_EMAIL=Niobium_Runas
INSTAGRAM_PASSWORD=<your_actual_password>

# API
NEXT_PUBLIC_API_URL=http://localhost:8001  # ← Changed from 8000!

# Redis
REDIS_PASSWORD=redis_testpass
```

---

## 🔧 Troubleshooting

### Docker Services Won't Start
```powershell
# Check if Docker is running
docker ps

# If not, restart Docker Desktop or:
docker-compose restart
```

### Port Already in Use
```powershell
# Find process using port 8001
Get-NetTCPConnection -LocalPort 8001 | Select-Object OwningProcess

# Kill process (replace PID)
Stop-Process -ID <PID> -Force
```

### MongoDB Connection Error
```powershell
# Check if MongoDB is healthy
docker-compose ps mongo

# View logs
docker-compose logs mongo

# Restart
docker-compose restart mongo
```

### Frontend Not Loading (http://localhost:3003)
```powershell
# Check if Next.js is running
docker-compose ps frontend

# View logs
docker-compose logs -f frontend
# Look for: "started server on 0.0.0.0:3000"
```

---

## 📋 Checklist Before Starting Phase 1

- [ ] `.env` file created with real Instagram password
- [ ] Docker Desktop running (`docker ps` works)
- [ ] `docker-compose up -d` succeeded
- [ ] All services healthy: `docker-compose ps`
- [ ] Frontend loads: http://localhost:3003
- [ ] Backend responds: http://localhost:8001/docs
- [ ] MongoDB can be accessed (test in code)
- [ ] PostgreSQL ready (test in code)
- [ ] Old Python process killed (PID 16024)

---

## 📍 Files Modified This Session

1. **docker-compose.yml**
   - Changed backend: `"8000:8000"` → `"8001:8000"`
   - Changed frontend: `"3000:3000"` → `"3003:3000"`

2. **.env.example**
   - Added Docker port mapping note

3. **CLAUDE.md**
   - Updated local dev URLs to 3003/8001

4. **PLAN.md** (NEW)
   - Complete Phase 0-3 implementation plan

5. **PORTS_STATUS.md** (THIS FILE)
   - Port allocation & troubleshooting

---

**Next:** Start Phase 1: Instagram Parser POC