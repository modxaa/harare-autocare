from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Security settings
app.secret_key = os.getenv("FLASK_SECRET_KEY")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

ADMIN_PASSWORD_HASH = generate_password_hash(
    os.getenv("ADMIN_PASSWORD")
)

CORS(app)


# =========================
# DATABASE
# =========================

def get_database():
    database_path = os.path.join(
        os.path.dirname(__file__),
        "bookings.db"
    )

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    return connection


def create_table():

    connection = get_database()

    connection.execute("""
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

    connection.commit()

    # Make sure status exists in older databases
    columns = connection.execute(
        "PRAGMA table_info(bookings)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "status" not in column_names:

        connection.execute("""
            ALTER TABLE bookings
            ADD COLUMN status TEXT DEFAULT 'Pending'
        """)

        connection.commit()

    connection.close()


# =========================
# CUSTOMER WEBSITE
# =========================

@app.route("/")
def home():

    return render_template("index.html")


# =========================
# BOOKING
# =========================

@app.route("/booking", methods=["POST"])
def booking():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No booking information received."
        }), 400

    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    vehicle = data.get("vehicle", "").strip()
    service = data.get("service", "").strip()
    date = data.get("date", "").strip()
    message = data.get("message", "").strip()

    if not name or not phone or not email or not vehicle or not service or not date:

        return jsonify({
            "success": False,
            "message": "Please complete all required fields."
        }), 400

    connection = get_database()

    connection.execute("""
        INSERT INTO bookings
        (name, phone, email, vehicle, service, date, message, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (
        name,
        phone,
        email,
        vehicle,
        service,
        date,
        message
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Booking submitted successfully!"
    })


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        if session.get("admin_logged_in"):
            return redirect("/dashboard")

        return render_template("login.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if (
        username == ADMIN_USERNAME
        and check_password_hash(ADMIN_PASSWORD_HASH, password)
    ):

        session["admin_logged_in"] = True

        return redirect("/dashboard")

    return render_template(
        "login.html",
        error="Invalid username or password."
    )


# =========================
# LOGOUT
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

    connection = get_database()

    if search:

        bookings = connection.execute("""
            SELECT *
            FROM bookings
            WHERE name LIKE ?
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

        bookings = connection.execute("""
            SELECT *
            FROM bookings
            ORDER BY id DESC
        """).fetchall()

    total = connection.execute(
        "SELECT COUNT(*) FROM bookings"
    ).fetchone()[0]

    pending = connection.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Pending'"
    ).fetchone()[0]

    confirmed = connection.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Confirmed'"
    ).fetchone()[0]

    completed = connection.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'Completed'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "dashboard.html",
        bookings=bookings,
        total=total,
        pending=pending,
        confirmed=confirmed,
        completed=completed,
        search=search
    )


# =========================
# UPDATE BOOKING STATUS
# =========================

@app.route(
    "/update-status/<int:booking_id>",
    methods=["POST"]
)
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

        return redirect("/dashboard")

    connection = get_database()

    connection.execute("""
        UPDATE bookings
        SET status = ?
        WHERE id = ?
    """, (
        status,
        booking_id
    ))

    connection.commit()
    connection.close()

    return redirect("/dashboard")


# =========================
# DELETE BOOKING
# =========================

@app.route(
    "/delete-booking/<int:booking_id>",
    methods=["POST"]
)
def delete_booking(booking_id):

    if not session.get("admin_logged_in"):

        return redirect("/login")

    connection = get_database()

    connection.execute("""
        DELETE FROM bookings
        WHERE id = ?
    """, (booking_id,))

    connection.commit()
    connection.close()

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