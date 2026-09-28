# CloudSky Airways — Day 7 Production Deployment Guide

This guide covers complete, production-ready deployment strategies for the **CloudSky Airways Flight Reservation & Commercial Airline Simulator**.

---

## 🚀 Architecture Overview

- **Framework:** Flask 3.x (Modular Blueprints architecture)
- **WSGI Production Servers:**
  - **Linux / Cloud:** `Gunicorn` (Multi-worker, multi-threaded)
  - **Windows:** `Waitress` (Pure Python high-performance production WSGI)
- **Database:** SQLite 3 with **WAL mode (Write-Ahead Logging)** enabled for high-concurrency read/write operations without reader/writer deadlocks.
- **Frontend:** Luxury Vanilla CSS + Vue.js 3 reactive cabin & search engine.
- **Zero-Touch Cold Start:** The application auto-detects and provisions missing tables and seeds flight schedules on initial boot.

---

## 📋 Environment Variables Reference

Duplicate `.env.example` to `.env` in production:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `FLASK_ENV` | `production` | Environment mode (`production`, `development`, `testing`) |
| `FLASK_DEBUG` | `0` | Debug mode (`0` for production, `1` for local development) |
| `PORT` | `5000` | HTTP port dynamically assigned by host (Render, Railway, Heroku) |
| `SECRET_KEY` | *(Required in prod)* | Cryptographically secure random key for session signing |
| `DATABASE_PATH` | `cloudsky.db` | Absolute or relative path to SQLite database file |
| `SESSION_COOKIE_SECURE` | `0` | Set to `1` when running behind HTTPS in production |

Generate a production `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## ☁️ Deployment Option 1: Render (Recommended Free Cloud)

The repository includes a ready-to-use [`Procfile`](./Procfile) and [`requirements.txt`](./requirements.txt).

1. Push your repository to **GitHub**.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** → **Web Service**.
4. Connect this repository. Render automatically detects Python and `Procfile`:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 wsgi:app`
   - **Health Check Path:** `/health`
5. Under Environment Variables, add `SECRET_KEY` and click **Create Web Service**.

---

## 🚂 Deployment Option 2: Railway

The repository uses standard [`Procfile`](./Procfile) detection.

1. Log into [Railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select this repository. Railway automatically detects `Procfile` and launches the Gunicorn WSGI server.
4. In Railway project settings, add the variable `SECRET_KEY`.
5. Under **Networking**, click **Generate Domain** to get a public URL.

---

## 🐳 Deployment Option 3: Docker & Docker Compose

### Using Docker Compose (Recommended for local / VPS containers)
```bash
# Build and start container in background with persistent volume
docker compose up --build -d

# View real-time logs
docker compose logs -f

# Check container health status
docker ps
```
The application will be accessible at `http://localhost:5000`. Database records are saved to the persistent volume `cloudsky_data`.

### Using Standalone Docker CLI
```bash
# 1. Build image
docker build -t cloudsky-airways:latest .

# 2. Run container
docker run -d \
  --name cloudsky \
  -p 5000:5000 \
  -e SECRET_KEY="your-production-secret-key" \
  -e FLASK_ENV="production" \
  cloudsky-airways:latest

# 3. Check health status
docker inspect --format='{{json .State.Health.Status}}' cloudsky
```

---

## 🐧 Deployment Option 4: Linux Ubuntu / Debian VPS (Nginx + Systemd)

### 1. System Setup
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx
git clone <your-repo-url> /var/www/csa
cd /var/www/csa

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Systemd Service
Create `/etc/systemd/system/cloudsky.service`:
```ini
[Unit]
Description=CloudSky Airways Flight Reservation WSGI Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/csa
Environment="PATH=/var/www/csa/.venv/bin"
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=your-production-secret-key-here"
Environment="DATABASE_PATH=/var/www/csa/cloudsky.db"
ExecStart=/var/www/csa/.venv/bin/gunicorn --workers 3 --threads 4 --bind 127.0.0.1:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudsky
sudo systemctl start cloudsky
```

### 3. Configure Nginx Reverse Proxy
Create `/etc/nginx/sites-available/cloudsky`:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location /static/ {
        alias /var/www/csa/app/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable site and install SSL certificate via Certbot:
```bash
sudo ln -s /etc/nginx/sites-available/cloudsky /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🪟 Deployment Option 5: Windows Server / Local Production

On Windows systems, production serving is handled by **Waitress**:
```powershell
.\.venv\Scripts\python wsgi.py
```
Waitress starts multi-threaded serving on `http://0.0.0.0:5000` without requiring external UNIX process managers.

---

## 🩺 Health Check & Monitoring

Cloud monitoring tools (UptimeRobot, AWS Route53, Render, Kubernetes) can probe:

- **Endpoint:** `GET /health` or `GET /api/health`
- **Healthy Response (HTTP 200):**
  ```json
  {
    "status": "healthy",
    "service": "CloudSky Airways Flight Reservation System",
    "version": "1.0.0",
    "environment": "production",
    "database": "connected",
    "timestamp": "2026-09-28T13:30:00.000000Z"
  }
  ```
- **Degraded Response (HTTP 503):** If database connection fails, returns HTTP 503 with `"status": "degraded"`.

---

## 🛡️ Security Verification Checklist

- [x] **CSRF / Cookie Flags:** `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"`.
- [x] **Security Headers:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`.
- [x] **Container Security:** Runs as non-root user `cloudsky` (UID 1001) in Docker.
- [x] **Custom Error Handlers:** 404 and 500 error pages for browsers, structured JSON for API callers.
- [x] **Concurrency Hardening:** SQLite WAL mode with 10s busy timeout preventing lock contention.
- [x] **CI/CD Automation:** GitHub Actions validates pytest tests and Docker builds on every push.
