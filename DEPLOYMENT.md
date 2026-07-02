# 🚀 Production Deployment Guide

**Target:** Hetzner VPS (root@138.199.204.107)  
**OS:** Linux (Ubuntu 20.04+)  
**Time Required:** ~1 hour

---

## 📋 Prerequisites

### Hetzner VPS Setup
- [ ] SSH access to VPS
- [ ] SSH key configured: `C:\Users\Serhii\.ssh\spacecode_hetzner`
- [ ] Public IP assigned
- [ ] Domain name (optional but recommended)

### Local Machine
- [ ] Git configured
- [ ] All code committed and pushed to `main` branch
- [ ] `.env` files with production credentials

---

## 🔧 Step 1: Connect to VPS

```bash
# SSH into VPS from PowerShell
ssh -i "C:\Users\Serhii\.ssh\spacecode_hetzner" root@138.199.204.107

# Expected prompt:
# root@hetzner:~#
```

---

## 📦 Step 2: Install Prerequisites

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# Install Nginx (reverse proxy)
sudo apt install -y nginx

# Install Git
sudo apt install -y git

# Install Supervisor (process manager)
sudo apt install -y supervisor
```

---

## 🗂️ Step 3: Setup Project Directory

```bash
# Create deployment directory
sudo mkdir -p /home/deploy/apps
cd /home/deploy/apps

# Clone repository
sudo git clone https://github.com/SerhiiRiabko/insta-data.git

# Change ownership
sudo chown -R $USER:$USER /home/deploy/apps

cd insta-data
```

---

## 🔐 Step 4: Configure Environment

```bash
# Copy .env templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env with production values
nano backend/.env
```

**Update for production:**
```env
# Instagram credentials
INSTAGRAM_EMAIL=Niobium_Runas
INSTAGRAM_PASSWORD=your_actual_password

# Database passwords (change from defaults!)
MONGODB_PASSWORD=strong_mongo_password_here
POSTGRES_PASSWORD=strong_postgres_password_here

# API configuration
SECRET_KEY=generate_new_production_secret
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=production

# Frontend API URL
NEXT_PUBLIC_API_URL=https://your-domain.com/api  # Or IP address

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Retention policies
PRICE_HISTORY_RETENTION_DAYS=365
```

**Save:** Ctrl+O, Enter, Ctrl+X

```bash
# Edit frontend/.env
nano frontend/.env
```

**Update:**
```env
NEXT_PUBLIC_API_URL=https://your-domain.com/api
NEXT_PUBLIC_ENVIRONMENT=production
```

---

## 🐳 Step 5: Build Docker Images

```bash
# From project root
cd /home/deploy/apps/insta-data

# Build images for production
docker-compose build

# Or build and push to registry (optional)
# docker build -t yourusername/insta-data-backend:1.0.0 backend/
# docker push yourusername/insta-data-backend:1.0.0
```

---

## 🚀 Step 6: Start Services

```bash
# Start all services in background
docker-compose up -d

# Wait 30 seconds
sleep 30

# Check status
docker-compose ps

# Verify all services are healthy
docker-compose logs --tail=20
```

---

## 🌐 Step 7: Configure Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/insta-data > /dev/null <<EOF
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com 138.199.204.107;

    # Redirect HTTP to HTTPS (optional)
    # return 301 https://\$server_name\$request_uri;

    # API Routes
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Swagger documentation
    location /docs {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
    }

    location /openapi.json {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/insta-data /etc/nginx/sites-enabled/insta-data

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable Nginx on boot
sudo systemctl enable nginx
```

---

## 🔒 Step 8: Setup SSL/HTTPS (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace your-domain.com)
sudo certbot certonly --nginx -d your-domain.com

# Update Nginx to use HTTPS
sudo tee /etc/nginx/sites-available/insta-data > /dev/null <<EOF
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # API Routes
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host \$host;
    }
}
EOF

# Restart Nginx
sudo systemctl restart nginx

# Setup auto-renewal
sudo systemctl enable certbot.timer
```

---

## 📊 Step 9: Setup Monitoring & Logging

```bash
# Create log directory
mkdir -p /home/deploy/apps/insta-data/logs

# Create supervisord config for process monitoring
sudo tee /etc/supervisor/conf.d/insta-data.conf > /dev/null <<EOF
[group:insta-data]
programs=backend,frontend,mongo,postgres,redis

[program:backend]
directory=/home/deploy/apps/insta-data
command=docker-compose start backend
autostart=true
autorestart=true
stderr_logfile=/var/log/insta-data/backend.err.log
stdout_logfile=/var/log/insta-data/backend.out.log

