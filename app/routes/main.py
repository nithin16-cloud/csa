from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    db = get_db()
    airports = db.execute("SELECT * FROM airports ORDER BY city ASC").fetchall()
    featured_flights = db.execute("""
        SELECT f.*, 
               orig.city AS origin_city, orig.name AS origin_name,
               dest.city AS dest_city, dest.name AS dest_name,
               (SELECT COUNT(*) FROM seats s WHERE s.flight_id = f.id AND s.is_booked = 0) AS available_seats
        FROM flights f
        JOIN airports orig ON f.origin_code = orig.code
        JOIN airports dest ON f.destination_code = dest.code
        ORDER BY f.departure_time ASC
        LIMIT 6
    """).fetchall()
    return render_template("index.html", airports=airports, featured_flights=featured_flights)

@main_bp.route("/flights")
def flights_search():
    origin = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()
    departure_date = request.args.get("date", "").strip()

    db = get_db()
    query = """
        SELECT f.*, 
               orig.city AS origin_city, orig.name AS origin_name,
               dest.city AS dest_city, dest.name AS dest_name,
               (SELECT COUNT(*) FROM seats s WHERE s.flight_id = f.id AND s.is_booked = 0) AS available_seats,
               (SELECT COUNT(*) FROM seats s WHERE s.flight_id = f.id) AS total_seats
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
    if departure_date:
        query += " AND f.departure_time LIKE ?"
        params.append(f"{departure_date}%")

    query += " ORDER BY f.departure_time ASC"

    flights = db.execute(query, params).fetchall()
    airports = db.execute("SELECT * FROM airports ORDER BY city ASC").fetchall()
    flights_data = [dict(f) for f in flights]

    return render_template(
        "flights.html",
        flights=flights_data,
        flights_json=flights_data,
        airports=airports,
        search_origin=origin,
        search_destination=destination,
        search_date=departure_date
    )

@main_bp.route("/booking/<int:flight_id>")
def booking_view(flight_id):
    db = get_db()
    flight = db.execute("""
        SELECT f.*, 
               orig.city AS origin_city, orig.name AS origin_name,
               dest.city AS dest_city, dest.name AS dest_name
        FROM flights f
        JOIN airports orig ON f.origin_code = orig.code
        JOIN airports dest ON f.destination_code = dest.code
        WHERE f.id = ?
    """, (flight_id,)).fetchone()

    if not flight:
        flash("Flight not found", "error")
        return redirect(url_for("main.index"))

    return render_template("booking.html", flight=flight)

@main_bp.route("/manage", methods=["GET", "POST"])
def manage():
    booking = None
    seats = []
    error = None

    if request.method == "POST":
        pnr = request.form.get("pnr", "").strip().upper()
        email = request.form.get("email", "").strip().lower()

        db = get_db()
        booking = db.execute("""
            SELECT b.*, f.flight_number, f.departure_time, f.arrival_time, f.aircraft_model,
                   orig.city AS origin_city, orig.code AS origin_code,
                   dest.city AS dest_city, dest.code AS dest_code
            FROM bookings b
            JOIN flights f ON b.flight_id = f.id
            JOIN airports orig ON f.origin_code = orig.code
            JOIN airports dest ON f.destination_code = dest.code
            WHERE UPPER(b.booking_reference) = ? AND LOWER(b.passenger_email) = ?
        """, (pnr, email)).fetchone()

        if booking:
            seats = db.execute("""
                SELECT bs.*, s.cabin_class, s.seat_type
                FROM booking_seats bs
                JOIN seats s ON bs.seat_id = s.id
                WHERE bs.booking_id = ?
            """, (booking["id"],)).fetchall()
        else:
            error = "No booking found with this Reference Code and Email combination."

    return render_template("manage.html", booking=booking, seats=seats, error=error)
