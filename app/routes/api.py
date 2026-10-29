import string
import random
import uuid
import datetime
import sqlite3
import json
from flask import Blueprint, jsonify, request, session
from app.db import get_db

api_bp = Blueprint("api", __name__)

def generate_pnr():
    """Generate a unique 6-character airline PNR (Passenger Name Record)."""
    chars = string.ascii_uppercase + string.digits
    return "CS-" + "".join(random.choices(chars, k=6))

# ---------------------------------------------------------------------------
# Dynamic Pricing Engine — Yield Management (Threshold-Based Surge Pricing)
# ---------------------------------------------------------------------------
# Inspired by real airline yield management: as a flight fills up, price
# rises in discrete tiers to maximise revenue from remaining scarce seats.
#
# Tiers (seat occupancy %):
#   < 30% filled  → BASE PRICE     (no surge — encourage early bookings)
#   30% – 59%     → 1.20x SURGE    (low surge label)
#   60% – 84%     → 1.45x SURGE    (medium surge label)
#   ≥ 85% filled  → 1.75x SURGE    (high surge — near-sold-out premium)
# ---------------------------------------------------------------------------
_PRICE_TIERS = [
    (0.85, 1.75, "🔥 High Demand"),
    (0.60, 1.45, "📈 Filling Fast"),
    (0.30, 1.20, "💺 Limited Seats"),
]

def apply_dynamic_pricing(flight_dict):
    """
    Compute surge-adjusted price for a flight dict.
    Adds keys: dynamic_price, original_price, price_surge_pct, price_surge_label.
    Mutates and returns the dict.
    """
    total = flight_dict.get("total_seats") or 0
    available = flight_dict.get("available_seats") or 0
    base_price = flight_dict.get("base_price", 0)

    if total > 0:
        occupancy = (total - available) / total
    else:
        occupancy = 0.0

    multiplier = 1.0
    label = None
    for threshold, mult, lbl in _PRICE_TIERS:
        if occupancy >= threshold:
            multiplier = mult
            label = lbl
            break

    dynamic_price = round(base_price * multiplier)
    flight_dict["original_price"] = base_price
    flight_dict["dynamic_price"] = dynamic_price
    flight_dict["price_surge_pct"] = round((multiplier - 1.0) * 100)
    flight_dict["price_surge_label"] = label
    flight_dict["occupancy_pct"] = round(occupancy * 100)
    return flight_dict

def clean_expired_holds(db):
    """Releases seats whose temporary reservation holds have passed."""
    now_iso = datetime.datetime.now().isoformat()
    db.execute("""
        UPDATE seats 
        SET locked_until = NULL, lock_token = NULL 
        WHERE is_booked = 0 AND locked_until IS NOT NULL AND locked_until < ?
    """, (now_iso,))
    db.commit()

@api_bp.route("/airports", methods=["GET"])
def get_airports():
    db = get_db()
    airports = db.execute("SELECT * FROM airports ORDER BY city ASC").fetchall()
    return jsonify([dict(a) for a in airports])

