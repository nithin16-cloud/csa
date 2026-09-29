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

def test_register_then_login_cycle(client):
    """Verify newly registered user can log out and log back in with exact credentials."""
    import uuid
    unique_email = f"signup_test_{uuid.uuid4().hex[:6]}@gmail.com"
    raw_password = "SecretPassword123"

    # Step 1: Register
    reg_resp = client.post("/register", data={
        "name": "Pooja Hegde",
        "email": f"  {unique_email.upper()}  ",  # Test mixed case and whitespace
        "phone": "+91 98888 77777",
        "password": raw_password,
        "confirm_password": raw_password
    }, follow_redirects=True)
    assert reg_resp.status_code == 200
    assert b"Welcome to CloudSky Airways, Pooja Hegde!" in reg_resp.data

    # Step 2: Logout
    logout_resp = client.get("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200

    # Step 3: Login with same credentials
    login_resp = client.post("/login", data={
        "email": unique_email,
        "password": raw_password,
        "remember": "on"
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Welcome back, Pooja Hegde!" in login_resp.data

def test_login_with_mobile_autocomplete_space_in_password(client):
    """Verify login succeeds even if phone keyboard autofill appended a trailing space."""
    login_resp = client.post("/login", data={
        "email": "rohan.sharma@example.in",
        "password": "Password@123   "  # Trailing space from virtual keyboard
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Welcome back, Rohan Sharma!" in login_resp.data

def test_login_non_existent_account_feedback(client):
    """Verify proper feedback when email is not registered in the database."""
    login_resp = client.post("/login", data={
        "email": "non_existent_user_9999@gmail.com",
        "password": "SomePassword123"
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"No account found with this email" in login_resp.data

