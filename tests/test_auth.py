import pytest
from app import create_app
from app.db import get_db

@pytest.fixture
def client():
    app = create_app()
    return app.test_client()

def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Welcome to CloudSky" in response.data
    assert b"Sign In to Account" in response.data

def test_register_page_renders(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Join CloudSky Airways" in response.data

def test_login_with_demo_credentials(client):
    # Rohan Sharma demo account seeded in database
    response = client.post("/login", data={
        "email": "rohan.sharma@example.in",
        "password": "Password@123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back, Rohan Sharma!" in response.data
    assert b"Rohan" in response.data

def test_login_invalid_password(client):
    response = client.post("/login", data={
        "email": "rohan.sharma@example.in",
        "password": "WrongPassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data

def test_register_new_user(client):
    import uuid
    random_email = f"user_{uuid.uuid4().hex[:6]}@domain.in"
    response = client.post("/register", data={
        "name": "Aarav Patel",
        "email": random_email,
        "phone": "+91 91234 56789",
        "password": "SecurePassword1",
        "confirm_password": "SecurePassword1"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome to CloudSky Airways, Aarav Patel!" in response.data

def test_register_password_mismatch(client):
    response = client.post("/register", data={
        "name": "Test User",
        "email": "mismatch@test.in",
        "phone": "+91 99999 99999",
        "password": "Password123",
        "confirm_password": "DifferentPassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Passwords do not match" in response.data

def test_logout(client):
    # Log in first
    client.post("/login", data={
        "email": "rohan.sharma@example.in",
        "password": "Password@123"
    })
    # Then logout
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been signed out successfully." in response.data

def test_api_auth_login(client):
    response = client.post("/api/auth/login", json={
        "email": "rohan.sharma@example.in",
        "password": "Password@123"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["user"]["name"] == "Rohan Sharma"