@api_bp.route("/flights", methods=["GET"])
def get_flights():
    """Returns available scheduled flights with real-time seat counts."""
    db = get_db()
    origin = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()
    date_param = request.args.get("date", "").strip()
    try:
        limit = int(request.args.get("limit", 20))
    except (ValueError, TypeError):
        limit = 20

    query = """
        SELECT f.*, 
               orig.city AS origin_city, orig.name AS origin_name,
               dest.city AS dest_city, dest.name AS dest_name,
               (SELECT COUNT(*) FROM seats s WHERE s.flight_id = f.id AND s.is_booked = 0) AS available_seats
        FROM flights f
        JOIN airports orig ON f.origin_code = orig.code
        JOIN airports dest ON f.destination_code = dest.code
        WHERE 1=1
    """
    params = []

    if origin:
        query += " AND f.origin_code = ?"
        params.append(origin)
    if destination:
        query += " AND f.destination_code = ?"
        params.append(destination)
    if date_param:
        query += " AND f.departure_time LIKE ?"
        params.append(f"{date_param}%")

    query += " ORDER BY f.departure_time ASC LIMIT ?"
    params.append(limit)

    rows = db.execute(query, params).fetchall()

    # Fallback if 0 found with date_param
    if len(rows) == 0 and date_param and (origin or destination):
        fb_query = """
            SELECT f.*, 
                   orig.city AS origin_city, orig.name AS origin_name,
                   dest.city AS dest_city, dest.name AS dest_name,
                   (SELECT COUNT(*) FROM seats s WHERE s.flight_id = f.id AND s.is_booked = 0) AS available_seats
            FROM flights f
            JOIN airports orig ON f.origin_code = orig.code
            JOIN airports dest ON f.destination_code = dest.code
            WHERE 1=1
        """
        fb_params = []
        if origin:
            fb_query += " AND f.origin_code = ?"
            fb_params.append(origin)
        if destination:
            fb_query += " AND f.destination_code = ?"
            fb_params.append(destination)
        fb_query += " ORDER BY f.departure_time ASC LIMIT ?"
        fb_params.append(limit)
        rows = db.execute(fb_query, fb_params).fetchall()

    # Fallback to general flights if still empty
    if len(rows) == 0 and (origin or destination):
        rows = db.execute("""
            SELECT f.*, 
                   orig.city AS origin_city, orig.name AS origin_name,
                   dest.city AS dest_city, dest.name AS dest_name,
                   (SELECT COUNT(*) FROM seats s WHERE s.flight_id = f.id AND s.is_booked = 0) AS available_seats
            FROM flights f
            JOIN airports orig ON f.origin_code = orig.code
            JOIN airports dest ON f.destination_code = dest.code
            ORDER BY f.departure_time ASC LIMIT ?
        """, (limit,)).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        d["dest_code"] = d.get("destination_code", "")
        dep = str(d.get("departure_time", ""))
        arr = str(d.get("arrival_time", ""))
        d["departure_date"] = dep[:10] if len(dep) >= 10 else dep
        d["date"] = d["departure_date"]
        d["departure_hour"] = dep[11:16] if len(dep) >= 16 else dep
        d["arrival_hour"] = arr[11:16] if len(arr) >= 16 else arr
        # Apply yield-management dynamic pricing
        apply_dynamic_pricing(d)
        result.append(d)

    return jsonify(result)

