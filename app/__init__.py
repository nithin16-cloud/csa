import click
from flask import Flask, session
from app.config import Config
from app import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database hooks
    db.init_app(app)

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

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
