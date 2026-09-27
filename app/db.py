import sqlite3
from flask import g, current_app

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10.0  # Wait up to 10 seconds for locks to clear in concurrent writes
        )
        g.db.row_factory = sqlite3.Row
        # Enable foreign key constraint enforcement
        g.db.execute("PRAGMA foreign_keys = ON;")
        # Enable WAL mode for better concurrency (readers do not block writers, writers do not block readers)
        g.db.execute("PRAGMA journal_mode = WAL;")
    return g.db

def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes database schema from schema.sql."""
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