@api_bp.route("/flights/<int:flight_id>/seats", methods=["GET"])
def get_flight_seats(flight_id):
    """
    Returns complete live aircraft cabin seats enriched with
    rich amenity metadata (seat pitch, power outlets, extra legroom flags, recline angle, features list).
    Supports optional query filters: ?cabin_class=First|Business|Economy & ?seat_type=Window|Aisle|Exit Row & ?extra_legroom=1
    """
    db = get_db()
    clean_expired_holds(db)

    flight = db.execute("SELECT * FROM flights WHERE id = ?", (flight_id,)).fetchone()
    if not flight:
        return jsonify({"error": "Flight not found"}), 404

    client_token = request.args.get("lock_token", "")
    cabin_class_filter = request.args.get("cabin_class", "").strip()
    seat_type_filter = request.args.get("seat_type", "").strip()
    extra_legroom_filter = request.args.get("extra_legroom", "").strip()

    now_iso = datetime.datetime.now().isoformat()

    seats = db.execute("""
        SELECT id, flight_id, seat_number, cabin_class, seat_type, price_multiplier,
               seat_pitch, has_power, has_extra_legroom, recline_deg, features,
               is_booked, locked_until, lock_token
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

    seat_list = []
    for s in seats:
        seat_dict = dict(s)

        # Check if held by someone else
        is_held = False
        if not seat_dict["is_booked"] and seat_dict["locked_until"]:
            if seat_dict["locked_until"] > now_iso:
                is_held = (seat_dict["lock_token"] != client_token)

        seat_dict["is_held"] = is_held
        seat_dict["price_inr"] = round(flight["base_price"] * seat_dict["price_multiplier"])
        
        # Format feature tags as a clean list
        feat_str = seat_dict.get("features") or ""
        seat_dict["features_list"] = [f.strip() for f in feat_str.split(",") if f.strip()]

        # Don't expose other people's lock tokens
        seat_dict.pop("lock_token", None)

        # Optional query filters
        if cabin_class_filter and seat_dict["cabin_class"].lower() != cabin_class_filter.lower():
            continue
        if seat_type_filter and seat_dict["seat_type"].lower() != seat_type_filter.lower():
            continue
        if extra_legroom_filter in ("1", "true", "True") and not seat_dict.get("has_extra_legroom"):
            continue

        seat_list.append(seat_dict)

    return jsonify({
        "flight_id": flight_id,
        "flight_number": flight["flight_number"],
        "aircraft_model": flight["aircraft_model"],
        "base_price_inr": flight["base_price"],
        "total_seats": len(seat_list),
        "seats": seat_list
    })

@api_bp.route("/seats/hold", methods=["POST"])
def hold_seats():
    """
    Day 2 Feature: Holds seats for 5 minutes during passenger checkout.
    Payload: { "flight_id": 1, "seat_ids": [12, 13], "lock_token": "uuid" }
    """
    data = request.get_json() or {}
    flight_id = data.get("flight_id")
    seat_ids = data.get("seat_ids", [])
    lock_token = data.get("lock_token") or str(uuid.uuid4())

    if not flight_id or not seat_ids or not isinstance(seat_ids, list):
        return jsonify({"error": "flight_id and list of seat_ids required"}), 400

    db = get_db()
    clean_expired_holds(db)

    now = datetime.datetime.now()
    hold_expires = now + datetime.timedelta(minutes=5)
    now_iso = now.isoformat()
    expires_iso = hold_expires.isoformat()

    try:
        db.execute("BEGIN IMMEDIATE")

        for seat_id in seat_ids:
            seat = db.execute("SELECT * FROM seats WHERE id = ? AND flight_id = ?", (seat_id, flight_id)).fetchone()
            if not seat:
                db.rollback()
                return jsonify({"error": f"Seat ID {seat_id} not found"}), 404

            if seat["is_booked"]:
                db.rollback()
                return jsonify({"error": f"Seat {seat['seat_number']} is already booked", "code": "SEAT_BOOKED"}), 409

            if seat["locked_until"] and seat["locked_until"] > now_iso and seat["lock_token"] != lock_token:
                db.rollback()
                return jsonify({"error": f"Seat {seat['seat_number']} is currently being held by another passenger", "code": "SEAT_HELD"}), 409

            # Apply 5-minute hold
            db.execute("""
                UPDATE seats 
                SET locked_until = ?, lock_token = ?, version = version + 1
                WHERE id = ? AND is_booked = 0
            """, (expires_iso, lock_token, seat_id))

        db.commit()
        return jsonify({
            "success": True,
            "lock_token": lock_token,
            "expires_at": expires_iso,
            "hold_seconds": 300,
            "message": "Seats held for 5 minutes"
        })

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to hold seats", "details": str(e)}), 500

@api_bp.route("/seats/release", methods=["POST"])
def release_seats():
    """Releases seats if passenger abandons checkout or deselects."""
    data = request.get_json() or {}
    lock_token = data.get("lock_token")
    if not lock_token:
        return jsonify({"error": "lock_token required"}), 400

    db = get_db()
    db.execute("""
        UPDATE seats 
        SET locked_until = NULL, lock_token = NULL 
        WHERE lock_token = ? AND is_booked = 0
    """, (lock_token,))
    db.commit()
    return jsonify({"success": True, "message": "Seats released"})

@api_bp.route("/bookings", methods=["POST"])
def create_booking():
    """
    Day 3: Creates a confirmed booking with atomic seat reservation in Indian Rupees (₹).
    Supports multi-passenger ticket engine, mapping individual passenger names/ages/genders to each seat.
    """
    data = request.get_json() or {}
    flight_id = data.get("flight_id")
    passenger_name = data.get("passenger_name", "").strip()
    passenger_email = data.get("passenger_email", "").strip()
    passenger_phone = data.get("passenger_phone", "").strip()
    seat_ids = data.get("seat_ids", [])
    lock_token = data.get("lock_token", "")
    passengers = data.get("passengers", [])  # Array: [{ seat_id, name, age, gender }]

    # Fallback: if top-level passenger_name is empty but passengers array has a name
    if not passenger_name and isinstance(passengers, list) and len(passengers) > 0:
        first_p = passengers[0] if isinstance(passengers[0], dict) else {}
        passenger_name = first_p.get("name", "").strip()

    if not flight_id or not passenger_name or not passenger_email or not seat_ids:
        return jsonify({"error": "Missing required fields"}), 400

    if not isinstance(seat_ids, list) or len(seat_ids) == 0:
        return jsonify({"error": "At least one seat must be selected"}), 400

    # Build passenger lookup map by seat_id or index
    passenger_map = {}
    if isinstance(passengers, list):
        for idx, p in enumerate(passengers):
            if isinstance(p, dict):
                sid = p.get("seat_id")
                if sid is not None:
                    passenger_map[sid] = p
                elif idx < len(seat_ids):
                    passenger_map[seat_ids[idx]] = p

    db = get_db()
    now_iso = datetime.datetime.now().isoformat()

    try:
        db.execute("BEGIN IMMEDIATE")

        flight = db.execute("SELECT * FROM flights WHERE id = ?", (flight_id,)).fetchone()
        if not flight:
            db.rollback()
            return jsonify({"error": "Flight not found"}), 404

        base_price = flight["base_price"]
        booked_seats_info = []
        total_amount = 0.0

        for idx, seat_id in enumerate(seat_ids):
            seat = db.execute("SELECT * FROM seats WHERE id = ? AND flight_id = ?", (seat_id, flight_id)).fetchone()
            if not seat:
                db.rollback()
                return jsonify({"error": f"Seat ID {seat_id} not found"}), 404

            # Check if occupied or locked by someone else
            if seat["is_booked"]:
                db.rollback()
                return jsonify({
                    "error": f"Seat {seat['seat_number']} is already booked by another passenger.",
                    "code": "SEAT_ALREADY_BOOKED"
                }), 409

            if seat["locked_until"] and seat["locked_until"] > now_iso and seat["lock_token"] and seat["lock_token"] != lock_token:
                db.rollback()
                return jsonify({
                    "error": f"Seat {seat['seat_number']} is currently held in another checkout.",
                    "code": "SEAT_HELD"
                }), 409

            # Atomic claim and transition to booked
            cursor = db.execute("""
                UPDATE seats 
                SET is_booked = 1, locked_until = NULL, lock_token = NULL, version = version + 1
                WHERE id = ? AND is_booked = 0
            """, (seat_id,))

            if cursor.rowcount == 0:
                db.rollback()
                return jsonify({
                    "error": f"Seat {seat['seat_number']} was just claimed by another passenger.",
                    "code": "SEAT_ALREADY_BOOKED"
                }), 409

            seat_price = round(base_price * seat["price_multiplier"])
            total_amount += seat_price

            p_data = passenger_map.get(seat_id, {})
            p_name = p_data.get("name", "").strip() or (passenger_name if idx == 0 else f"Passenger {idx + 1}")
            p_age_raw = p_data.get("age")
            try:
                p_age = int(p_age_raw) if p_age_raw is not None and str(p_age_raw).strip() != "" else None
            except (ValueError, TypeError):
                p_age = None
            p_gender = p_data.get("gender", "").strip() or ""

            booked_seats_info.append({
                "seat_id": seat_id,
                "seat_number": seat["seat_number"],
                "price": seat_price,
                "cabin_class": seat["cabin_class"],
                "seat_type": seat["seat_type"],
                "passenger_name": p_name,
                "passenger_age": p_age,
                "passenger_gender": p_gender
            })

        user_id = session.get("user_id") or data.get("user_id")
        pnr = generate_pnr()
        payment_method = data.get("payment_method", "UPI")
        payment_details = data.get("payment_details", "")
        transaction_id = "TXN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

        cursor = db.execute("""
            INSERT INTO bookings (user_id, booking_reference, flight_id, passenger_name, passenger_email, passenger_phone, total_amount, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmed')
        """, (user_id, pnr, flight_id, passenger_name, passenger_email, passenger_phone, total_amount))
        
        booking_id = cursor.lastrowid

        # Insert Payment Transaction Record
        p_details_str = json.dumps(payment_details) if isinstance(payment_details, dict) else str(payment_details)
        db.execute("""
            INSERT INTO payments (booking_id, transaction_id, payment_method, amount, currency, status, payment_details)
            VALUES (?, ?, ?, ?, 'INR', 'Success', ?)
        """, (booking_id, transaction_id, payment_method, total_amount, p_details_str))

        for s_info in booked_seats_info:
            db.execute("""
                INSERT INTO booking_seats (booking_id, seat_id, flight_id, seat_number, price_paid, passenger_name, passenger_age, passenger_gender)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                booking_id,
                s_info["seat_id"],
                flight_id,
                s_info["seat_number"],
                s_info["price"],
                s_info["passenger_name"],
                s_info["passenger_age"],
                s_info["passenger_gender"]
            ))

        db.commit()

        # Compute realistic gate, terminal & boarding time for instant pass
        term = f"T{((flight_id % 2) + 2)}" if flight["origin_code"] in ("DEL", "BOM") else "T1"
        gate_letter = ['A', 'B', 'C', 'D'][(flight_id * 3) % 4]
        gate_num = ((flight_id * 7) % 24) + 1
        gate = f"{gate_num}{gate_letter}"

        try:
            dep_dt = datetime.datetime.strptime(flight["departure_time"], "%Y-%m-%d %H:%M")
            boarding_time = (dep_dt - datetime.timedelta(minutes=45)).strftime("%H:%M")
        except Exception:
            boarding_time = "45m prior"

        return jsonify({
            "success": True,
            "message": "Payment authorized and booking confirmed successfully!",
            "booking": {
                "id": booking_id,
                "pnr": pnr,
                "flight_number": flight["flight_number"],
                "passenger_name": passenger_name,
                "passenger_email": passenger_email,
                "passenger_phone": passenger_phone,
                "total_amount_inr": total_amount,
                "payment_status": "Confirmed",
                "payment_method": payment_method,
                "transaction_id": transaction_id,
                "terminal": term,
                "gate": gate,
                "boarding_time": boarding_time,
                "seats": [s["seat_number"] for s in booked_seats_info],
                "passengers": [
                    {
                        "seat_id": s["seat_id"],
                        "seat_number": s["seat_number"],
                        "passenger_name": s["passenger_name"],
                        "passenger_age": s["passenger_age"],
                        "passenger_gender": s["passenger_gender"],
                        "cabin_class": s["cabin_class"],
                        "price_inr": s["price"],
                        "terminal": term,
                        "gate": gate,
                        "boarding_time": boarding_time,
                        "boarding_group": "Group 1" if s["cabin_class"] in ("First", "Business") else "Group 2"
                    }
                    for s in booked_seats_info
                ]
            }
        }), 201

    except sqlite3.IntegrityError as e:
        db.rollback()
        return jsonify({"error": "Database constraint prevented duplicate seat booking.", "details": str(e)}), 409
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal booking failure", "details": str(e)}), 500

