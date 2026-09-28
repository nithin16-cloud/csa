import pytest
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig

@pytest.fixture
def client():
    app = create_app()
    return app.test_client()

def test_health_check_endpoint(client):
    """Verify production /health endpoint returns HTTP 200 and valid JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data["status"] == "healthy"
    assert data["service"] == "CloudSky Airways Flight Reservation System"
    assert data["database"] == "connected"
    assert "timestamp" in data

def test_api_health_check_endpoint(client):
    """Verify /api/health alias for API monitors and gateways."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"

def test_security_headers_present(client):
    """Verify production security headers are attached to responses."""
    response = client.get("/")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"

def test_404_html_error_page(client):
    """Verify custom luxury 404 page renders for browser navigation."""
    response = client.get("/non-existent-route-for-testing")
    assert response.status_code == 404
    assert b"Error 404" in response.data
    assert b"Destination Not Found" in response.data

def test_404_api_json_response(client):
    """Verify custom 404 returns structured JSON for /api/* endpoints."""
    response = client.get("/api/non-existent-endpoint")
    assert response.status_code == 404
    data = response.get_json()
    assert data is not None
    assert data["status_code"] == 404
    assert "error" in data

def test_wsgi_module_import():
    """Verify wsgi.py loads cleanly and exposes the production app."""
    import wsgi
    assert wsgi.app is not None

def test_config_environments():
    """Verify config environments have appropriate flags."""
    dev = DevelopmentConfig()
    assert dev.DEBUG is True
    assert dev.SESSION_COOKIE_SECURE is False

    prod = ProductionConfig()
    assert prod.DEBUG is False

    test = TestingConfig()
    assert test.TESTING is True
