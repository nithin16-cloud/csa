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

def test_payment_gateway_simulation(client):
    """Test simulated Indian payment gateway for UPI, Card, and NetBanking."""
    # Successful UPI authorization
    resp_upi = client.post("/api/payments/simulate", json={
        "method": "UPI",
        "amount": 4500,
        "vpa": "rohan@okhdfcbank"
    })
    assert resp_upi.status_code == 200
    upi_data = resp_upi.get_json()
    assert upi_data["success"] is True
    assert upi_data["transaction_id"].startswith("TXN-")
    assert upi_data["status"] == "Authorized"

    # Invalid UPI without @
    resp_bad_upi = client.post("/api/payments/simulate", json={
        "method": "UPI",
        "amount": 4500,
        "vpa": "invalidvpa"
    })
    assert resp_bad_upi.status_code == 400
    assert "Invalid UPI ID" in resp_bad_upi.get_json()["error"]

    # Card authorization
    resp_card = client.post("/api/payments/simulate", json={
        "method": "CreditCard",
        "amount": 7500,
        "card_number": "4532 8821 9012 3456"
    })
    assert resp_card.status_code == 200
    assert resp_card.get_json()["success"] is True

    # NetBanking authorization
    resp_nb = client.post("/api/payments/simulate", json={
        "method": "NetBanking",
        "amount": 6000,
        "bank": "HDFC"
    })
    assert resp_nb.status_code == 200
    assert resp_nb.get_json()["success"] is True