@api_bp.route("/bookings/<string:pnr>", methods=["GET"])
def get_booking(pnr):
    db = get_db()
    clean_expired_holds(db)

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
        SELECT bs.*, s.cabin_class, s.seat_type, s.seat_pitch, s.has_power, s.has_extra_legroom, s.recline_deg, s.features
        FROM booking_seats bs
        JOIN seats s ON bs.seat_id = s.id
        WHERE bs.booking_id = ?
    """, (booking["id"],)).fetchall()

    payment = db.execute("""
        SELECT * FROM payments 
        WHERE booking_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (booking["id"],)).fetchone()

    # Dynamic gate & boarding calculation
    term = f"T{((booking['flight_id'] % 2) + 2)}" if booking["origin_code"] in ("DEL", "BOM") else "T1"
    gate_letter = ['A', 'B', 'C', 'D'][(booking["flight_id"] * 3) % 4]
    gate_num = ((booking["flight_id"] * 7) % 24) + 1
    gate = f"{gate_num}{gate_letter}"

    try:
        dep_dt = datetime.datetime.strptime(booking["departure_time"], "%Y-%m-%d %H:%M")
        boarding_time = (dep_dt - datetime.timedelta(minutes=45)).strftime("%H:%M")
    except Exception:
        boarding_time = "45m prior"

    booking_dict = dict(booking)
    booking_dict["terminal"] = term
    booking_dict["gate"] = gate
    booking_dict["boarding_time"] = boarding_time
    booking_dict["payment"] = dict(payment) if payment else None

    # Attach boarding pass info to individual passenger seats
    seats_list = []
    if seats:
        for s in seats:
            sd = dict(s)
            sd["terminal"] = term
            sd["gate"] = gate
            sd["boarding_time"] = boarding_time
            sd["boarding_group"] = "Group 1" if sd.get("cabin_class") in ("First", "Business") else "Group 2"
            seats_list.append(sd)
    elif booking["payment_status"] == "Cancelled" and booking["cancellation_details"]:
        try:
            raw_seats = json.loads(booking["cancellation_details"])
            for s in raw_seats:
                sd = dict(s)
                sd["terminal"] = term
                sd["gate"] = gate
                sd["boarding_time"] = boarding_time
                sd["boarding_group"] = "Group 1" if sd.get("cabin_class") in ("First", "Business") else "Group 2"
                seats_list.append(sd)
        except Exception:
            pass

    return jsonify({
        "booking": booking_dict,
        "seats": seats_list
    })

