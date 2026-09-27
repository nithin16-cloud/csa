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
    # Use real seeded db to test concurrency with threads
    app = create_app()
    client = app.test_client()

    with app.app_context():
        from app.db import get_db
        db = get_db()
        # Find an available seat
        seat = db.execute("SELECT id, flight_id FROM seats WHERE is_booked = 0 LIMIT 1").fetchone()
        seat_id = seat["id"]
        flight_id = seat["flight_id"]

    # Passenger A books seat
    resp1 = client.post("/api/bookings", json={
        "flight_id": flight_id,
        "passenger_name": "Alice Smith",
        "passenger_email": "alice@example.com",
        "passenger_phone": "+1 555-0100",
        "seat_ids": [seat_id]
    })
    assert resp1.status_code == 201
    data1 = resp1.get_json()
    assert data1["success"] is True

    # Passenger B attempts to book the exact same seat
    resp2 = client.post("/api/bookings", json={
        "flight_id": flight_id,
        "passenger_name": "Bob Jones",
        "passenger_email": "bob@example.com",
        "passenger_phone": "+1 555-0200",
        "seat_ids": [seat_id]
    })
    assert resp2.status_code == 409
    data2 = resp2.get_json()
    assert data2["code"] == "SEAT_ALREADY_BOOKED"

def test_prevent_double_booking_concurrent():
    app = create_app()
    
    with app.app_context():
        from app.db import get_db
        db = get_db()
        # Find an available seat
        seat = db.execute("SELECT id, flight_id FROM seats WHERE is_booked = 0 LIMIT 1").fetchone()
        seat_id = seat["id"]
        flight_id = seat["flight_id"]

    results = []

    def attempt_booking(user_name):
        client = app.test_client()
        resp = client.post("/api/bookings", json={
            "flight_id": flight_id,
            "passenger_name": user_name,
            "passenger_email": f"{user_name.lower()}@test.com",
            "passenger_phone": "+1 555-0000",
            "seat_ids": [seat_id]
        })
        results.append((user_name, resp.status_code, resp.get_json()))

    t1 = threading.Thread(target=attempt_booking, args=("User_Concurrent_1",))
    t2 = threading.Thread(target=attempt_booking, args=("User_Concurrent_2",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    status_codes = [r[1] for r in results]
    # Exactly one request must succeed (201) and the other must be rejected (409)
    assert 201 in status_codes
    assert 409 in status_codes
    assert len(status_codes) == 2
