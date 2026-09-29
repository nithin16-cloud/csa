import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db

logger = logging.getLogger("cloudsky.auth")
auth_bp = Blueprint("auth", __name__)

def verify_user_password(password_hash, candidate_password):
    """
    Verifies user password with tolerance for accidental mobile autocomplete
    whitespace while strictly preserving security.
    """
    if not password_hash or not candidate_password:
        return False
    # 1. Exact match test
    if check_password_hash(password_hash, candidate_password):
        return True
    # 2. Trimmed match test (protects users from accidental spacebar / mobile keyboard autofill spaces)
    trimmed = candidate_password.strip()
    if trimmed != candidate_password and check_password_hash(password_hash, trimmed):
        return True
    return False

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

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
        existing_user = db.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email,)).fetchone()
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
        session.permanent = True
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        session['user'] = {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone
        }

        logger.info("[AUTH REGISTER] New user created successfully: ID=%s, Email='%s', Name='%s'", user_id, email, name)
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
        user = db.execute("SELECT * FROM users WHERE LOWER(TRIM(email)) = ?", (email,)).fetchone()

        if not user:
            total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            logger.warning("[AUTH LOGIN FAILED] Email '%s' not found. Total registered users in database: %s", email, total_users)
            flash("Invalid email or password. No account found with this email. Please check your spelling or sign up.", "error")
            return render_template("auth/login.html", email=email)

        if not verify_user_password(user["password_hash"], password):
            logger.warning("[AUTH LOGIN FAILED] Incorrect password for user ID=%s, Email='%s'", user["id"], email)
            flash("Invalid email or password. The password entered is incorrect.", "error")
            return render_template("auth/login.html", email=email)

        if request.form.get("remember"):
            session.permanent = True

        session['user_id'] = user["id"]
        session['user_name'] = user["name"]
        session['user_email'] = user["email"]
        session['user'] = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"]
        }

        logger.info("[AUTH LOGIN SUCCESS] User logged in: ID=%s, Email='%s'", user["id"], email)
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
    user = db.execute("SELECT * FROM users WHERE LOWER(TRIM(email)) = ?", (email,)).fetchone()

    if not user:
        return jsonify({"error": "Invalid email or password. No account found with this email."}), 401

    if not verify_user_password(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password. Incorrect password."}), 401

    session.permanent = True
    session['user_id'] = user["id"]
    session['user_name'] = user["name"]
    session['user_email'] = user["email"]
    session['user'] = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user["phone"]
    }

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
    password = data.get("password", "").strip()

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = ?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "An account with this email already exists"}), 409

    password_hash = generate_password_hash(password)
    cursor = db.execute("""
        INSERT INTO users (name, email, phone, password_hash)
        VALUES (?, ?, ?, ?)
    """, (name, email, phone, password_hash))
    db.commit()

    user_id = cursor.lastrowid
    session.permanent = True
    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email
    session['user'] = {
        "id": user_id,
        "name": name,
        "email": email,
        "phone": phone
    }

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

