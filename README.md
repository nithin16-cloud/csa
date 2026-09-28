# ✈️ CloudSky Airways — Luxury Commercial Flight Simulator & Reservation System

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Flask 3.x](https://img.shields.io/badge/Flask-3.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CloudSky Airways is a commercial airline flight reservation and cabin simulator platform built with **Python/Flask 3.x**, **SQLite (WAL concurrency mode)**, and a **reactive Vue.js 3 frontend**.

---

## ✨ Features

- **Flight Search & Real-Time Filters:** Instant filtering by departure time, aircraft model, and ticket price.
- **Interactive Cabin Seat Map:** Visual aircraft cabin layouts (First, Business, Economy, Exit Row) with pitch, recline, power amenity details, and real-time temporary seat locks.
- **Multi-Passenger Booking Manifest:** Book individual or group tickets with passenger names, ages, and genders.
- **Zero Double-Booking Engine:** Transactional concurrency locking with automated expired-hold release.
- **Indian Payment Gateway Simulation:** Instant PNR generation (`CS-XXXXXX`), simulated Razorpay/UPI checkout, and printable boarding passes with barcode.
- **Passenger Self-Service Portal:** Manage bookings, change seats, cancel reservations with automated refunds, and complete web check-in.
- **Authentication & User Profiles:** Secure account registration, PBKDF2 password hashing, and user booking history.
- **Production Ready:** Health monitoring probes (`/health`), security headers, Gunicorn & Waitress WSGI integration, and Docker container support.

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

```powershell
.\.venv\Scripts\pytest -v
```

All **34 tests** validate concurrency, multi-passenger bookings, authentication security, and health checks across:
- `tests/test_auth.py`
- `tests/test_concurrency.py`
- `tests/test_routes.py`
- `tests/test_deployment.py`

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
├── Procfile                 # Cloud WSGI process manager command
├── requirements.txt         # Pinned production dependencies
├── run.py                   # Local development server entrypoint
├── wsgi.py                  # Production WSGI application entrypoint
└── README.md                # Project documentation & overview
```
