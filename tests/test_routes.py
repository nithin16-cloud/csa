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

def test_seat_amenities_metadata(client):
    """Test that /api/flights/<id>/seats returns enriched seat amenity metadata."""
    resp = client.get("/api/flights/1/seats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "seats" in data
    assert "aircraft_model" in data
    assert "total_seats" in data
    assert len(data["seats"]) > 0

    first_class_seats = [s for s in data["seats"] if s["cabin_class"] == "First"]
    business_seats = [s for s in data["seats"] if s["cabin_class"] == "Business"]
    exit_row_seats = [s for s in data["seats"] if s["seat_type"] == "Exit Row"]
    economy_std_seats = [s for s in data["seats"] if s["cabin_class"] == "Economy" and s["seat_type"] != "Exit Row"]

    # First Class: 78" pitch, 180° recline, extra legroom, universal AC/USB-C
    assert len(first_class_seats) > 0
    for s in first_class_seats:
        assert s["seat_pitch"] == '78"'
        assert s["recline_deg"] == 180
        assert s["has_extra_legroom"] == 1
        assert s["has_power"] == 1
        assert "features_list" in s
        assert len(s["features_list"]) > 0

    # Business Class: 42" pitch, 150° recline
    assert len(business_seats) > 0
    for s in business_seats:
        assert s["seat_pitch"] == '42"'
        assert s["recline_deg"] == 150
        assert s["has_extra_legroom"] == 1
        assert s["has_power"] == 1

    # Exit Row: 34" pitch, extra legroom
    assert len(exit_row_seats) > 0
    for s in exit_row_seats:
        assert s["seat_pitch"] == '34"'
        assert s["has_extra_legroom"] == 1

    # Economy Standard: 31" pitch
    assert len(economy_std_seats) > 0
    for s in economy_std_seats:
        assert s["seat_pitch"] == '31"'
        assert s["has_extra_legroom"] == 0

def test_seat_query_filters(client):
    """Test query parameter filtering on /api/flights/<id>/seats."""
    resp_first = client.get("/api/flights/1/seats?cabin_class=First")
    assert resp_first.status_code == 200
    seats_first = resp_first.get_json()["seats"]
    assert len(seats_first) > 0
    assert all(s["cabin_class"] == "First" for s in seats_first)

    resp_win = client.get("/api/flights/1/seats?seat_type=Window")
    assert resp_win.status_code == 200
    seats_win = resp_win.get_json()["seats"]
    assert len(seats_win) > 0
    assert all(s["seat_type"] == "Window" for s in seats_win)

    resp_leg = client.get("/api/flights/1/seats?extra_legroom=1")
    assert resp_leg.status_code == 200
    seats_leg = resp_leg.get_json()["seats"]
    assert len(seats_leg) > 0
    assert all(s["has_extra_legroom"] == 1 for s in seats_leg)

def test_cabin_ui_elements(client):
    """Test that booking page renders interactive inspector, wings, emergency exits, and filters."""
    resp = client.get("/booking/1")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")

    assert "seat-inspector-card" in html
    assert "Interactive Seat Inspector" in html
    assert "cabin-filters-toolbar" in html
    assert "fuselage-outer-stage" in html
    assert "airplane-wing wing-left" in html
    assert "airplane-wing wing-right" in html
    assert "cockpit-windows" in html
    assert "emergency-exit-marker" in html
    assert "cabin-amenity-station" in html

