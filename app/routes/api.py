import string
import random
import sqlite3
from flask import Blueprint, jsonify, request
from app.db import get_db

api_bp = Blueprint("api", __name__)

def generate_pnr():
    """Generate a unique 6-character airline PNR (Passenger Name Record)."""
    chars = string.ascii_uppercase + string.digits
    return "CS-" + "".join(random.choices(chars, k=6))

@api_bp.route("/airports", methods=["GET"])
def get_airports():
    db = get_db()
    airports = db.execute("SELECT * FROM airports ORDER BY city ASC").fetchall()
    return jsonify([dict(a) for a in airports])

@api_bp.route("/flights/<int:flight_id>/seats", methods=["GET"])
def get_flight_seats(flight_id):
    db = get_db()
    flight = db.execute("SELECT * FROM flights WHERE id = ?", (flight_id,)).fetchone()
    if not flight:
        return jsonify({"error": "Flight not found"}), 404

    seats = db.execute("""
        SELECT id, flight_id, seat_number, cabin_class, seat_type, price_multiplier, is_booked
        FROM seats 
        WHERE flight_id = ?
        ORDER BY 
            CASE cabin_class 
                WHEN 'First' THEN 1 
                WHEN 'Business' THEN 2 
                ELSE 3 
            END,
            CAST(SUBSTR(seat_number, 1, LENGTH(seat_number)-1) AS INTEGER),
            SUBSTR(seat_number, -1)
    """, (flight_id,)).fetchall()

    return jsonify({
        "flight_id": flight_id,
        "flight_number": flight["flight_number"],
        "base_price": flight["base_price"],
        "seats": [dict(s) for s in seats]
    })

@api_bp.route("/bookings", methods=["POST"])
def create_booking():
    """
    Creates a new booking with ACID transaction and double-booking prevention.
    Accepts JSON:
    {
        "flight_id": 1,
        "passenger_name": "Jane Doe",
        "passenger_email": "jane@example.com",
        "passenger_phone": "+1 234 567 890",
        "seat_ids": [10, 11]
    }
    """
    data = request.get_json() or {}
    flight_id = data.get("flight_id")
    passenger_name = data.get("passenger_name", "").strip()
    passenger_email = data.get("passenger_email", "").strip()
    passenger_phone = data.get("passenger_phone", "").strip()
    seat_ids = data.get("seat_ids", [])

    if not flight_id or not passenger_name or not passenger_email or not seat_ids:
        return jsonify({"error": "Missing required fields (flight_id, passenger_name, passenger_email, seat_ids)"}), 400

    if not isinstance(seat_ids, list) or len(seat_ids) == 0:
        return jsonify({"error": "At least one seat must be selected"}), 400

    db = get_db()

    try:
        # Start an IMMEDIATE transaction to prevent concurrent race conditions
        db.execute("BEGIN IMMEDIATE")

        # 1. Verify flight exists
        flight = db.execute("SELECT * FROM flights WHERE id = ?", (flight_id,)).fetchone()
        if not flight:
            db.rollback()
            return jsonify({"error": "Flight not found"}), 404

        base_price = flight["base_price"]
        booked_seats_info = []
        total_amount = 0.0

        # 2. Prevent Double Booking:
        # Check and atomically claim each requested seat
        for seat_id in seat_ids:
            seat = db.execute(
                "SELECT * FROM seats WHERE id = ? AND flight_id = ?", 
                (seat_id, flight_id)
            ).fetchone()

            if not seat:
                db.rollback()
                return jsonify({"error": f"Seat ID {seat_id} not found on this flight"}), 404

            # Attempt atomic update using optimistic concurrency condition (is_booked = 0)
            cursor = db.execute("""
                UPDATE seats 
                SET is_booked = 1, version = version + 1
                WHERE id = ? AND is_booked = 0
            """, (seat_id,))

            # If rowcount is 0, another concurrent transaction has already booked this seat!
            if cursor.rowcount == 0:
                db.rollback()
                return jsonify({
                    "error": f"Seat {seat['seat_number']} was just booked by another passenger. Please select another seat.",
                    "code": "SEAT_ALREADY_BOOKED",
                    "conflict_seat": seat["seat_number"]
                }), 409

            seat_price = round(base_price * seat["price_multiplier"], 2)
            total_amount += seat_price
            booked_seats_info.append({
                "seat_id": seat_id,
                "seat_number": seat["seat_number"],
                "price": seat_price,
                "cabin_class": seat["cabin_class"]
            })

        # 3. Generate unique PNR and insert Booking record
        pnr = generate_pnr()
        cursor = db.execute("""
            INSERT INTO bookings (booking_reference, flight_id, passenger_name, passenger_email, passenger_phone, total_amount, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, 'Confirmed')
        """, (pnr, flight_id, passenger_name, passenger_email, passenger_phone, total_amount))
        
        booking_id = cursor.lastrowid

        # 4. Insert junction records with UNIQUE constraint enforcement
        for s_info in booked_seats_info:
            db.execute("""
                INSERT INTO booking_seats (booking_id, seat_id, flight_id, seat_number, price_paid)
                VALUES (?, ?, ?, ?, ?)
            """, (booking_id, s_info["seat_id"], flight_id, s_info["seat_number"], s_info["price"]))

        # Commit transaction
        db.commit()

        return jsonify({
            "success": True,
            "message": "Booking confirmed successfully!",
            "booking": {
                "id": booking_id,
                "pnr": pnr,
                "flight_number": flight["flight_number"],
                "passenger_name": passenger_name,
                "passenger_email": passenger_email,
                "total_amount": total_amount,
                "seats": [s["seat_number"] for s in booked_seats_info]
            }
        }), 201

    except sqlite3.IntegrityError as e:
        db.rollback()
        return jsonify({
            "error": "A conflict occurred while booking your selected seats. Please re-check seat availability.",
            "details": str(e)
        }), 409
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal booking failure", "details": str(e)}), 500

@api_bp.route("/bookings/<string:pnr>", methods=["GET"])
def get_booking(pnr):
    db = get_db()
    booking = db.execute("""
        SELECT b.*, f.flight_number, f.departure_time, f.arrival_time, f.aircraft_model,
               orig.city AS origin_city, orig.name AS origin_name, orig.code AS origin_code,
               dest.city AS dest_city, dest.name AS dest_name, dest.code AS dest_code
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports orig ON f.origin_code = orig.code
        JOIN airports dest ON f.destination_code = dest.code
        WHERE UPPER(b.booking_reference) = ?
    """, (pnr.strip().upper(),)).fetchone()

    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    seats = db.execute("""
        SELECT bs.*, s.cabin_class, s.seat_type
        FROM booking_seats bs
        JOIN seats s ON bs.seat_id = s.id
        WHERE bs.booking_id = ?
    """, (booking["id"],)).fetchall()

    return jsonify({
        "booking": dict(booking),
        "seats": [dict(s) for s in seats]
    })
