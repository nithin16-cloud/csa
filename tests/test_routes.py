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
