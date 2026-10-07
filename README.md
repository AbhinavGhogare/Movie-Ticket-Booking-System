@"
# Movie Ticket Booking System

## Project Description

The Movie Ticket Booking System is a Flask and MySQL based web application that allows customers to register, log in, browse movies and shows, select seats, book movie tickets, and view their bookings.

An admin can manage movies and shows and view bookings.

## Technologies Used

- Python
- Flask
- MySQL
- mysql-connector-python
- HTML/CSS
- Jinja2 Templates

## Project Structure

Movie-Ticket-Booking-System/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── PROJECT_CHECKLIST.md
│
└── templates/
    ├── index.html
    ├── login.html
    ├── register.html
    ├── shows.html
    ├── booking.html
    ├── seats.html
    └── confirmation.html

## Installation

### 1. Create a virtual environment

python -m venv venv

### 2. Activate the virtual environment

Windows PowerShell:

venv\Scripts\Activate.ps1

### 3. Install dependencies

pip install -r requirements.txt

### 4. Configure MySQL

Create the required MySQL database and tables.

Update the database configuration in app.py:

DB_HOST=localhost
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name

### 5. Run the application

python app.py

### 6. Open the application

http://127.0.0.1:5000

## Main Features

### Customer

- Customer registration
- Customer login
- Browse movies
- View available shows
- Select seats
- Book tickets
- Booking confirmation
- View previous bookings

### Admin

- Admin login
- Add movies
- Update movies
- Delete movies
- Add shows
- Update shows
- Delete shows
- View bookings

## Testing

The major customer and administrator workflows were tested successfully, including registration, login, movie selection, show selection, seat selection, booking, confirmation, customer booking history, movie CRUD, show CRUD, and admin booking management.

## Notes

Do not include the virtual environment (venv) in the submission ZIP.

Do not include real database passwords or other sensitive credentials in the submission.
"@ | Set-Content README.md