@api_bp.route("/bookings/<string:pnr>/cancel", methods=["POST"])
def cancel_booking(pnr):
    """
    Cancels a booking reservation, frees up seats back to inventory atomically,
    calculates cancellation fee and refund, and records payment refund.
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    db = get_db()
    booking = db.execute("""
        SELECT b.*, f.flight_number 
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        WHERE UPPER(b.booking_reference) = ?
    """, (pnr.strip().upper(),)).fetchone()

    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if email and booking["passenger_email"].strip().lower() != email:
        return jsonify({"error": "Email does not match booking record."}), 403

    if booking["payment_status"] == "Cancelled":
        return jsonify({"error": "Booking has already been cancelled."}), 400

    try:
        db.execute("BEGIN IMMEDIATE")

        # 1. Fetch booked seats
        booked_seats = db.execute("""
            SELECT bs.seat_id, bs.seat_number, bs.price_paid, bs.passenger_name, bs.passenger_age, bs.passenger_gender,
                   s.cabin_class, s.seat_type, s.seat_pitch, s.has_power, s.has_extra_legroom, s.recline_deg, s.features
            FROM booking_seats bs
            JOIN seats s ON bs.seat_id = s.id
            WHERE bs.booking_id = ?
        """, (booking["id"],)).fetchall()

        seat_ids = [s["seat_id"] for s in booked_seats]
        seat_numbers = [s["seat_number"] for s in booked_seats]
        seats_snapshot = json.dumps([dict(s) for s in booked_seats])

        # 2. Free seats immediately back to inventory
        if seat_ids:
            placeholders = ",".join("?" for _ in seat_ids)
            db.execute(f"""
                UPDATE seats 
                SET is_booked = 0, locked_until = NULL, lock_token = NULL, version = version + 1
                WHERE id IN ({placeholders})
            """, seat_ids)

        # 3. Release seat mapping from booking_seats so the freed seats can be re-booked
        db.execute("DELETE FROM booking_seats WHERE booking_id = ?", (booking["id"],))

        # 4. Calculate refund and cancellation charge
        total_fare = float(booking["total_amount"])
        pax_count = max(1, len(seat_ids))
        cancellation_fee = min(total_fare, 500.0 * pax_count)
        refund_amount = round(max(0.0, total_fare - cancellation_fee), 2)
        now_iso = datetime.datetime.now().isoformat()

        # 5. Update booking status
        db.execute("""
            UPDATE bookings 
            SET payment_status = 'Cancelled', cancellation_fee = ?, refund_amount = ?, cancelled_at = ?, cancellation_details = ?
            WHERE id = ?
        """, (cancellation_fee, refund_amount, now_iso, seats_snapshot, booking["id"]))

        # 5. Record refund transaction in payments
        refund_txn = "REF-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        db.execute("""
            INSERT INTO payments (booking_id, transaction_id, payment_method, amount, currency, status, payment_details)
            VALUES (?, ?, 'Refund', ?, 'INR', 'Refunded', ?)
        """, (booking["id"], refund_txn, refund_amount, f"Refund to original source for {pnr}"))

        db.commit()

        return jsonify({
            "success": True,
            "message": f"Booking {pnr} has been successfully cancelled. Seats have been returned to available inventory.",
            "cancellation": {
                "pnr": pnr,
                "flight_number": booking["flight_number"],
                "seats_freed": seat_numbers,
                "total_fare_inr": total_fare,
                "cancellation_fee_inr": cancellation_fee,
                "refund_amount_inr": refund_amount,
                "refund_transaction_id": refund_txn,
                "cancelled_at": now_iso
            }
        })

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to cancel booking", "details": str(e)}), 500

@api_bp.route("/bookings/<string:pnr>/change-seat", methods=["POST"])
def change_seat(pnr):
    """
    Atomically reassigns a passenger from an existing seat to a new available seat on the same flight.
    """
    data = request.get_json() or {}
    old_seat_id = data.get("old_seat_id")
    new_seat_id = data.get("new_seat_id")

    if not old_seat_id or not new_seat_id:
        return jsonify({"error": "old_seat_id and new_seat_id required"}), 400

    db = get_db()
    booking = db.execute("SELECT * FROM bookings WHERE UPPER(booking_reference) = ?", (pnr.strip().upper(),)).fetchone()
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking["payment_status"] == "Cancelled":
        return jsonify({"error": "Cannot change seats on a cancelled booking"}), 400

    try:
        db.execute("BEGIN IMMEDIATE")

        # Verify old seat belongs to this booking
        bs = db.execute("SELECT * FROM booking_seats WHERE booking_id = ? AND seat_id = ?", (booking["id"], old_seat_id)).fetchone()
        if not bs:
            db.rollback()
            return jsonify({"error": "Specified current seat is not part of this booking"}), 404

        # Verify new seat is on the same flight and available
        new_seat = db.execute("SELECT * FROM seats WHERE id = ? AND flight_id = ?", (new_seat_id, booking["flight_id"])).fetchone()
        if not new_seat:
            db.rollback()
            return jsonify({"error": "Target seat not found on this flight"}), 404

        if new_seat["is_booked"]:
            db.rollback()
            return jsonify({"error": f"Target seat {new_seat['seat_number']} is already occupied"}), 409

        # Atomic seat swap
        db.execute("UPDATE seats SET is_booked = 0, locked_until = NULL, lock_token = NULL WHERE id = ?", (old_seat_id,))
        db.execute("UPDATE seats SET is_booked = 1, locked_until = NULL, lock_token = NULL WHERE id = ?", (new_seat_id,))

        flight = db.execute("SELECT base_price FROM flights WHERE id = ?", (booking["flight_id"],)).fetchone()
        new_price = round(flight["base_price"] * new_seat["price_multiplier"])

        db.execute("""
            UPDATE booking_seats 
            SET seat_id = ?, seat_number = ?, price_paid = ?
            WHERE id = ?
        """, (new_seat_id, new_seat["seat_number"], new_price, bs["id"]))

        db.commit()

        return jsonify({
            "success": True,
            "message": f"Seat successfully updated to {new_seat['seat_number']}",
            "old_seat": bs["seat_number"],
            "new_seat": new_seat["seat_number"],
            "cabin_class": new_seat["cabin_class"],
            "new_price_inr": new_price
        })

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Seat change failed", "details": str(e)}), 500

@api_bp.route("/payments/simulate", methods=["POST"])
def simulate_payment():
    """Simulates instant Indian payment gateway authorization for UPI, Cards, and Net Banking."""
    data = request.get_json() or {}
    method = data.get("method", "UPI")
    amount = data.get("amount", 0)

    # Basic method validation
    if method == "UPI":
        vpa = data.get("vpa", "").strip()
        if not vpa or "@" not in vpa:
            return jsonify({"success": False, "error": "Invalid UPI ID. Format should be username@bank"}), 400
    elif method in ("CreditCard", "DebitCard", "Card"):
        card_num = str(data.get("card_number", "")).replace(" ", "")
        if len(card_num) < 15 or not card_num.isdigit():
            return jsonify({"success": False, "error": "Invalid Card Number. Must be 15 or 16 digits."}), 400
    elif method == "NetBanking":
        bank = data.get("bank", "").strip()
        if not bank:
            return jsonify({"success": False, "error": "Please select a participating Indian bank."}), 400

    txn_id = "TXN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return jsonify({
        "success": True,
        "transaction_id": txn_id,
        "status": "Authorized",
        "gateway": "National Payments Corporation of India (NPCI) Gateway Simulator",
        "amount_inr": amount
    })
