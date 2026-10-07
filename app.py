from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "movie-ticket-secret-key"

# ---------------- DATABASE CONNECTION ----------------
def get_db_connection():
    return mysql.connector.connect(
host="",
        user="",
        password="",
        database=""
    )


# ---------------- Register Page ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (name, email, phone, password, role)
            VALUES
            (%s, %s, %s, %s, 'CUSTOMER')
        """, (
            name,
            email,
            phone,
            password
        ))

        connection.commit()

        return redirect(url_for("login"))

    except Exception as e:

        connection.rollback()

        return f"Registration failed: {str(e)}", 400

    finally:

        cursor.close()
        connection.close()
#----------------- LOGIN PAGE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT user_id, name, email, password, role
        FROM users
        WHERE email = %s
    """, (email,))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user or user["password"] != password:
        return "Invalid email or password.", 401

    session["user_id"] = user["user_id"]
    session["user_name"] = user["name"]
    session["role"] = user["role"]

    return redirect(url_for("home"))
        
# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT movie_id, title, genre, language,
               duration_minutes, release_date, rating, description
        FROM movies
        ORDER BY title
    """)

    movies = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("index.html", movies=movies)

@app.route("/shows/<int:movie_id>")
def shows(movie_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.show_id,
            m.title AS movie_title,
            t.theatre_name,
            t.city,
            sc.screen_name,
            s.show_date,
            s.show_time,
            s.ticket_price
        FROM shows s
        JOIN movies m
            ON s.movie_id = m.movie_id
        JOIN screens sc
            ON s.screen_id = sc.screen_id
        JOIN theatres t
            ON sc.theatre_id = t.theatre_id
        WHERE s.movie_id = %s
        ORDER BY s.show_date, s.show_time
    """, (movie_id,))

    shows = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("shows.html", shows=shows)