@auth_bp.route("/admin/users", methods=["GET"])
def admin_users_view():
    """
    Direct web dashboard for viewing registered user emails, details,
    downloading the database, and resetting passwords for free tier.
    """
    import os
    from flask import current_app
    secret_key = current_app.config.get("SECRET_KEY", "cloudsky-dev-secret-key-12345")
    key = request.args.get("key", "").strip()

    is_admin_session = session.get("user_email") in [
        "rohan.sharma@example.in",
        os.getenv("ADMIN_EMAIL", "").strip().lower()
    ]

    if not is_admin_session and key != secret_key:
        return jsonify({
            "error": "Unauthorized",
            "hint": "To view registered users, append ?key=<YOUR_SECRET_KEY> to the URL or sign in with an admin account."
        }), 403

    db = get_db()
    users = db.execute("SELECT id, name, email, phone, created_at FROM users ORDER BY id ASC").fetchall()
    users_list = [dict(u) for u in users]

    if "text/html" in request.headers.get("Accept", "") and not request.args.get("json"):
        active_key = key if key else secret_key
        messages_html = ""
        for cat, msg in session.pop('_flashes', []):
            color = "#10b981" if cat == "success" else "#ef4444"
            messages_html += f"<div style='background: {color}22; border-left: 4px solid {color}; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; color: #f8fafc; font-size: 13px;'>{msg}</div>"

        rows_html = "".join([
            f"""<tr style='border-bottom: 1px solid #334155;'>
                <td style='padding: 10px;'>{u['id']}</td>
                <td style='padding: 10px; font-weight: 600;'>{u['name']}</td>
                <td style='padding: 10px; color: #38bdf8;'>{u['email']}</td>
                <td style='padding: 10px;'>{u['phone'] or '—'}</td>
                <td style='padding: 10px; color: #94a3b8; font-size: 12px;'>{u['created_at']}</td>
                <td style='padding: 10px;'>
                    <form action='/admin/reset-password' method='POST' style='display: flex; gap: 6px; align-items: center; margin: 0;'>
                        <input type='hidden' name='key' value='{active_key}'>
                        <input type='hidden' name='user_id' value='{u['id']}'>
                        <input type='text' name='new_password' placeholder='New password' required style='padding: 4px 8px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; width: 110px; font-size: 12px;'>
                        <button type='submit' style='background: #2563eb; color: #fff; border: none; padding: 5px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600;'>Set Password</button>
                    </form>
                </td>
            </tr>"""
            for u in users_list
        ])

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CloudSky Admin — Registered Users & Credentials</title>
        </head>
        <body style="background: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; padding: 24px; margin: 0;">
            <div style="max-width: 1020px; margin: 0 auto; background: #1e293b; padding: 28px; border-radius: 14px; border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 18px; flex-wrap: wrap; gap: 12px;">
                    <div>
                        <h2 style="margin: 0; color: #38bdf8; font-size: 24px;">CloudSky Passenger Database</h2>
                        <span style="color: #94a3b8; font-size: 13px;">Free-Tier Render Admin Console &bull; SQLite Database (<code>cloudsky.db</code>)</span>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <a href="/admin/download-db?key={active_key}" style="background: #059669; color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">
                            📥 Download Database (.db)
                        </a>
                        <span style="background: #0369a1; color: #e0f2fe; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: bold;">{len(users_list)} Registered User(s)</span>
                    </div>
                </div>

                {messages_html}

                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                        <thead>
                            <tr style="border-bottom: 2px solid #475569; color: #94a3b8;">
                                <th style="padding: 10px;">ID</th>
                                <th style="padding: 10px;">Full Name</th>
                                <th style="padding: 10px;">Gmail / Email</th>
                                <th style="padding: 10px;">Phone</th>
                                <th style="padding: 10px;">Registered Date</th>
                                <th style="padding: 10px;">Set Known Password</th>
                            </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>

                <div style="margin-top: 24px; padding: 16px; background: #0f172a; border-radius: 8px; border: 1px solid #334155; font-size: 13px; color: #94a3b8; line-height: 1.6;">
                    <strong style="color: #f8fafc;">💡 Security & Credentials Note:</strong><br>
                    Passwords in modern web standards are stored as irreversible cryptographic hashes (e.g., <code>scrypt:...</code>) to protect user security. If you need to test logging in with any user account above, type a new password in the <strong>Set Known Password</strong> box and click <strong>Set Password</strong>.
                </div>
            </div>
        </body>
        </html>
        """
        return html, 200

    return jsonify({"total_users": len(users_list), "users": users_list}), 200

@auth_bp.route("/admin/download-db", methods=["GET"])
def admin_download_db():
    """1-Click download of the live SQLite database file from Render."""
    import os
    from flask import current_app, send_file
    secret_key = current_app.config.get("SECRET_KEY", "cloudsky-dev-secret-key-12345")
    key = request.args.get("key", "").strip()

    is_admin_session = session.get("user_email") in [
        "rohan.sharma@example.in",
        os.getenv("ADMIN_EMAIL", "").strip().lower()
    ]

    if not is_admin_session and key != secret_key:
        return jsonify({"error": "Unauthorized"}), 403

    db_path = current_app.config.get("DATABASE_PATH")
    if not os.path.exists(db_path):
        return jsonify({"error": "Database file not found"}), 404

    return send_file(db_path, as_attachment=True, download_name="cloudsky.db")

@auth_bp.route("/admin/reset-password", methods=["POST"])
def admin_reset_password():
    """Allows admin to set a known password for any user account."""
    import os
    from flask import current_app
    secret_key = current_app.config.get("SECRET_KEY", "cloudsky-dev-secret-key-12345")
    key = request.form.get("key", "").strip() or request.args.get("key", "").strip()

    is_admin_session = session.get("user_email") in [
        "rohan.sharma@example.in",
        os.getenv("ADMIN_EMAIL", "").strip().lower()
    ]

    if not is_admin_session and key != secret_key:
        return jsonify({"error": "Unauthorized"}), 403

    user_id = request.form.get("user_id")
    new_password = request.form.get("new_password", "").strip()

    if not user_id or not new_password:
        flash("User ID and new password are required.", "error")
        return redirect(url_for("auth.admin_users_view", key=key))

    db = get_db()
    user = db.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        flash(f"User ID {user_id} not found.", "error")
        return redirect(url_for("auth.admin_users_view", key=key))

    new_hash = generate_password_hash(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    db.commit()

    logger.info("[ADMIN] Password reset successfully for user ID=%s, Email='%s'", user["id"], user["email"])
    flash(f"Password successfully reset for {user['name']} ({user['email']}) to '{new_password}'.", "success")
    return redirect(url_for("auth.admin_users_view", key=key))
