import sqlite3
from flask import g, current_app

def migrate_db(db):
    """Ensures seat amenity metadata columns exist and are populated."""
    try:
        cursor = db.cursor()
        cols = [row[1] for row in cursor.execute("PRAGMA table_info(seats)").fetchall()]
        if not cols:
            return  # Table not created yet
        
        modified = False
        if "seat_pitch" not in cols:
            cursor.execute("ALTER TABLE seats ADD COLUMN seat_pitch VARCHAR(10) DEFAULT '31\"'")
            modified = True
        if "has_power" not in cols:
            cursor.execute("ALTER TABLE seats ADD COLUMN has_power INTEGER NOT NULL DEFAULT 1")
            modified = True
        if "has_extra_legroom" not in cols:
            cursor.execute("ALTER TABLE seats ADD COLUMN has_extra_legroom INTEGER NOT NULL DEFAULT 0")
            modified = True
        if "recline_deg" not in cols:
            cursor.execute("ALTER TABLE seats ADD COLUMN recline_deg INTEGER NOT NULL DEFAULT 15")
            modified = True
        if "features" not in cols:
            cursor.execute("ALTER TABLE seats ADD COLUMN features TEXT DEFAULT ''")
            modified = True

        if modified:
            # Backfill First Class
            cursor.execute("""
                UPDATE seats 
                SET seat_pitch = '78"', has_power = 1, has_extra_legroom = 1, recline_deg = 180,
                    features = 'Lie-flat Bed, Private Suite, Chef Dining, 24" 4K IFE Screen, Universal AC & 65W USB-C'
                WHERE cabin_class = 'First'
            """)
            # Backfill Business Class
            cursor.execute("""
                UPDATE seats 
                SET seat_pitch = '42"', has_power = 1, has_extra_legroom = 1, recline_deg = 150,
                    features = 'Plush Leather Recline, 15.6" Touchscreen, Gourmet Hot Meals, Universal AC & USB-C Power'
                WHERE cabin_class = 'Business'
            """)
            # Backfill Exit Row
            cursor.execute("""
                UPDATE seats 
                SET seat_pitch = '34"', has_power = 1, has_extra_legroom = 1, recline_deg = 20,
                    features = 'Extra Legroom, Priority Exit, High-Speed USB Port, Complimentary Refreshment'
                WHERE cabin_class = 'Economy' AND seat_type = 'Exit Row'
            """)
            # Backfill Economy Window
            cursor.execute("""
                UPDATE seats 
                SET seat_pitch = '31"', has_power = 1, has_extra_legroom = 0, recline_deg = 15,
                    features = 'Scenic Window View, Ergonomic Headrest, High-Speed USB Port'
                WHERE cabin_class = 'Economy' AND seat_type = 'Window' AND (features IS NULL OR features = '')
            """)
            # Backfill Economy Aisle
            cursor.execute("""
                UPDATE seats 
                SET seat_pitch = '31"', has_power = 1, has_extra_legroom = 0, recline_deg = 15,
                    features = 'Direct Aisle Access, Rapid Movement, High-Speed USB Port'
                WHERE cabin_class = 'Economy' AND seat_type = 'Aisle' AND (features IS NULL OR features = '')
            """)
            # Backfill Economy Middle / Standard
            cursor.execute("""
                UPDATE seats 
                SET seat_pitch = '31"', has_power = 1, has_extra_legroom = 0, recline_deg = 15,
                    features = 'Ergonomic Cushioning, Personal Reading Light, High-Speed USB Port'
                WHERE cabin_class = 'Economy' AND (features IS NULL OR features = '')
            """)
            db.commit()
    except Exception:
        pass

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            timeout=10.0  # Wait up to 10 seconds for locks to clear in concurrent writes
        )
        g.db.row_factory = sqlite3.Row
        # Enable foreign key constraint enforcement
        g.db.execute("PRAGMA foreign_keys = ON;")
        # Enable WAL mode for better concurrency (readers do not block writers, writers do not block readers)
        g.db.execute("PRAGMA journal_mode = WAL;")

        if not getattr(current_app, '_db_migrated', False):
            migrate_db(g.db)
            current_app._db_migrated = True

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

