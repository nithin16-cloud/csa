import datetime
import random
from app.db import get_db

AIRPORTS_DATA = [
    ("JFK", "John F. Kennedy International Airport", "New York", "United States"),
    ("LHR", "Heathrow Airport", "London", "United Kingdom"),
    ("DXB", "Dubai International Airport", "Dubai", "United Arab Emirates"),
    ("SIN", "Singapore Changi Airport", "Singapore", "Singapore"),
    ("HND", "Tokyo Haneda Airport", "Tokyo", "Japan"),
    ("CDG", "Charles de Gaulle Airport", "Paris", "France"),
    ("SFO", "San Francisco International Airport", "San Francisco", "United States"),
    ("DEL", "Indira Gandhi International Airport", "New Delhi", "India"),
]

FLIGHT_TEMPLATES = [
    ("CS-101", "JFK", "LHR", 7, 450.0, "Boeing 787-9 Dreamliner"),
    ("CS-102", "LHR", "JFK", 8, 460.0, "Boeing 787-9 Dreamliner"),
    ("CS-201", "DXB", "LHR", 7.5, 380.0, "Airbus A350-900"),
    ("CS-202", "LHR", "DXB", 7, 390.0, "Airbus A350-900"),
    ("CS-301", "SIN", "HND", 7, 520.0, "Boeing 777-300ER"),
    ("CS-302", "HND", "SIN", 7.2, 510.0, "Boeing 777-300ER"),
    ("CS-401", "JFK", "SFO", 6, 280.0, "Airbus A321neo"),
    ("CS-402", "SFO", "JFK", 5.5, 290.0, "Airbus A321neo"),
    ("CS-501", "DEL", "DXB", 3.5, 240.0, "Boeing 737 MAX 9"),
    ("CS-502", "DXB", "DEL", 3.5, 240.0, "Boeing 737 MAX 9"),
    ("CS-601", "CDG", "JFK", 8.5, 490.0, "Airbus A350-900"),
    ("CS-602", "JFK", "CDG", 8, 480.0, "Airbus A350-900"),
    ("CS-701", "LHR", "SIN", 13, 720.0, "Boeing 787-9 Dreamliner"),
    ("CS-702", "SIN", "LHR", 13.5, 740.0, "Boeing 787-9 Dreamliner"),
]

def generate_seats_for_flight(cursor, flight_id):
    """
    Generates a realistic commercial cabin seat layout:
    - Rows 1-2: First Class (1A, 1B, 1E, 1F) (1.8x - 2.5x base price)
    - Rows 3-6: Business Class (3A, 3B, 3C, 3D, 3E, 3F) (1.4x - 1.8x base price)
    - Rows 7-18: Economy Class (Window A/F, Middle B/E, Aisle C/D) (1.0x - 1.1x base price)
    """
    seat_records = []

    # First Class: Rows 1-2 (4 seats per row)
    for r in range(1, 3):
        for col in ["A", "B", "E", "F"]:
            stype = "Window" if col in ("A", "F") else "Aisle"
            seat_records.append((flight_id, f"{r}{col}", "First", stype, 2.2, 0))

    # Business Class: Rows 3-6 (6 seats per row)
    for r in range(3, 7):
        for col in ["A", "B", "C", "D", "E", "F"]:
            if col in ("A", "F"):
                stype = "Window"
            elif col in ("C", "D"):
                stype = "Aisle"
            else:
                stype = "Middle"
            seat_records.append((flight_id, f"{r}{col}", "Business", stype, 1.6, 0))

    # Economy Class: Rows 7-16
    for r in range(7, 17):
        for col in ["A", "B", "C", "D", "E", "F"]:
            if r == 10:
                stype = "Exit Row"
                mult = 1.15
            elif col in ("A", "F"):
                stype = "Window"
                mult = 1.05
            elif col in ("C", "D"):
                stype = "Aisle"
                mult = 1.05
            else:
                stype = "Middle"
                mult = 1.0
            seat_records.append((flight_id, f"{r}{col}", "Economy", stype, mult, 0))

    cursor.executemany("""
        INSERT INTO seats (flight_id, seat_number, cabin_class, seat_type, price_multiplier, is_booked)
        VALUES (?, ?, ?, ?, ?, ?)
    """, seat_records)

def seed_database():
    """Populates airports, schedules for the next 14 days, and all seats."""
    db = get_db()
    cursor = db.cursor()

    # 1. Insert Airports
    cursor.executemany("""
        INSERT OR IGNORE INTO airports (code, name, city, country)
        VALUES (?, ?, ?, ?)
    """, AIRPORTS_DATA)

    # 2. Insert Flights across upcoming 14 days
    today = datetime.date.today()
    flight_records = []

    for day_offset in range(0, 14):
        date_curr = today + datetime.timedelta(days=day_offset)
        for num, orig, dest, duration, price, aircraft in FLIGHT_TEMPLATES:
            # Create 1-2 departures per route per day
            dep_hour = random.choice([7, 11, 14, 18, 22])
            dep_dt = datetime.datetime(date_curr.year, date_curr.month, date_curr.day, dep_hour, 0)
            arr_dt = dep_dt + datetime.timedelta(hours=int(duration), minutes=int((duration % 1) * 60))

            flight_records.append((
                num, orig, dest,
                dep_dt.strftime("%Y-%m-%d %H:%M"),
                arr_dt.strftime("%Y-%m-%d %H:%M"),
                aircraft, price, "Scheduled"
            ))

    cursor.executemany("""
        INSERT INTO flights (flight_number, origin_code, destination_code, departure_time, arrival_time, aircraft_model, base_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, flight_records)
    db.commit()

    # 3. Generate seats for each flight created
    cursor.execute("SELECT id FROM flights")
    flight_ids = [row["id"] for row in cursor.fetchall()]

    for f_id in flight_ids:
        generate_seats_for_flight(cursor, f_id)

    db.commit()
    print(f"Successfully seeded {len(AIRPORTS_DATA)} airports, {len(flight_records)} flights, and cabin seats!")