@app.route("/seats/<int:show_id>")
def seats(show_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get show details
    cursor.execute("""
        SELECT
            s.show_id,
            m.title AS movie_title,
            t.theatre_name,
            t.city,
            sc.screen_name,
            s.show_date,
            s.show_time,
            s.ticket_price,
            s.screen_id
        FROM shows s
        JOIN movies m ON s.movie_id = m.movie_id
        JOIN screens sc ON s.screen_id = sc.screen_id
        JOIN theatres t ON sc.theatre_id = t.theatre_id
        WHERE s.show_id = %s
    """, (show_id,))

    show = cursor.fetchone()

    if not show:
        cursor.close()
        connection.close()
        return "Show not found", 404

    # Get all seats for this screen
    cursor.execute("""
        SELECT
            seat_id,
            seat_number,
            seat_type
        FROM seats
        WHERE screen_id = %s
        ORDER BY seat_id
    """, (show["screen_id"],))

    seats = cursor.fetchall()

    # Find already booked seats for this show
    cursor.execute("""
        SELECT bs.seat_id
        FROM booking_seats bs
        JOIN bookings b
            ON bs.booking_id = b.booking_id
        WHERE b.show_id = %s
          AND b.booking_status = 'CONFIRMED'
    """, (show_id,))

    booked_seat_rows = cursor.fetchall()
    booked_seat_ids = [row["seat_id"] for row in booked_seat_rows]

    cursor.close()
    connection.close()

    return render_template(
        "seats.html",
        show=show,
        seats=seats,
        booked_seat_ids=booked_seat_ids
    )
    
@app.route("/booking/summary", methods=["POST"])
def booking_summary():

    show_id = request.form.get("show_id")
    selected_seats = request.form.get("selected_seats")

    if not show_id or not selected_seats:
        return "Please select at least one seat.", 400

    seat_ids = selected_seats.split(",")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get show details
    cursor.execute("""
        SELECT
            s.show_id,
            m.title AS movie_title,
            t.theatre_name,
            t.city,
            sc.screen_name,
            s.show_date,
            s.show_time,
            s.ticket_price
        FROM shows s
        JOIN movies m ON s.movie_id = m.movie_id
        JOIN screens sc ON s.screen_id = sc.screen_id
        JOIN theatres t ON sc.theatre_id = t.theatre_id
        WHERE s.show_id = %s
    """, (show_id,))

    show = cursor.fetchone()

    # Get selected seat details
    placeholders = ",".join(["%s"] * len(seat_ids))

    cursor.execute(
        f"""
        SELECT seat_id, seat_number, seat_type
        FROM seats
        WHERE seat_id IN ({placeholders})
        ORDER BY seat_id
        """,
        tuple(seat_ids)
    )

    seats = cursor.fetchall()

    cursor.close()
    connection.close()

    total_amount = len(seats) * float(show["ticket_price"])

    return render_template(
        "booking.html",
        show=show,
        seats=seats,
        total_amount=total_amount
    )
    
@app.route("/booking/confirm", methods=["POST"])
def confirm_booking():

    show_id = request.form.get("show_id")
    seat_ids = request.form.get("seat_ids")

    if not show_id or not seat_ids:
        return "Invalid booking request.", 400

    seat_ids = seat_ids.split(",")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # ------------------------------------------------
        # 1. Get show information
        # ------------------------------------------------
        cursor.execute("""
            SELECT
                show_id,
                ticket_price
            FROM shows
            WHERE show_id = %s
        """, (show_id,))

        show = cursor.fetchone()

        if not show:
            return "Show not found.", 404

        # ------------------------------------------------
        # 2. Check whether seats are already booked
        # ------------------------------------------------
        placeholders = ",".join(["%s"] * len(seat_ids))

        cursor.execute(
            f"""
            SELECT bs.seat_id
            FROM booking_seats bs
            JOIN bookings b
                ON bs.booking_id = b.booking_id
            WHERE b.show_id = %s
              AND b.booking_status = 'CONFIRMED'
              AND bs.seat_id IN ({placeholders})
            """,
            tuple([show_id] + seat_ids)
        )

        already_booked = cursor.fetchall()

        if already_booked:
            connection.rollback()

            booked_ids = [
                str(row["seat_id"])
                for row in already_booked
            ]

            return (
                "Sorry, these seats were already booked: "
                + ", ".join(booked_ids)
            ), 409

        # ------------------------------------------------
        # 3. Calculate total amount
        # ------------------------------------------------
        total_amount = len(seat_ids) * float(show["ticket_price"])

        # ------------------------------------------------
        # 4. Start transaction
        # ------------------------------------------------
        
        
        # ------------------------------------------------
        # 5. Create booking
        #
        # For now user_id = 1
        # This will later be replaced by logged-in user.
        # ------------------------------------------------
        cursor.execute("""
            INSERT INTO bookings
            (user_id, show_id, total_amount, booking_status)
            VALUES
            (%s, %s, %s, 'CONFIRMED')
        """, (1, show_id, total_amount))

        booking_id = cursor.lastrowid

        # ------------------------------------------------
        # 6. Insert selected seats
        # ------------------------------------------------
        for seat_id in seat_ids:

            cursor.execute("""
                INSERT INTO booking_seats
                (booking_id, seat_id)
                VALUES
                (%s, %s)
            """, (booking_id, seat_id))

        # ------------------------------------------------
        # 7. Create payment
        # ------------------------------------------------
        transaction_reference = "WEB-TXN-" + str(booking_id)

        cursor.execute("""
            INSERT INTO payments
            (
                booking_id,
                amount,
                payment_method,
                payment_status,
                transaction_reference
            )
            VALUES
            (%s, %s, 'UPI', 'SUCCESS', %s)
        """, (
            booking_id,
            total_amount,
            transaction_reference
        ))

        # ------------------------------------------------
        # 8. Commit everything
        # ------------------------------------------------
        connection.commit()

        return render_template(
            "confirmation.html",
            booking_id=booking_id,
            total_amount=total_amount,
            transaction_reference=transaction_reference
        )

    except Exception as e:

        connection.rollback()

        return f"Booking failed: {str(e)}", 500

    finally:

        cursor.close()
        connection.close()
        
            
# ---------------- RUN APPLICATION ----------------
if __name__ == "__main__":
    app.run(debug=True)