def test_booking_payment_and_boarding_pass(client):
    """Test booking creation with payment details, payments table persistence, and boarding pass generation."""
    app = create_app()
    with app.app_context():
        from app.db import get_db
        db = get_db()
        db.execute("UPDATE seats SET locked_until = NULL, lock_token = NULL WHERE is_booked = 0")
        db.commit()
        seat = db.execute("SELECT id, flight_id, seat_number FROM seats WHERE is_booked = 0 LIMIT 1").fetchone()
        assert seat is not None
        flight_id = seat["flight_id"]
        seat_id = seat["id"]

    payload = {
        "flight_id": flight_id,
        "passenger_name": "Aarav Patel",
        "passenger_email": "aarav.patel@example.in",
        "passenger_phone": "+91 99887 76655",
        "seat_ids": [seat_id],
        "payment_method": "UPI",
        "payment_details": {
            "vpa": "aarav@okhdfcbank",
            "method": "UPI"
        },
        "passengers": [
            {
                "seat_id": seat_id,
                "name": "Aarav Patel",
                "age": 30,
                "gender": "Male"
            }
        ]
    }

    resp = client.post("/api/bookings", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    booking = data["booking"]
    pnr = booking["pnr"]
    assert booking["payment_method"] == "UPI"
    assert booking["transaction_id"].startswith("TXN-")
    assert "terminal" in booking
    assert "gate" in booking
    assert "boarding_time" in booking

    # Verify payment record in DB
    with app.app_context():
        db = get_db()
        payment_row = db.execute("SELECT * FROM payments WHERE booking_id = ?", (booking["id"],)).fetchone()
        assert payment_row is not None
        assert payment_row["payment_method"] == "UPI"
        assert payment_row["status"] == "Success"
        assert payment_row["amount"] == booking["total_amount_inr"]

    # Verify retrieval via GET /api/bookings/<pnr>
    get_resp = client.get(f"/api/bookings/{pnr}")
    assert get_resp.status_code == 200
    b_data = get_resp.get_json()
    assert b_data["booking"]["booking_reference"] == pnr
    assert b_data["booking"]["payment"] is not None
    assert b_data["booking"]["payment"]["payment_method"] == "UPI"
    assert len(b_data["seats"]) == 1
    assert b_data["seats"][0]["gate"] == booking["gate"]
    assert b_data["seats"][0]["boarding_group"] in ("Group 1", "Group 2")

def test_seat_swap_workflow(client):
    """Test reassigning a booked seat to another available seat on the same flight."""
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
        flight_id = row["flight_id"]
        avail_seats = db.execute("SELECT id, seat_number FROM seats WHERE flight_id = ? AND is_booked = 0 LIMIT 2", (flight_id,)).fetchall()
        seat_a_id = avail_seats[0]["id"]
        seat_b_id = avail_seats[1]["id"]

    # Book seat A
    resp = client.post("/api/bookings", json={
        "flight_id": flight_id,
        "passenger_name": "Kavita Rao",
        "passenger_email": "kavita@example.in",
        "passenger_phone": "+91 91234 56789",
        "seat_ids": [seat_a_id],
        "passengers": [{"seat_id": seat_a_id, "name": "Kavita Rao", "age": 27, "gender": "Female"}]
    })
    assert resp.status_code == 201
    pnr = resp.get_json()["booking"]["pnr"]

    # Swap from seat A to seat B
    swap_resp = client.post(f"/api/bookings/{pnr}/change-seat", json={
        "old_seat_id": seat_a_id,
        "new_seat_id": seat_b_id
    })
    assert swap_resp.status_code == 200
    swap_data = swap_resp.get_json()
    assert swap_data["success"] is True
    assert swap_data["new_seat"] == avail_seats[1]["seat_number"]

    # Verify in DB: seat A is now available (0), seat B is now booked (1)
    with app.app_context():
        db = get_db()
        seat_a = db.execute("SELECT is_booked FROM seats WHERE id = ?", (seat_a_id,)).fetchone()
        seat_b = db.execute("SELECT is_booked FROM seats WHERE id = ?", (seat_b_id,)).fetchone()
        assert seat_a["is_booked"] == 0
        assert seat_b["is_booked"] == 1

def test_cancellation_and_inventory_release(client):
    """Test booking cancellation, immediate inventory release, fee deduction, and refund tracking."""
    app = create_app()
    with app.app_context():
        from app.db import get_db
        db = get_db()
        seat = db.execute("SELECT id, flight_id FROM seats WHERE is_booked = 0 LIMIT 1").fetchone()
        flight_id = seat["flight_id"]
        seat_id = seat["id"]

    # Book seat
    resp = client.post("/api/bookings", json={
        "flight_id": flight_id,
        "passenger_name": "Vikram Seth",
        "passenger_email": "vikram@example.in",
        "passenger_phone": "+91 98888 77777",
        "seat_ids": [seat_id],
        "passengers": [{"seat_id": seat_id, "name": "Vikram Seth", "age": 45, "gender": "Male"}]
    })
    assert resp.status_code == 201
    pnr = resp.get_json()["booking"]["pnr"]
    total_paid = resp.get_json()["booking"]["total_amount_inr"]

    # Verify seat is currently booked
    with app.app_context():
        db = get_db()
        s_booked = db.execute("SELECT is_booked FROM seats WHERE id = ?", (seat_id,)).fetchone()
        assert s_booked["is_booked"] == 1

    # Cancel booking
    cancel_resp = client.post(f"/api/bookings/{pnr}/cancel", json={
        "email": "vikram@example.in"
    })
    assert cancel_resp.status_code == 200
    c_data = cancel_resp.get_json()
    assert c_data["success"] is True
    assert c_data["cancellation"]["cancellation_fee_inr"] == 500.0
    assert c_data["cancellation"]["refund_amount_inr"] == total_paid - 500.0
    assert c_data["cancellation"]["refund_transaction_id"].startswith("REF-")

    # Verify seat is immediately released back to available inventory
    with app.app_context():
        db = get_db()
        s_freed = db.execute("SELECT is_booked, locked_until, lock_token FROM seats WHERE id = ?", (seat_id,)).fetchone()
        assert s_freed["is_booked"] == 0
        assert s_freed["locked_until"] is None
        assert s_freed["lock_token"] is None

        # Verify payments table records refund
        refund_payment = db.execute("SELECT * FROM payments WHERE booking_id = (SELECT id FROM bookings WHERE booking_reference = ?) AND status = 'Refunded'", (pnr,)).fetchone()
        assert refund_payment is not None
        assert refund_payment["payment_method"] == "Refund"

    # Attempting to cancel again should return 400
    cancel_again = client.post(f"/api/bookings/{pnr}/cancel", json={"email": "vikram@example.in"})
    assert cancel_again.status_code == 400

def test_manage_portal_views(client):
    """Test retrieving booking via GET query parameter and POST form on manage portal."""
    app = create_app()
    with app.app_context():
        from app.db import get_db
        db = get_db()
        db.execute("UPDATE seats SET locked_until = NULL, lock_token = NULL WHERE is_booked = 0")
        db.commit()
        seat = db.execute("SELECT id, flight_id FROM seats WHERE is_booked = 0 LIMIT 1").fetchone()
        flight_id = seat["flight_id"]
        seat_id = seat["id"]

    # Create a booking
    resp = client.post("/api/bookings", json={
        "flight_id": flight_id,
        "passenger_name": "Meera Nambiar",
        "passenger_email": "meera@example.in",
        "passenger_phone": "+91 97777 66666",
        "seat_ids": [seat_id],
        "passengers": [{"seat_id": seat_id, "name": "Meera Nambiar", "age": 35, "gender": "Female"}]
    })
    pnr = resp.get_json()["booking"]["pnr"]

    # Test GET /manage?pnr=...
    get_manage = client.get(f"/manage?pnr={pnr}")
    assert get_manage.status_code == 200
    assert b"PASSENGER SELF-SERVICE PORTAL" in get_manage.data
    assert pnr.encode() in get_manage.data

    # Test POST /manage
    post_manage = client.post("/manage", data={"pnr": pnr, "email": "meera@example.in"})
    assert post_manage.status_code == 200
    assert pnr.encode() in post_manage.data

