from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# =========================
# ENVIRONMENT VARIABLES
# =========================

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Check required environment variables
if not FLASK_SECRET_KEY:
    raise RuntimeError("FLASK_SECRET_KEY is missing")

if not ADMIN_USERNAME:
    raise RuntimeError("ADMIN_USERNAME is missing")

if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD is missing")

# Flask session security
app.secret_key = FLASK_SECRET_KEY

# Create secure password hash
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Allow frontend requests
CORS(app)


# =========================
# DATABASE
# =========================

def get_database():
    database = sqlite3.connect("bookings.db")
    database.row_factory = sqlite3.Row
    return database


def create_table():
    database = get_database()

    database.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            vehicle TEXT NOT NULL,
            service TEXT NOT NULL,
            date TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    # Make sure older databases also have the status column
    columns = database.execute(
        "PRAGMA table_info(bookings)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "status" not in column_names:
        database.execute(
            "ALTER TABLE bookings ADD COLUMN status TEXT DEFAULT 'Pending'"
        )

    database.commit()
    database.close()


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# CUSTOMER BOOKING
# =========================

@app.route("/booking", methods=["POST"])
def booking():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No booking information received."
        }), 400

    required_fields = [
        "name",
        "phone",
        "email",
        "vehicle",
        "service",
        "date"
    ]

    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "success": False,
                "message": f"Please provide {field}."
            }), 400

    database = get_database()

    database.execute("""
        INSERT INTO bookings
        (name, phone, email, vehicle, service, date, message, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["phone"],
        data["email"],
        data["vehicle"],
        data["service"],
        data["date"],
        data.get("message", ""),
        "Pending"
    ))

    database.commit()
    database.close()

    return jsonify({
        "success": True,
        "message": "Your booking request has been submitted successfully."
    })


# =========================
# ADMIN LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    # If already logged in, go to dashboard
    if session.get("admin_logged_in"):
        return redirect("/dashboard")

    error = None

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            username == ADMIN_USERNAME
            and check_password_hash(ADMIN_PASSWORD_HASH, password)
        ):
            session["admin_logged_in"] = True
            return redirect("/dashboard")

        error = "Invalid username or password."

    return render_template(
        "login.html",
        error=error
    )


# =========================
# ADMIN LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if not session.get("admin_logged_in"):
        return redirect("/login")

    search = request.args.get("search", "").strip()

    database = get_database()

    if search:

        bookings = database.execute("""
            SELECT *
            FROM bookings
            WHERE
                name LIKE ?
                OR phone LIKE ?
                OR vehicle LIKE ?
                OR service LIKE ?
            ORDER BY id DESC
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        bookings = database.execute("""
            SELECT *
            FROM bookings
            ORDER BY id DESC
        """).fetchall()

    # Dashboard statistics
    total = database.execute(
        "SELECT COUNT(*) FROM bookings"
    ).fetchone()[0]

    pending = database.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Pending'"
    ).fetchone()[0]

    confirmed = database.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Confirmed'"
    ).fetchone()[0]

    completed = database.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Completed'"
    ).fetchone()[0]

    database.close()

    return render_template(
        "dashboard.html",
        bookings=bookings,
        search=search,
        total=total,
        pending=pending,
        confirmed=confirmed,
        completed=completed
    )


# =========================
# UPDATE BOOKING STATUS
# =========================

@app.route("/update-status/<int:booking_id>", methods=["POST"])
def update_status(booking_id):

    if not session.get("admin_logged_in"):
        return redirect("/login")

    status = request.form.get("status")

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        return "Invalid status", 400

    database = get_database()

    database.execute("""
        UPDATE bookings
        SET status = ?
        WHERE id = ?
    """, (
        status,
        booking_id
    ))

    database.commit()
    database.close()

    return redirect("/dashboard")


# =========================
# DELETE BOOKING
# =========================

@app.route("/delete-booking/<int:booking_id>", methods=["POST"])
def delete_booking(booking_id):

    if not session.get("admin_logged_in"):
        return redirect("/login")

    database = get_database()

    database.execute("""
        DELETE FROM bookings
        WHERE id = ?
    """, (
        booking_id,
    ))

    database.commit()
    database.close()

    return redirect("/dashboard")


# =========================
# START APPLICATION
# =========================

if __name__ == "__main__":

    create_table()

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )