# ✈️ CloudSky Airways — Luxury Commercial Flight Simulator & Reservation System

[![CI/CD Pipeline](https://github.com/nithin16-cloud/csa/actions/workflows/ci.yml/badge.svg)](https://github.com/nithin16-cloud/csa/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Flask 3.x](https://img.shields.io/badge/Flask-3.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CloudSky Airways is a state-of-the-art commercial airline reservation and cabin simulator platform built with **Python/Flask 3.x**, **SQLite (WAL concurrency mode)**, and a **reactive Vue.js 3 frontend**.

---

## 📅 Complete 7-Day System Roadmap

| Day | Module | Features Delivered |
| :--- | :--- | :--- |
| **Day 1** | **Foundation & Schema** | Database architecture, SQL schemas, 10 domestic/international airports, realistic flight templates with INR pricing, and seeder engine. |
| **Day 2** | **Search & Concurrency** | Flight search engine, atomic seat locking, and transactional double-booking prevention under concurrent requests. |
| **Day 3** | **Multi-Passenger Engine** | Group/family passenger manifest (names, ages, genders), reactive flight schedule filters (price slider, departure time slots, aircraft fleet). |
| **Day 4** | **Interactive Cabin** | Full aircraft cabin layout (First, Business, Economy, Exit Row), rich amenity metadata (pitch, recline, USB-C/power), and 5-minute temporary seat hold countdown timers. |
| **Day 5** | **Payments & Boarding Passes** | Indian payment simulator (UPI, Cards, NetBanking), instant PNR generation (`CS-XXXXXX`), printable high-fidelity boarding pass with barcode, and trip self-service portal (check-in, seat modification, cancellation). |
| **Day 6** | **Authentication & Security** | User registration, password hashing (PBKDF2-SHA256), session state injection, and responsive user dropdown navigation. |
| **Day 7** | **Production & Deployment** | Multi-worker Gunicorn & Waitress WSGI servers, Docker containerization, health probes (`/health`), Render/Railway configs, and GitHub Actions CI/CD. |

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.11+
- Virtual environment (`.venv`)

### 2. Setup & Installation
```powershell
# Clone the repository
git clone https://github.com/nithin16-cloud/csa.git
cd csa

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
# (or on Linux / macOS: source .venv/bin/activate)

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application
```powershell
# Run with Flask development server
python run.py

# Or run with production WSGI server (Waitress on Windows)
python wsgi.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 🧪 Running Automated Tests

The test suite validates database concurrency, multi-passenger bookings, authentication security, and deployment health checks:

```powershell
.\.venv\Scripts\pytest -v
```

All **34 tests** run across:
- `tests/test_auth.py` — Registration, authentication, password mismatch, session handling.
- `tests/test_concurrency.py` — Multi-threaded seat hold race conditions & double-booking prevention.
- `tests/test_routes.py` — Flight search, multi-passenger booking engine, PNR lookups, check-in.
- `tests/test_deployment.py` — Production health checks (`/health`), security headers, WSGI entrypoint, and error handling.

---

## 🌐 Production Deployment Options

Full instructions are available in [DEPLOYMENT.md](./DEPLOYMENT.md).

### Option A: Render (Free Cloud Hosting)
Connect this repository to [Render](https://render.com) as a Web Service. Render automatically reads [`Procfile`](./Procfile), builds dependencies, auto-provisions SQLite database, and deploys automatically.

### Option B: Railway
Connect repository to [Railway](https://railway.app) using the included [`Procfile`](./Procfile).

### Option C: Docker Container
```bash
# Build and run with Docker Compose
docker compose up --build -d

# Check health probe
curl http://localhost:5000/health
```

---

## 🩺 System Health Monitoring

The platform includes an automated liveness & readiness health probe:

- **Endpoint:** `GET /health` or `GET /api/health`
- **Response Format (JSON):**
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

---

## 📁 Repository Structure

```text
csa/
├── .github/workflows/ci.yml # GitHub Actions CI/CD Pipeline
├── app/
│   ├── routes/              # Modular Flask Blueprints (main, api, auth)
│   ├── static/              # Luxury CSS stylesheets, branding, fonts
│   ├── templates/           # Jinja2 & Vue 3 templates (index, flights, booking, manage, errors)
│   ├── config.py            # Environment-aware configuration classes
│   ├── db.py                # SQLite WAL connection manager & migrations
│   ├── schema.sql           # Complete relational schema
│   └── seed.py              # Airports, routes, and cabin layout seeder
├── tests/                   # 34 Pytest unit & integration tests
├── Dockerfile               # Production container image definition
├── docker-compose.yml       # Production container orchestration
├── Procfile                 # Cloud WSGI process manager command
├── requirements.txt         # Pinned production dependencies
├── run.py                   # Local development server entrypoint
├── wsgi.py                  # Production WSGI application entrypoint
├── DEPLOYMENT.md            # Comprehensive production deployment guide
└── README.md                # Project documentation & architecture overview
```
