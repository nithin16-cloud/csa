import datetime
import random
from app.db import get_db

AIRPORTS_DATA = [
    ("DEL", "Indira Gandhi International Airport", "New Delhi", "India"),
    ("BOM", "Chhatrapati Shivaji Maharaj Intl Airport", "Mumbai", "India"),
    ("BLR", "Kempegowda International Airport", "Bengaluru", "India"),
    ("HYD", "Rajiv Gandhi International Airport", "Hyderabad", "India"),
    ("MAA", "Chennai International Airport", "Chennai", "India"),
    ("CCU", "Netaji Subhash Chandra Bose Intl Airport", "Kolkata", "India"),
    ("DXB", "Dubai International Airport", "Dubai", "United Arab Emirates"),
    ("SIN", "Singapore Changi Airport", "Singapore", "Singapore"),
    ("LHR", "Heathrow Airport", "London", "United Kingdom"),
    ("JFK", "John F. Kennedy International Airport", "New York", "United States"),
]

# Comprehensive Flight routes connecting domestic and global hubs with realistic INR base fares
FLIGHT_TEMPLATES = [
    # Trunk Routes: Delhi - Mumbai
    ("CS-101", "DEL", "BOM", 2.2, 5499.0, "Boeing 737 MAX 8"),
    ("CS-102", "BOM", "DEL", 2.1, 5699.0, "Boeing 737 MAX 8"),
    # Delhi - Bengaluru
    ("CS-103", "DEL", "BLR", 2.8, 6899.0, "Airbus A321neo"),
    ("CS-104", "BLR", "DEL", 2.7, 6799.0, "Airbus A321neo"),
    # Mumbai - Bengaluru
    ("CS-105", "BOM", "BLR", 1.8, 4899.0, "Airbus A320neo"),
    ("CS-106", "BLR", "BOM", 1.7, 4999.0, "Airbus A320neo"),
    # Delhi - Hyderabad
    ("CS-107", "DEL", "HYD", 2.2, 5299.0, "Boeing 737 MAX 8"),
    ("CS-108", "HYD", "DEL", 2.1, 5299.0, "Boeing 737 MAX 8"),
    # Mumbai - Hyderabad
    ("CS-109", "BOM", "HYD", 1.4, 4299.0, "Airbus A320neo"),
    ("CS-110", "HYD", "BOM", 1.4, 4299.0, "Airbus A320neo"),
    # Delhi - Chennai
    ("CS-111", "DEL", "MAA", 2.8, 6499.0, "Airbus A321neo"),
    ("CS-112", "MAA", "DEL", 2.8, 6499.0, "Airbus A321neo"),
    # Mumbai - Chennai
    ("CS-113", "BOM", "MAA", 2.0, 4899.0, "Airbus A320neo"),
    ("CS-114", "MAA", "BOM", 1.9, 4899.0, "Airbus A320neo"),
    # Bengaluru - Hyderabad
    ("CS-115", "BLR", "HYD", 1.2, 3699.0, "Airbus A320neo"),
    ("CS-116", "HYD", "BLR", 1.1, 3699.0, "Airbus A320neo"),
    # Bengaluru - Chennai
    ("CS-117", "BLR", "MAA", 1.0, 3299.0, "Airbus A320neo"),
    ("CS-118", "MAA", "BLR", 1.0, 3299.0, "Airbus A320neo"),
    # Kolkata Connectors
    ("CS-701", "CCU", "DEL", 2.3, 5899.0, "Boeing 737 MAX 8"),
    ("CS-702", "DEL", "CCU", 2.2, 5999.0, "Boeing 737 MAX 8"),
    ("CS-703", "CCU", "BOM", 2.8, 6499.0, "Airbus A321neo"),
    ("CS-704", "BOM", "CCU", 2.7, 6499.0, "Airbus A321neo"),
    ("CS-705", "CCU", "BLR", 2.5, 6199.0, "Airbus A320neo"),
    ("CS-706", "BLR", "CCU", 2.5, 6199.0, "Airbus A320neo"),
    ("CS-707", "CCU", "HYD", 2.1, 5199.0, "Boeing 737 MAX 8"),
    ("CS-708", "HYD", "CCU", 2.0, 5199.0, "Boeing 737 MAX 8"),
    ("CS-709", "CCU", "MAA", 2.2, 5499.0, "Airbus A320neo"),
    ("CS-710", "MAA", "CCU", 2.2, 5499.0, "Airbus A320neo"),
    # Hyderabad - Chennai
    ("CS-601", "HYD", "MAA", 1.2, 3899.0, "Airbus A320neo"),
    ("CS-602", "MAA", "HYD", 1.2, 3899.0, "Airbus A320neo"),
    # International Routes: Dubai
    ("CS-201", "BOM", "DXB", 3.5, 16999.0, "Boeing 787-9 Dreamliner"),
    ("CS-202", "DXB", "BOM", 3.5, 17499.0, "Boeing 787-9 Dreamliner"),
    ("CS-203", "DEL", "DXB", 3.8, 18499.0, "Boeing 787-9 Dreamliner"),
    ("CS-204", "DXB", "DEL", 3.8, 18999.0, "Boeing 787-9 Dreamliner"),
    ("CS-205", "BLR", "DXB", 4.0, 17999.0, "Boeing 787-9 Dreamliner"),
    ("CS-206", "DXB", "BLR", 4.0, 18499.0, "Boeing 787-9 Dreamliner"),
    ("CS-207", "HYD", "DXB", 3.8, 17299.0, "Boeing 787-9 Dreamliner"),
    ("CS-208", "DXB", "HYD", 3.8, 17599.0, "Boeing 787-9 Dreamliner"),
    # International Routes: Singapore
    ("CS-301", "BLR", "SIN", 4.5, 21500.0, "Airbus A350-900"),
    ("CS-302", "SIN", "BLR", 4.5, 22000.0, "Airbus A350-900"),
    ("CS-303", "MAA", "SIN", 4.0, 19500.0, "Airbus A350-900"),
    ("CS-304", "SIN", "MAA", 4.0, 19800.0, "Airbus A350-900"),
    ("CS-305", "DEL", "SIN", 5.5, 24500.0, "Airbus A350-900"),
    ("CS-306", "SIN", "DEL", 5.5, 24900.0, "Airbus A350-900"),
    ("CS-307", "BOM", "SIN", 5.0, 23500.0, "Airbus A350-900"),
    ("CS-308", "SIN", "BOM", 5.0, 23900.0, "Airbus A350-900"),
    # International Routes: London Heathrow
    ("CS-401", "DEL", "LHR", 9.0, 42500.0, "Boeing 777-300ER"),
    ("CS-402", "LHR", "DEL", 8.5, 44000.0, "Boeing 777-300ER"),
    ("CS-403", "BOM", "LHR", 9.5, 43500.0, "Boeing 777-300ER"),
    ("CS-404", "LHR", "BOM", 9.0, 45000.0, "Boeing 777-300ER"),
    ("CS-405", "BLR", "LHR", 10.0, 46000.0, "Boeing 777-300ER"),
    ("CS-406", "LHR", "BLR", 9.5, 47500.0, "Boeing 777-300ER"),
    # International Routes: New York JFK
    ("CS-501", "BOM", "JFK", 15.5, 68000.0, "Boeing 787-9 Dreamliner"),
    ("CS-502", "JFK", "BOM", 15.0, 71000.0, "Boeing 787-9 Dreamliner"),
    ("CS-503", "DEL", "JFK", 15.0, 69500.0, "Boeing 787-9 Dreamliner"),
    ("CS-504", "JFK", "DEL", 14.5, 72500.0, "Boeing 787-9 Dreamliner"),
    # Global Inter-Hub Connectors
    ("CS-801", "DXB", "LHR", 7.5, 38500.0, "Boeing 777-300ER"),
    ("CS-802", "LHR", "DXB", 7.0, 39500.0, "Boeing 777-300ER"),
    ("CS-803", "LHR", "JFK", 8.0, 52000.0, "Boeing 777-300ER"),
    ("CS-804", "JFK", "LHR", 7.5, 53500.0, "Boeing 777-300ER"),
    ("CS-805", "SIN", "DXB", 7.2, 34000.0, "Airbus A350-900"),
    ("CS-806", "DXB", "SIN", 7.0, 34500.0, "Airbus A350-900"),
]

