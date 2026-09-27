import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cloudsky-dev-secret-key-12345")
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "cloudsky.db"))
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
