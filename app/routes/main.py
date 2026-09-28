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

    featured_flights_data = []
    for f in featured_flights:
        d = dict(f)
        d["dest_code"] = d.get("destination_code", "")
        dep = str(d.get("departure_time", ""))
        arr = str(d.get("arrival_time", ""))
        d["departure_date"] = dep[:10] if len(dep) >= 10 else dep
        d["date"] = d["departure_date"]
        d["departure_hour"] = dep[11:16] if len(dep) >= 16 else dep
        d["arrival_hour"] = arr[11:16] if len(arr) >= 16 else arr
        featured_flights_data.append(d)

    return render_template(
        "index.html",
        airports=airports,
        featured_flights=featured_flights,
        featured_flights_json=featured_flights_data
    )

@main_bp.route("/flights")
def flights_search():
    origin = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()
    departure_date = request.args.get("date", "").strip()

    db = get_db()
    base_query = """
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
    query = base_query

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

    # Fallback 1: If specific departure_date yielded 0 results, check other dates on this route
    if len(flights) == 0 and departure_date and (origin or destination):
        fallback_query = base_query
        fallback_params = []
        if origin:
            fallback_query += " AND f.origin_code = ?"
            fallback_params.append(origin)
        if destination:
            fallback_query += " AND f.destination_code = ?"
            fallback_params.append(destination)
        fallback_query += " ORDER BY f.departure_time ASC LIMIT 20"
        fallback_flights = db.execute(fallback_query, fallback_params).fetchall()
        if len(fallback_flights) > 0:
            flights = fallback_flights

    # Fallback 2: If completely 0 flights (e.g. route has no direct flights), show all scheduled flights
    if len(flights) == 0 and (origin or destination):
        all_flights = db.execute(base_query + " ORDER BY f.departure_time ASC LIMIT 20").fetchall()
        if len(all_flights) > 0:
            flights = all_flights

    airports = db.execute("SELECT * FROM airports ORDER BY city ASC").fetchall()
    flights_data = [dict(f) for f in flights]
    for d in flights_data:
        d["dest_code"] = d.get("destination_code", "")

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
    pnr_param = request.args.get("pnr", "").strip().upper()

    pnr = ""
    email = ""

    if request.method == "POST":
        pnr = request.form.get("pnr", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
    elif pnr_param:
        pnr = pnr_param

    if pnr:
        db = get_db()
        query = """
            SELECT b.*, f.flight_number, f.departure_time, f.arrival_time, f.aircraft_model,
                   orig.city AS origin_city, orig.code AS origin_code,
                   dest.city AS dest_city, dest.code AS dest_code
            FROM bookings b
            JOIN flights f ON b.flight_id = f.id
            JOIN airports orig ON f.origin_code = orig.code
            JOIN airports dest ON f.destination_code = dest.code
            WHERE UPPER(b.booking_reference) = ?
        """
        params = [pnr]
        if email:
            query += " AND LOWER(b.passenger_email) = ?"
            params.append(email)

        booking = db.execute(query, params).fetchone()
        if booking:
            seats = db.execute("""
                SELECT bs.*, s.cabin_class, s.seat_type
                FROM booking_seats bs
                JOIN seats s ON bs.seat_id = s.id
                WHERE bs.booking_id = ?
            """, (booking["id"],)).fetchall()
        elif request.method == "POST":
            error = "No booking found with this Reference Code and Email combination."
        elif pnr_param:
            error = f"No booking found matching reservation reference {pnr_param}."

    return render_template("manage.html", booking=booking, seats=seats, error=error, initial_pnr=pnr)