def generate_seats_for_flight(cursor, flight_id):
    """Generates commercial cabin layout with First, Business, and Economy."""
    seat_records = []

    # First Class: Rows 1-2 (4 seats per row: A, B, E, F) (2.2x multiplier)
    for r in range(1, 3):
        for col in ["A", "B", "E", "F"]:
            stype = "Window" if col in ("A", "F") else "Aisle"
            seat_records.append((
                flight_id, f"{r}{col}", "First", stype, 2.2,
                '78"', 1, 1, 180,
                'Lie-flat Bed, Private Suite, Chef Dining, 24" 4K IFE Screen, Universal AC & 65W USB-C',
                0
            ))

    # Business Class: Rows 3-6 (6 seats per row: A-F) (1.6x multiplier)
    for r in range(3, 7):
        for col in ["A", "B", "C", "D", "E", "F"]:
            if col in ("A", "F"):
                stype = "Window"
            elif col in ("C", "D"):
                stype = "Aisle"
            else:
                stype = "Middle"
            seat_records.append((
                flight_id, f"{r}{col}", "Business", stype, 1.6,
                '42"', 1, 1, 150,
                'Plush Leather Recline, 15.6" Touchscreen, Gourmet Hot Meals, Universal AC & USB-C Power',
                0
            ))

    # Economy Class: Rows 7-16 (1.0x - 1.15x multiplier)
    for r in range(7, 17):
        for col in ["A", "B", "C", "D", "E", "F"]:
            if r == 10:
                stype = "Exit Row"
                mult = 1.15
                pitch = '34"'
                extra_leg = 1
                recline = 20
                features = "Extra Legroom, Priority Exit, High-Speed USB Port, Complimentary Refreshment"
            elif col in ("A", "F"):
                stype = "Window"
                mult = 1.05
                pitch = '31"'
                extra_leg = 0
                recline = 15
                features = "Scenic Window View, Ergonomic Headrest, High-Speed USB Port"
            elif col in ("C", "D"):
                stype = "Aisle"
                mult = 1.05
                pitch = '31"'
                extra_leg = 0
                recline = 15
                features = "Direct Aisle Access, Rapid Movement, High-Speed USB Port"
            else:
                stype = "Middle"
                mult = 1.0
                pitch = '31"'
                extra_leg = 0
                recline = 15
                features = "Ergonomic Cushioning, Personal Reading Light, High-Speed USB Port"

            seat_records.append((
                flight_id, f"{r}{col}", "Economy", stype, mult,
                pitch, 1, extra_leg, recline, features,
                0
            ))

    cursor.executemany("""
        INSERT INTO seats (flight_id, seat_number, cabin_class, seat_type, price_multiplier, seat_pitch, has_power, has_extra_legroom, recline_deg, features, is_booked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, seat_records)

def seed_database():
    """Populates airports, flight schedules in Indian Rupees, and cabin seats."""
    db = get_db()
    cursor = db.cursor()

    # 1. Insert Demo Registered User
    from werkzeug.security import generate_password_hash
    demo_pw = generate_password_hash("Password@123")
    cursor.execute("""
        INSERT OR IGNORE INTO users (name, email, phone, password_hash)
        VALUES ('Rohan Sharma', 'rohan.sharma@example.in', '+91 98765 43210', ?)
    """, (demo_pw,))

    # 2. Insert Airports
    cursor.executemany("""
        INSERT OR IGNORE INTO airports (code, name, city, country)
        VALUES (?, ?, ?, ?)
    """, AIRPORTS_DATA)

    # 3. Insert Flights across upcoming 14 days
    today = datetime.date.today()
    flight_records = []

    for day_offset in range(0, 14):
        date_curr = today + datetime.timedelta(days=day_offset)
        for num, orig, dest, duration, price, aircraft in FLIGHT_TEMPLATES:
            dep_hour = random.choice([6, 9, 13, 17, 21])
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

    # 3. Generate seats for each flight that does not yet have seats
    cursor.execute("SELECT id FROM flights WHERE id NOT IN (SELECT DISTINCT flight_id FROM seats)")
    flight_ids = [row["id"] for row in cursor.fetchall()]

    for f_id in flight_ids:
        generate_seats_for_flight(cursor, f_id)

    db.commit()
    print(f"Successfully seeded {len(AIRPORTS_DATA)} airports, flights with INR fares, and cabin seats!")
