import click
from flask import Flask
from app.config import Config
from app import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database hooks
    db.init_app(app)

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

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
