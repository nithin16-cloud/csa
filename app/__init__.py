import os
import datetime
import click
from pathlib import Path
from flask import Flask, session, jsonify, render_template, request
from app.config import Config
from app import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure parent directory for SQLite database exists (crucial for Docker / volume mounts)
    db_path = app.config.get("DATABASE_PATH")
    if db_path and db_path != ":memory:":
        parent_dir = Path(db_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database hooks
    db.init_app(app)

    # Auto-seed database on first startup if tables don't exist (e.g. cold start on cloud deployment)
    with app.app_context():
        try:
            db_conn = db.get_db()
            table_check = db_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='airports'").fetchone()
            if not table_check:
                from app.seed import seed_database
                db.init_db()
                seed_database()
        except Exception:
            pass

    # Context processor to make current_user available in all templates
    @app.context_processor
    def inject_user():
        from app.db import get_db
        if 'user_id' in session:
            try:
                db_conn = get_db()
                user = db_conn.execute("SELECT id, name, email, phone FROM users WHERE id = ?", (session['user_id'],)).fetchone()
                return {'current_user': user}
            except Exception:
                return {'current_user': None}
        return {'current_user': None}

    # Production Security Response Headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # Health Check Endpoints (for Docker, Render, Kubernetes, AWS, Railway)
    @app.route("/health")
    @app.route("/api/health")
    def health_check():
        db_status = "connected"
        try:
            db_conn = db.get_db()
            db_conn.execute("SELECT 1").fetchone()
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            return jsonify({
                "status": "degraded",
                "service": "CloudSky Airways Flight Reservation System",
                "database": db_status,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }), 503

        return jsonify({
            "status": "healthy",
            "service": "CloudSky Airways Flight Reservation System",
            "version": "1.0.0",
            "environment": app.config.get("FLASK_ENV", "production"),
            "database": db_status,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }), 200

    # Production Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found", "status_code": 404}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error", "status_code": 500}), 500
        return render_template("errors/500.html"), 500

    # Register custom CLI commands
    @app.cli.command("init-db")
    def init_db_command():
        """Clear the existing data and create new tables."""
        db.init_db()
        click.echo("Initialized the database.")

    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed the database with sample airports, flights, and seats."""
        from app.seed import seed_database
        db.init_db()
        seed_database()
        click.echo("Database seeded successfully.")

    @app.cli.command("list-users")
    def list_users_command():
        """List all registered users stored in the SQLite database."""
        db_conn = db.get_db()
        users = db_conn.execute("SELECT id, name, email, phone, created_at FROM users ORDER BY id ASC").fetchall()
        if not users:
            click.echo("No registered users found in database.")
            return
        click.echo(f"\nFound {len(users)} user(s) in SQLite database:")
        click.echo("=" * 80)
        click.echo(f"{'ID':<4} {'Name':<22} {'Gmail / Email':<32} {'Created At'}")
        click.echo("-" * 80)
        for u in users:
            click.echo(f"{u['id']:<4} {u['name']:<22} {u['email']:<32} {u['created_at']}")
        click.echo("=" * 80 + "\n")

    # Apply ProxyFix so Flask trusts X-Forwarded-Proto and X-Forwarded-For from Render reverse proxy
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
