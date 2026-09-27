from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("auth/register.html", name=name, email=email, phone=phone)

        if password != confirm_password:
            flash("Passwords do not match. Please verify.", "error")
            return render_template("auth/register.html", name=name, email=email, phone=phone)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("auth/register.html", name=name, email=email, phone=phone)

        db = get_db()
        existing_user = db.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        if existing_user:
            flash("An account with this email already exists. Please sign in.", "error")
            return redirect(url_for("auth.login"))

        password_hash = generate_password_hash(password)
        cursor = db.execute("""
            INSERT INTO users (name, email, phone, password_hash)
            VALUES (?, ?, ?, ?)
        """, (name, email, phone, password_hash))
        db.commit()

        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email

        flash(f"Welcome to CloudSky Airways, {name}! Your account has been created.", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("auth/login.html", email=email)

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password. Please try again.", "error")
            return render_template("auth/login.html", email=email)

        session['user_id'] = user["id"]
        session['user_name'] = user["name"]
        session['user_email'] = user["email"]

        flash(f"Welcome back, {user['name']}!", "success")
        next_url = request.args.get("next") or url_for("main.index")
        return redirect(next_url)

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "success")
    return redirect(url_for("main.index"))

# REST APIs for client-side Vue auth
@auth_bp.route("/api/auth/me", methods=["GET"])
def get_current_user():
    if 'user_id' in session:
        db = get_db()
        user = db.execute("SELECT id, name, email, phone FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        if user:
            return jsonify({"authenticated": True, "user": dict(user)})
    return jsonify({"authenticated": False, "user": None})

@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session['user_id'] = user["id"]
    session['user_name'] = user["name"]
    session['user_email'] = user["email"]

    return jsonify({
        "success": True,
        "message": "Signed in successfully",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"]
        }
    })

@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "An account with this email already exists"}), 409

    password_hash = generate_password_hash(password)
    cursor = db.execute("""
        INSERT INTO users (name, email, phone, password_hash)
        VALUES (?, ?, ?, ?)
    """, (name, email, phone, password_hash))
    db.commit()

    user_id = cursor.lastrowid
    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email

    return jsonify({
        "success": True,
        "message": "Account created successfully",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone
        }
    }), 201

@auth_bp.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Signed out successfully"})
