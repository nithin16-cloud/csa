-- CloudSky Airlines Database Schema (Day 2: Real-Time Seat Hold & Concurrency Engine)

DROP TABLE IF EXISTS booking_seats;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS seats;
DROP TABLE IF EXISTS flights;
DROP TABLE IF EXISTS airports;

CREATE TABLE airports (
    code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL
);

CREATE TABLE flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number VARCHAR(10) NOT NULL,
    origin_code VARCHAR(3) NOT NULL,
    destination_code VARCHAR(3) NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_time TEXT NOT NULL,
    aircraft_model VARCHAR(50) NOT NULL DEFAULT 'Boeing 787-9 Dreamliner',
    base_price REAL NOT NULL,                           -- Base price in Indian Rupees (INR ₹)
    status VARCHAR(20) NOT NULL DEFAULT 'Scheduled',
    FOREIGN KEY (origin_code) REFERENCES airports (code),
    FOREIGN KEY (destination_code) REFERENCES airports (code)
);

CREATE TABLE seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INTEGER NOT NULL,
    seat_number VARCHAR(5) NOT NULL,
    cabin_class VARCHAR(20) NOT NULL DEFAULT 'Economy',  -- 'Economy', 'Business', 'First'
    seat_type VARCHAR(20) NOT NULL DEFAULT 'Standard',  -- 'Window', 'Aisle', 'Middle', 'Exit Row'
    price_multiplier REAL NOT NULL DEFAULT 1.0,
    is_booked INTEGER NOT NULL DEFAULT 0,              -- 0 = available, 1 = booked
    locked_until TEXT DEFAULT NULL,                     -- ISO timestamp for 5-minute hold lock
    lock_token TEXT DEFAULT NULL,                       -- Session token holding this seat
    version INTEGER NOT NULL DEFAULT 0,                 -- Optimistic concurrency control counter
    FOREIGN KEY (flight_id) REFERENCES flights (id) ON DELETE CASCADE,
    UNIQUE (flight_id, seat_number)                     -- Physical DB constraint: duplicate seat per flight impossible
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_reference VARCHAR(10) UNIQUE NOT NULL,     -- 6-character PNR code e.g. CS-9X4A
    flight_id INTEGER NOT NULL,
    passenger_name VARCHAR(100) NOT NULL,
    passenger_email VARCHAR(100) NOT NULL,
    passenger_phone VARCHAR(30) NOT NULL,
    total_amount REAL NOT NULL,                         -- Total fare in Indian Rupees (₹)
    payment_status VARCHAR(20) NOT NULL DEFAULT 'Confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flight_id) REFERENCES flights (id)
);

CREATE TABLE booking_seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    seat_id INTEGER NOT NULL,
    flight_id INTEGER NOT NULL,
    seat_number VARCHAR(5) NOT NULL,
    price_paid REAL NOT NULL,                           -- Paid price in Indian Rupees (₹)
    FOREIGN KEY (booking_id) REFERENCES bookings (id) ON DELETE CASCADE,
    FOREIGN KEY (seat_id) REFERENCES seats (id) ON DELETE CASCADE,
    FOREIGN KEY (flight_id) REFERENCES flights (id),
    UNIQUE (flight_id, seat_id)                         -- Prevent same seat mapped to multiple bookings
);

CREATE INDEX idx_flights_search ON flights(origin_code, destination_code, departure_time);
CREATE INDEX idx_seats_flight ON seats(flight_id, is_booked, locked_until);
CREATE INDEX idx_bookings_pnr ON bookings(booking_reference);
