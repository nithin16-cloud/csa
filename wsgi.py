import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from app import create_app
from app.config import config_by_name

# Resolve configuration based on FLASK_ENV
env_name = os.getenv("FLASK_ENV", "production").lower()
config_class = config_by_name.get(env_name, config_by_name["default"])

app = create_app(config_class=config_class)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")

    # In production on Windows, prefer Waitress; on Unix Gunicorn is typically run directly
    try:
        from waitress import serve
        print(f" * CloudSky Airways running on http://{host}:{port} via Waitress WSGI")
        serve(app, host=host, port=port)
    except ImportError:
        app.run(host=host, port=port)
