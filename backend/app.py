from flask import Flask, request, jsonify, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

ADMIN_PASSWORD_HASH = generate_password_hash(
    os.getenv("ADMIN_PASSWORD")
)

CORS(app)


def get_database():

    connection = sqlite3.connect("bookings.db")

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


@app.route("/")
def home():

    return "Harare AutoCare backend is running!"


@app.route("/booking", methods=["POST"])
def booking():

    data = request.get_json()

    connection = get_database()

    connection.execute("""
        INSERT INTO bookings
        (name, phone, email, vehicle, service, date, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["phone"],
        data["email"],
        data["vehicle"],
        data["service"],
        data["date"],
        data["message"]
    ))

    connection.commit()

    connection.close()

    print("Booking saved successfully!")

    return jsonify({
        "message": "Booking received and saved successfully!"
    })

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and check_password_hash(
            ADMIN_PASSWORD_HASH,
            password
        ):

            session["logged_in"] = True

            return redirect("/dashboard")

        else:

            return render_template(
                "login.html",
                error="Invalid username or password."
            )

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.pop("logged_in", None)

    return redirect("/login")

@app.route("/dashboard")
def dashboard():

    if not session.get("logged_in"):
        return redirect("/login")

    search = request.args.get("search", "").strip()

    connection = get_database()

    if search:

        bookings = connection.execute("""
            SELECT * FROM bookings
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
            SELECT * FROM bookings
            ORDER BY id DESC
        """).fetchall()

    total = connection.execute("""
        SELECT COUNT(*) FROM bookings
    """).fetchone()[0]

    pending = connection.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE status = 'Pending'
    """).fetchone()[0]

    confirmed = connection.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE status = 'Confirmed'
    """).fetchone()[0]

    completed = connection.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE status = 'Completed'
    """).fetchone()[0]

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

@app.route("/update-status/<int:booking_id>", methods=["POST"])
def update_status(booking_id):

    status = request.form["status"]

    connection = get_database()

    connection.execute("""
        UPDATE bookings
        SET status = ?
        WHERE id = ?
    """, (status, booking_id))

    connection.commit()

    connection.close()

    return redirect("/dashboard")

@app.route("/delete-booking/<int:booking_id>", methods=["POST"])
def delete_booking(booking_id):

    connection = get_database()

    connection.execute("""
        DELETE FROM bookings
        WHERE id = ?
    """, (booking_id,))

    connection.commit()

    connection.close()

    return redirect("/dashboard")

if __name__ == "__main__":
    create_table()

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )