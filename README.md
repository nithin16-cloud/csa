# CloudSky Airways — Flight Reservation & Cabin Management Platform

[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas_Cloud-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Engine-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **CloudSky Airways (CSA)** is an enterprise flight booking, aircraft seat allocation, and reservation management system built with Python and Flask. It features real-time flight search, interactive 3-class cabin seat selection with temporary holds, yield-management surge pricing, simulated payment settlement, self-service PNR web check-in, and **seamless dual database support (MongoDB Atlas & SQLite)**.

---

## 🌟 Key Features

### ✈️ 1. Passenger Booking & Discovery
* **Real-Time Flight Search**: Discover scheduled flights across major domestic and international hubs (DEL, BOM, BLR, HYD, MAA, CCU, DXB, SIN, LHR, JFK) by route and date.
* **Smart Route Fallback**: Gracefully suggests flights on alternative dates when specific queries yield no direct matches.
* **Interactive 3-Class Cabin Map**: Visual aircraft layout spanning **First Class** (lie-flat suites), **Business Class**, and **Economy Class** with live amenity indicators (seat pitch, power ports, recline angles).
* **Multi-Passenger Manifest**: Book single or group tickets with custom names, ages, and assigned cabin seats.
* **Checkout Simulation**: Generates an airline-standard 6-character PNR (e.g., `CS-9X4A8B`) and instant digital boarding passes.

### 🎫 2. Self-Service Management (`/manage`)
* **PNR Lookup**: Retrieve existing reservations using the unique PNR reference code and passenger email.
* **Live Seat Swap**: Switch seats before departure with real-time inventory reallocation.
* **Digital Web Check-in**: One-click flight check-in and boarding pass download.
* **Instant Cancellation & Refund**: Transparent cancellation fee deduction with automated simulated refunds.

### 📈 3. Dynamic Pricing & Concurrency Locks
* **Yield Management Pricing**: Automatically applies surge pricing based on flight occupancy tiers (<30% standard, 30–60% limited, 60–85% filling fast, ≥85% high demand).
* **Double-Booking Prevention**: Optimistic concurrency locks with an automated 5-minute seat hold window to prevent duplicate bookings during checkout.

### 🔄 4. Dual Database Architecture
* **MongoDB Atlas (Cloud)**: Full native document store with collections for `airports`, `flights`, `seats`, `users`, `bookings`, and `payments`.
* **SQLite (Local Fallback)**: Zero-configuration local database with Write-Ahead Logging (WAL) and foreign keys.

---

## 📁 Project Structure

```plaintext
csa/
├── app/
│   ├── routes/
│   │   ├── __init__.py        # Blueprint declarations
│   │   ├── api.py             # REST API: seat holds, bookings, cancellations, check-in
│   │   ├── auth.py            # Authentication, registration, login & profile sessions
│   │   └── main.py            # Controllers: flight search, booking view, user dashboard
│   ├── static/
│   │   └── css/
│   │       └── style.css      # Airline design system with light/dark theme support
│   ├── templates/
│   │   ├── auth/              # Sign-in & registration views
│   │   ├── errors/            # 404 & 500 error pages
│   │   ├── base.html          # Global layout shell & navigation
│   │   ├── booking.html       # Interactive 3-class cabin seat selection & checkout
│   │   ├── dashboard.html     # Passenger booking history & profile statistics
│   │   ├── flights.html       # Flight search results & filters
│   │   ├── index.html         # Hero landing page & featured routes
│   │   ├── info.html          # Baggage rules, dining, and airline policies
│   │   └── manage.html        # PNR lookup, web check-in & seat swap portal
│   ├── __init__.py            # Application factory, security headers & error handlers
│   ├── config.py              # Environment configuration loader
│   ├── db.py                  # Database engine switcher (MongoDB / SQLite)
│   ├── mongo.py               # MongoDB Atlas driver & collections adapter
│   ├── schema.sql             # Relational database schema
│   └── seed.py                # Pre-populated airports, flights, and cabin layouts
├── .dockerignore              # Docker build exclusions
├── .env                       # Active environment variables (git-ignored)
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── Dockerfile                 # Production Docker container specification
├── requirements.txt           # Python application dependencies
├── run.py                     # Development server entry point
└── wsgi.py                    # Production WSGI entry point
```

---

## 🚀 Getting Started

### 1. Setup Environment
```powershell
# Clone the repository
git clone https://github.com/nithin16-cloud/csa.git
cd csa

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Database (`.env`)
Copy the template to create your `.env` file:
```powershell
Copy-Item .env.example .env
```

Set your database in `.env`:

#### Option A: MongoDB Atlas (Cloud)
```env
DB_TYPE=mongodb
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.xxxx.mongodb.net/cloudsky?retryWrites=true&w=majority
MONGO_DB_NAME=cloudsky
```

#### Option B: SQLite (Local)
```env
DB_TYPE=sqlite
DATABASE_PATH=cloudsky.db
```

### 3. Launch the Server
```powershell
python run.py
```
Open your browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

*(The application automatically connects, verifies collections, and seeds flight data on first startup!)*

---

## 🔑 Demo Account Credentials

| Role | Username / PNR | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **Registered User** | `rohan.sharma@example.in` | `Password@123` | Booking history, flight dashboard, profile analytics |
| **Guest Passenger** | Valid PNR (e.g. `CS-XXXXXX`) | *Not required* | Web check-in, seat reassignment, automated cancellations |

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health and database engine status |
| `GET` | `/api/airports` | List all serviced airport destinations |
| `GET` | `/api/flights` | Search flight schedules with dynamic surge fares |
| `GET` | `/api/flights/<id>/seats` | Get cabin layout and seat availability |
| `POST` | `/api/seats/lock` | Place a 5-minute temporary hold on chosen seats |
| `POST` | `/api/bookings` | Finalize booking, process payment & generate PNR |
| `GET` | `/api/bookings/<pnr>` | Retrieve booking details and passenger manifest |
| `POST` | `/api/bookings/<pnr>/checkin` | Perform digital web check-in |
| `POST` | `/api/bookings/<pnr>/cancel` | Cancel reservation and compute automated refund |
| `POST` | `/api/bookings/<pnr>/change-seat` | Change seat selection prior to departure |

---

## 🛠️ CLI Database Commands

Manage your database directly from the terminal:

```bash
# Seed or re-seed airports, flights, and cabin seats
flask --app run.py seed-db

# Reset database to a clean state
flask --app run.py init-db

# List all registered users
flask --app run.py list-users
```

---

## 🐳 Docker Deployment

Run CloudSky in a containerized production environment:

```bash
# Build the Docker image
docker build -t cloudsky-airways:latest .

# Run container
docker run -d -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY="your-secret-key" \
  cloudsky-airways:latest
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