[program:frontend]
directory=/home/deploy/apps/insta-data
command=docker-compose start frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/insta-data/frontend.err.log
stdout_logfile=/var/log/insta-data/frontend.out.log
EOF

# Update supervisord
sudo supervisorctl reread
sudo supervisorctl update
```

---

## 🔄 Step 10: Setup Daily Backups

```bash
# Create backup script
sudo tee /home/deploy/backup.sh > /dev/null <<'EOF'
#!/bin/bash

BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/home/deploy/apps/insta-data"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup MongoDB
docker exec insta-data-mongo mongodump --uri="mongodb://admin:password@localhost:27017/" --out=$BACKUP_DIR/mongo_$DATE

# Backup PostgreSQL
docker exec insta-data-postgres pg_dump -U admin insta_data_history > $BACKUP_DIR/postgres_$DATE.sql

# Compress backups
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/mongo_$DATE $BACKUP_DIR/postgres_$DATE.sql

# Remove old backups (keep last 7 days)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed at $DATE"
EOF

# Make executable
sudo chmod +x /home/deploy/backup.sh

# Schedule daily backup (3 AM)
echo "0 3 * * * /home/deploy/backup.sh" | sudo crontab -
```

---

## ✅ Step 11: Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Expected: All services "Up"

# Test backend health
curl http://localhost:8000/api/v1/status
# Expected: {"status":"ok","version":"0.1.0"}

# Test frontend
curl http://localhost:3000
# Expected: HTML content starts with <!DOCTYPE html>

# Test Nginx reverse proxy
curl http://your-domain.com/api/v1/status
# Expected: {"status":"ok","version":"0.1.0"}

# Check logs for errors
docker-compose logs --tail=50
```

---

## 🛠️ Step 12: Setup Daily Scraper Job

The APScheduler in backend already runs at 06:00 UTC daily. To verify:

```bash
# Check backend logs for scraper runs
docker-compose logs backend | grep "Starting all scrapers"

# Manual trigger (testing)
curl -X POST http://localhost:8000/api/v1/scrapers/run-all

# Check scraper status
curl http://localhost:8000/api/v1/scrapers/status
```

---

## 📚 Post-Deployment

### Update DNS Records
If using domain name:
```
A Record: your-domain.com → 138.199.204.107
```

### Enable Firewall
```bash
# UFW (Uncomplicated Firewall)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Monitor Resources
```bash
# Check disk space
df -h

# Check memory usage
free -h

# Monitor Docker container usage
docker stats

# View system logs
tail -f /var/log/syslog
```

---

## 🔄 Deployment Updates

When pushing new code:

```bash
# On local machine
git add .
git commit -m "feat: add new feature"
git push origin main

# On VPS
cd /home/deploy/apps/insta-data
git pull origin main
docker-compose build
docker-compose up -d
docker-compose logs -f
```

---

## 🚨 Troubleshooting

### Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# View logs
docker-compose logs backend

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### High Memory Usage
```bash
# Check container stats
docker stats

# Reduce container resource limits in docker-compose.yml:
# Add: mem_limit: 512m
```

### Database Connection Errors
```bash
# Check MongoDB
docker exec insta-data-mongo mongosh -u admin -p password

# Check PostgreSQL
docker exec insta-data-postgres psql -U admin -c "SELECT 1;"
```

### SSL Certificate Issues
```bash
# Renew certificate
sudo certbot renew

# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

---

## 📊 Production Checklist

- [ ] Domain name registered and DNS configured
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Firewall configured (UFW)
- [ ] SSH key-only authentication (no passwords)
- [ ] Daily backups running
- [ ] Monitoring setup (disk, memory, logs)
- [ ] Update mechanism tested
- [ ] Rollback plan documented
- [ ] Database maintenance scheduled
- [ ] Log rotation configured

---

## 🎉 Deployment Complete!

Your application is now live at:
- **Frontend:** https://your-domain.com
- **API:** https://your-domain.com/api
- **Docs:** https://your-domain.com/docs

---

## 📞 Monitoring & Maintenance

### Weekly
- [ ] Check disk space
- [ ] Review error logs
- [ ] Test backup restoration

### Monthly
- [ ] Update system packages
- [ ] Review database growth
- [ ] Check API performance metrics

### Quarterly
- [ ] Security audit
- [ ] Database optimization
- [ ] Performance tuning

---

**Production deployment successful! 🚀**