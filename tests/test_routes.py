import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    return app.test_client()

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"CloudSky" in response.data
    assert b"Fly in Comfort" in response.data

def test_flights_search_page(client):
    response = client.get("/flights")
    assert response.status_code == 200
    assert b"Available Commercial Flights" in response.data

def test_booking_page(client):
    response = client.get("/booking/1")
    assert response.status_code == 200
    assert b"Interactive Aircraft Cabin" in response.data

def test_manage_page(client):
    response = client.get("/manage")
    assert response.status_code == 200
    assert b"Booking Reference (PNR)" in response.data

def test_api_seats(client):
    response = client.get("/api/flights/1/seats")
    assert response.status_code == 200
    data = response.get_json()
    assert "seats" in data
    assert len(data["seats"]) > 0

def test_multi_passenger_booking_success(client):
    app = create_app()
    with app.app_context():
        from app.db import get_db
        db = get_db()
        row = db.execute("""
            SELECT flight_id, COUNT(*) as cnt 
            FROM seats 
            WHERE is_booked = 0 
            GROUP BY flight_id 
            HAVING cnt >= 2 
            LIMIT 1
        """).fetchone()
        assert row is not None
        flight_id = row["flight_id"]

        seats = db.execute("SELECT id, seat_number FROM seats WHERE flight_id = ? AND is_booked = 0 LIMIT 2", (flight_id,)).fetchall()
        seat_ids = [s["id"] for s in seats]

    payload = {
        "flight_id": flight_id,
        "passenger_name": "Rohan Sharma",
        "passenger_email": "rohan.multi@example.in",
        "passenger_phone": "+91 98765 43210",
        "seat_ids": seat_ids,
        "passengers": [
            {
                "seat_id": seat_ids[0],
                "name": "Rohan Sharma",
                "age": 32,
                "gender": "Male"
            },
            {
                "seat_id": seat_ids[1],
                "name": "Priya Sharma",
                "age": 29,
                "gender": "Female"
            }
        ]
    }

    resp = client.post("/api/bookings", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert "booking" in data
    booking = data["booking"]
    assert len(booking["passengers"]) == 2
    assert booking["passengers"][0]["passenger_name"] == "Rohan Sharma"
    assert booking["passengers"][0]["passenger_age"] == 32
    assert booking["passengers"][1]["passenger_name"] == "Priya Sharma"
    assert booking["passengers"][1]["passenger_age"] == 29

    # Verify retrieval via GET /api/bookings/<pnr>
    pnr = booking["pnr"]
    get_resp = client.get(f"/api/bookings/{pnr}")
    assert get_resp.status_code == 200
    get_data = get_resp.get_json()
    assert len(get_data["seats"]) == 2
    names = [s["passenger_name"] for s in get_data["seats"]]
    assert "Rohan Sharma" in names
    assert "Priya Sharma" in names

def test_multi_passenger_validation(client):
    resp = client.post("/api/bookings", json={
        "flight_id": 1,
        "seat_ids": []
    })
    assert resp.status_code == 400

    resp2 = client.post("/api/bookings", json={
        "flight_id": 1,
        "passenger_name": "",
        "seat_ids": [1]
    })
    assert resp2.status_code == 400

def test_flights_filter_view(client):
    resp = client.get("/flights?origin=DEL&destination=BOM")
    assert resp.status_code == 200
    assert b"Available Commercial Flights" in resp.data
    assert b"Filter Flights" in resp.data
    assert b"Departure Time" in resp.data
    assert b"Aircraft Fleet" in resp.data
