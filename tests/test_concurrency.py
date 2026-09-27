import threading
import sqlite3
import pytest
from app import create_app
from app.config import Config

class TestConfig(Config):
    DATABASE_PATH = ":memory:"
    TESTING = True

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        from app.db import init_db
        from app.seed import seed_database
        init_db()
        seed_database()
    return app.test_client()

def test_prevent_double_booking_sequential():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        from app.db import get_db
        db = get_db()
        seat = db.execute("SELECT id, flight_id FROM seats WHERE is_booked = 0 LIMIT 1").fetchone()
        seat_id = seat["id"]
        flight_id = seat["flight_id"]

    # Passenger A books seat
    resp1 = client.post("/api/bookings", json={
        "flight_id": flight_id,
        "passenger_name": "Rohan Sharma",
        "passenger_email": "rohan@example.in",
        "passenger_phone": "+91 9876543210",
        "seat_ids": [seat_id]
    })
    assert resp1.status_code == 201
    data1 = resp1.get_json()
    assert data1["success"] is True

    # Passenger B attempts to book the exact same seat
    resp2 = client.post("/api/bookings", json={
        "flight_id": flight_id,
        "passenger_name": "Priya Verma",
        "passenger_email": "priya@example.in",
        "passenger_phone": "+91 9876500000",
        "seat_ids": [seat_id]
    })
    assert resp2.status_code == 409
    data2 = resp2.get_json()
    assert data2["code"] == "SEAT_ALREADY_BOOKED"

def test_seat_hold_and_release():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        from app.db import get_db
        db = get_db()
        seat = db.execute("SELECT id, flight_id FROM seats WHERE is_booked = 0 LIMIT 1").fetchone()
        seat_id = seat["id"]
        flight_id = seat["flight_id"]

    # User 1 holds seat for 5 mins
    hold_resp = client.post("/api/seats/hold", json={
        "flight_id": flight_id,
        "seat_ids": [seat_id],
        "lock_token": "token-user-1"
    })
    assert hold_resp.status_code == 200
    assert hold_resp.get_json()["hold_seconds"] == 300

    # User 2 tries to hold or book the same held seat
    hold_resp2 = client.post("/api/seats/hold", json={
        "flight_id": flight_id,
        "seat_ids": [seat_id],
        "lock_token": "token-user-2"
    })
    assert hold_resp2.status_code == 409
    assert hold_resp2.get_json()["code"] == "SEAT_HELD"

    # User 1 releases the seat
    release_resp = client.post("/api/seats/release", json={
        "lock_token": "token-user-1"
    })
    assert release_resp.status_code == 200

    # User 2 can now hold the seat
    hold_resp3 = client.post("/api/seats/hold", json={
        "flight_id": flight_id,
        "seat_ids": [seat_id],
        "lock_token": "token-user-2"
    })
    assert hold_resp3.status_code == 200

def test_prevent_double_booking_concurrent():
    app = create_app()
    
    with app.app_context():
        from app.db import get_db
        db = get_db()
        seat = db.execute("SELECT id, flight_id FROM seats WHERE is_booked = 0 LIMIT 1").fetchone()
        seat_id = seat["id"]
        flight_id = seat["flight_id"]

    results = []

    def attempt_booking(user_name):
        client = app.test_client()
        resp = client.post("/api/bookings", json={
            "flight_id": flight_id,
            "passenger_name": user_name,
            "passenger_email": f"{user_name.lower()}@test.in",
            "passenger_phone": "+91 9999900000",
            "seat_ids": [seat_id]
        })
        results.append((user_name, resp.status_code, resp.get_json()))

    t1 = threading.Thread(target=attempt_booking, args=("Concurrent_User_A",))
    t2 = threading.Thread(target=attempt_booking, args=("Concurrent_User_B",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    status_codes = [r[1] for r in results]
    assert 201 in status_codes
    assert 409 in status_codes
    assert len(status_codes) == 2
