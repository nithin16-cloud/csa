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

        # Migration: Ensure bookings cancellation columns exist
        b_cols = [row[1] for row in cursor.execute("PRAGMA table_info(bookings)").fetchall()]
        if b_cols:
            if "cancellation_fee" not in b_cols:
                cursor.execute("ALTER TABLE bookings ADD COLUMN cancellation_fee REAL DEFAULT 0.0")
            if "refund_amount" not in b_cols:
                cursor.execute("ALTER TABLE bookings ADD COLUMN refund_amount REAL DEFAULT 0.0")
            if "cancelled_at" not in b_cols:
                cursor.execute("ALTER TABLE bookings ADD COLUMN cancelled_at TIMESTAMP DEFAULT NULL")
            if "cancellation_details" not in b_cols:
                cursor.execute("ALTER TABLE bookings ADD COLUMN cancellation_details TEXT DEFAULT ''")

        # Clean any historical booking_seats orphaned from cancelled bookings
        cursor.execute("DELETE FROM booking_seats WHERE booking_id IN (SELECT id FROM bookings WHERE payment_status = 'Cancelled')")

        # Migration: Ensure payments table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                transaction_id VARCHAR(50) UNIQUE NOT NULL,
                payment_method VARCHAR(30) NOT NULL,
                amount REAL NOT NULL,
                currency VARCHAR(5) NOT NULL DEFAULT 'INR',
                status VARCHAR(20) NOT NULL DEFAULT 'Success',
                payment_details TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments(booking_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_txn ON payments(transaction_id)")
        db.commit()
    except Exception:
        pass

def is_mongo_enabled():
    """Checks whether MongoDB is configured as the active database engine."""
    db_type = current_app.config.get("DB_TYPE", "sqlite").lower()
    mongo_uri = (current_app.config.get("MONGO_URI") or "").strip()
    return db_type == "mongodb" or (bool(mongo_uri) and db_type != "sqlite")

def get_db():
    """Opens a new database connection (MongoDB or SQLite) for the current application context."""
    if 'db' not in g:
        if is_mongo_enabled():
            from app.mongo import MongoAdapter
            mongo_uri = current_app.config.get("MONGO_URI") or "mongodb://localhost:27017/cloudsky"
            mongo_db_name = current_app.config.get("MONGO_DB_NAME", "cloudsky")
            adapter = MongoAdapter(uri=mongo_uri, db_name=mongo_db_name)
            adapter.ensure_indexes()
            g.db = adapter
        else:
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
    """Initializes database schema (clears and re-indexes MongoDB collections or runs schema.sql)."""
    if is_mongo_enabled():
        db = get_db()
        for col_name in ["users", "airports", "flights", "seats", "bookings", "booking_seats", "payments", "counters"]:
            try:
                db.db.drop_collection(col_name)
            except Exception:
                pass
        db.ensure_indexes()
    else:
        db = get_db()
        with current_app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)

