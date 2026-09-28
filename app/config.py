import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Base Configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "cloudsky-dev-secret-key-12345")
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "cloudsky.db"))
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("true", "1")
    TESTING = False

    # Security & Session Cookie Hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0").lower() in ("true", "1")
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

class DevelopmentConfig(Config):
    """Local Development Configuration."""
    DEBUG = True
    FLASK_ENV = "development"
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production Cloud Deployment Configuration."""
    DEBUG = False
    FLASK_ENV = "production"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1").lower() in ("true", "1")

class TestingConfig(Config):
    """Unit and Integration Testing Configuration."""
    TESTING = True
    DEBUG = True
    DATABASE_PATH = ":memory:"
    SECRET_KEY = "test-secret-key"

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": Config
}
