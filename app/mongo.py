import re
import datetime
from typing import Any, Dict, List, Optional
try:
    from pymongo import MongoClient, ReturnDocument, ASCENDING, DESCENDING
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


class MongoRow(dict):
    """
    A dict subclass that allows dictionary access, attribute access,
    and index-based access (row[0]) to mimic sqlite3.Row.
    """
    def __init__(self, data: Optional[Dict[str, Any]] = None, keys: Optional[List[str]] = None):
        super().__init__(data or {})
        object.__setattr__(self, "_keys", list(super().keys()) if keys is None else list(keys))

    def __getitem__(self, item):
        if isinstance(item, int):
            key = self._keys[item]
            return super().__getitem__(key)
        return super().__getitem__(item)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(f"'MongoRow' object has no attribute '{name}'")

    def keys(self):
        return self._keys


class MongoCursor:
    """Emulates a database cursor for query results."""
    def __init__(self, rows: Optional[List[MongoRow]] = None, lastrowid: Optional[int] = None, rowcount: int = 0):
        self._rows = rows or []
        self._index = 0
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    def fetchall(self) -> List[MongoRow]:
        return list(self._rows)

    def fetchone(self) -> Optional[MongoRow]:
        if self._rows and self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None

    def __iter__(self):
        return iter(self._rows)


class MongoAdapter:
    """
    MongoDB Database Adapter providing seamless compatibility
    with CloudSky Airways' query conventions and native PyMongo collections.
    """
    def __init__(self, uri: str, db_name: str = "cloudsky"):
        if not PYMONGO_AVAILABLE:
            raise ImportError(
                "PyMongo is not installed. Please run 'pip install pymongo dnspython' "
                "to enable MongoDB support."
            )
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        self._last_cursor = MongoCursor()

    # Direct collection properties
    @property
    def users(self):
        return self.db["users"]

    @property
    def airports(self):
        return self.db["airports"]

    @property
    def flights(self):
        return self.db["flights"]

    @property
    def seats(self):
        return self.db["seats"]

    @property
    def bookings(self):
        return self.db["bookings"]

    @property
    def booking_seats(self):
        return self.db["booking_seats"]

    @property
    def payments(self):
        return self.db["payments"]

    @property
    def counters(self):
        return self.db["counters"]

    def get_next_id(self, sequence_name: str) -> int:
        """Generates consecutive integer IDs for backward compatibility."""
        result = self.counters.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return result["seq"]

    def ensure_indexes(self):
        """Creates required unique and lookup indexes."""
        try:
            self.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
            self.airports.create_index([("code", ASCENDING)], unique=True)
            self.flights.create_index([("flight_number", ASCENDING)])
            self.flights.create_index([("origin_code", ASCENDING), ("destination_code", ASCENDING)])
            self.seats.create_index([("flight_id", ASCENDING), ("seat_number", ASCENDING)], unique=True)
            self.seats.create_index([("flight_id", ASCENDING), ("is_booked", ASCENDING)])
            self.bookings.create_index([("booking_reference", ASCENDING)], unique=True)
            self.bookings.create_index([("user_id", ASCENDING)])
            self.payments.create_index([("transaction_id", ASCENDING)], unique=True, sparse=True)
        except Exception:
            pass

    def cursor(self):
        return self

    def commit(self):
        """MongoDB writes are automatically committed."""
        pass

    def close(self):
        pass

    @property
    def lastrowid(self):
        return self._last_cursor.lastrowid

    def fetchone(self):
        return self._last_cursor.fetchone()

    def fetchall(self):
        return self._last_cursor.fetchall()

    def __iter__(self):
        return iter(self._last_cursor)

    # -------------------------------------------------------------------------
    # SQL-to-Mongo Execution Dispatcher
    # -------------------------------------------------------------------------
    def execute(self, query: str, params: Optional[Any] = None) -> MongoCursor:
        cursor = self._dispatch_execute(query, params)
        self._last_cursor = cursor
        return cursor

    def _dispatch_execute(self, query: str, params: Optional[Any] = None) -> MongoCursor:
        q = " ".join(query.strip().split())
        p = list(params) if params else []

        # 1. Health check & Schema inspection
        if q.upper().startswith("SELECT 1"):
            self.client.admin.command("ping")
            return MongoCursor([MongoRow({"1": 1})])

        if "SQLITE_MASTER" in q.upper():
            count = self.airports.estimated_document_count()
            if count > 0:
                return MongoCursor([MongoRow({"name": "airports"})])
            return MongoCursor([])

        if "PRAGMA" in q.upper():
            return MongoCursor([])

        # 2. Users Queries
        if "FROM USERS" in q.upper():
            return self._handle_users_select(q, p)

        if q.upper().startswith("INSERT INTO USERS") or q.upper().startswith("INSERT OR IGNORE INTO USERS"):
            return self._handle_users_insert(q, p)

        if q.upper().startswith("UPDATE USERS"):
            return self._handle_users_update(q, p)

        # 3. Airports Queries
        if "FROM AIRPORTS" in q.upper():
            return self._handle_airports_select(q, p)

        if q.upper().startswith("INSERT INTO AIRPORTS") or q.upper().startswith("INSERT OR IGNORE INTO AIRPORTS"):
            return self._handle_airports_insert(q, p)

        # 4. Flights Queries
        if "FROM FLIGHTS" in q.upper():
            return self._handle_flights_select(q, p)

        if q.upper().startswith("INSERT INTO FLIGHTS"):
            return self._handle_flights_insert(q, p)

        # 5. Seats Queries
        if "FROM SEATS" in q.upper():
            return self._handle_seats_select(q, p)

        if q.upper().startswith("UPDATE SEATS"):
            return self._handle_seats_update(q, p)

        if q.upper().startswith("INSERT INTO SEATS"):
            return self._handle_seats_insert(q, p)

        # 6. Bookings Queries
        if "FROM BOOKINGS" in q.upper():
            return self._handle_bookings_select(q, p)

        if q.upper().startswith("INSERT INTO BOOKINGS"):
            return self._handle_bookings_insert(q, p)

        if q.upper().startswith("UPDATE BOOKINGS"):
            return self._handle_bookings_update(q, p)

        # 7. Booking Seats Queries
        if "FROM BOOKING_SEATS" in q.upper():
            return self._handle_booking_seats_select(q, p)

        if q.upper().startswith("INSERT INTO BOOKING_SEATS"):
            return self._handle_booking_seats_insert(q, p)

        if q.upper().startswith("DELETE FROM BOOKING_SEATS"):
            return self._handle_booking_seats_delete(q, p)

        if q.upper().startswith("UPDATE BOOKING_SEATS"):
            return self._handle_booking_seats_update(q, p)

        # 8. Payments Queries
        if "FROM PAYMENTS" in q.upper():
            return self._handle_payments_select(q, p)

        if q.upper().startswith("INSERT INTO PAYMENTS"):
            return self._handle_payments_insert(q, p)

        return MongoCursor([])

    def executemany(self, query: str, seq_of_params: List[Any]) -> MongoCursor:
        q = " ".join(query.strip().split())
        if not seq_of_params:
            return MongoCursor()

        # Batch insert for airports
        if q.upper().startswith("INSERT INTO AIRPORTS") or q.upper().startswith("INSERT OR IGNORE INTO AIRPORTS"):
            docs = []
            for p in seq_of_params:
                code = p[0].strip().upper()
                if not self.airports.find_one({"code": code}):
                    docs.append({
                        "id": self.get_next_id("airports"),
                        "code": code,
                        "name": p[1],
                        "city": p[2],
                        "country": p[3]
                    })
            if docs:
                self.airports.insert_many(docs)
            return MongoCursor(rowcount=len(docs))

        # Batch insert for flights
        if q.upper().startswith("INSERT INTO FLIGHTS"):
            count = len(seq_of_params)
            res = self.counters.find_one_and_update(
                {"_id": "flights"},
                {"$inc": {"seq": count}},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            start_id = res["seq"] - count + 1
            docs = []
            for i, p in enumerate(seq_of_params):
                docs.append({
                    "id": start_id + i,
                    "flight_number": p[0],
                    "origin_code": p[1],
                    "destination_code": p[2],
                    "departure_time": p[3],
                    "arrival_time": p[4],
                    "aircraft_model": p[5],
                    "base_price": float(p[6]),
                    "status": p[7]
                })
            if docs:
                self.flights.insert_many(docs)
            return MongoCursor(rowcount=len(docs))

        # Batch insert for seats
        if q.upper().startswith("INSERT INTO SEATS"):
            count = len(seq_of_params)
            res = self.counters.find_one_and_update(
                {"_id": "seats"},
                {"$inc": {"seq": count}},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            start_id = res["seq"] - count + 1
            docs = []
            for i, p in enumerate(seq_of_params):
                docs.append({
                    "id": start_id + i,
                    "flight_id": int(p[0]),
                    "seat_number": p[1],
                    "cabin_class": p[2],
                    "seat_type": p[3],
                    "price_multiplier": float(p[4]),
                    "seat_pitch": p[5],
                    "has_power": int(p[6]),
                    "has_extra_legroom": int(p[7]),
                    "recline_deg": int(p[8]),
                    "features": p[9],
                    "is_booked": int(p[10]),
                    "locked_until": None,
                    "lock_token": None
                })
            if docs:
                self.seats.insert_many(docs)
            return MongoCursor(rowcount=len(docs))

        for params in seq_of_params:
            self.execute(q, params)
        return MongoCursor()

    # -------------------------------------------------------------------------
    # Handlers for Individual Entities
    # -------------------------------------------------------------------------
    def _handle_users_select(self, q: str, p: list) -> MongoCursor:
        if "COUNT(*)" in q.upper():
            count = self.users.count_documents({})
            return MongoCursor([MongoRow({"count": count, 0: count})])

        if "LOWER(TRIM(EMAIL)) = ?" in q:
            email = p[0].strip().lower()
            u = self.users.find_one({"email": email})
            return MongoCursor([MongoRow(u)] if u else [])

        if "WHERE ID = ?" in q.upper():
            user_id = int(p[0])
            u = self.users.find_one({"id": user_id})
            return MongoCursor([MongoRow(u)] if u else [])

        users = list(self.users.find().sort("id", ASCENDING))
        return MongoCursor([MongoRow(u) for u in users])

    def _handle_users_insert(self, q: str, p: list) -> MongoCursor:
        # Check if parameters were passed
        if len(p) >= 4:
            name, email, phone, pw_hash = p[0], p[1].strip().lower(), p[2], p[3]
        elif len(p) == 1:
            pw_hash = p[0]
            val_match = re.search(r"VALUES\s*\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*\?", q, re.IGNORECASE)
            if val_match:
                name, email, phone = val_match.group(1), val_match.group(2).strip().lower(), val_match.group(3)
            else:
                name, email, phone = "Demo User", "demo@example.com", ""
        else:
            return MongoCursor()

        existing = self.users.find_one({"email": email})
        if existing:
            return MongoCursor(lastrowid=existing.get("id"))

        user_id = self.get_next_id("users")
        doc = {
            "id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "password_hash": pw_hash,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.users.insert_one(doc)
        return MongoCursor(lastrowid=user_id)

    def _handle_users_update(self, q: str, p: list) -> MongoCursor:
        if "PASSWORD_HASH = ?" in q.upper():
            pw_hash, user_id = p[0], int(p[1])
            self.users.update_one({"id": user_id}, {"$set": {"password_hash": pw_hash}})
        elif "NAME = ?" in q.upper():
            name, phone, user_id = p[0], p[1], int(p[2])
            self.users.update_one({"id": user_id}, {"$set": {"name": name, "phone": phone}})
        return MongoCursor()

    def _handle_airports_select(self, q: str, p: list) -> MongoCursor:
        if "WHERE CODE = ?" in q.upper():
            code = p[0].strip().upper()
            a = self.airports.find_one({"code": code})
            return MongoCursor([MongoRow(a)] if a else [])

        airports = list(self.airports.find().sort("city", ASCENDING))
        return MongoCursor([MongoRow(a) for a in airports])

    def _handle_airports_insert(self, q: str, p: list) -> MongoCursor:
        # (code, name, city, country)
        code, name, city, country = p[0], p[1], p[2], p[3]
        if not self.airports.find_one({"code": code}):
            airport_id = self.get_next_id("airports")
            self.airports.insert_one({
                "id": airport_id,
                "code": code,
                "name": name,
                "city": city,
                "country": country
            })
        return MongoCursor()

    def _handle_flights_select(self, q: str, p: list) -> MongoCursor:
        # Check flights without seats
        if "NOT IN (SELECT" in q.upper():
            all_flight_ids = set(self.flights.distinct("id"))
            flight_ids_with_seats = set(self.seats.distinct("flight_id"))
            missing_ids = sorted(list(all_flight_ids - flight_ids_with_seats))
            return MongoCursor([MongoRow({"id": fid}) for fid in missing_ids])

        # Check if single flight: WHERE f.id = ?
        if "WHERE F.ID = ?" in q.upper() or "WHERE ID = ?" in q.upper():
            flight_id = int(p[0])
            f = self.flights.find_one({"id": flight_id})
            if not f:
                return MongoCursor([])
            f_row = self._enrich_flight(f)
            return MongoCursor([MongoRow(f_row)])

        # Query builder for flight searches
        query_filter: Dict[str, Any] = {}
        param_idx = 0

        if "ORIGIN_CODE = ?" in q.upper():
            query_filter["origin_code"] = p[param_idx]
            param_idx += 1
        if "DESTINATION_CODE = ?" in q.upper():
            query_filter["destination_code"] = p[param_idx]
            param_idx += 1
        if "DEPARTURE_TIME LIKE ?" in q.upper():
            date_prefix = p[param_idx].rstrip("%")
            query_filter["departure_time"] = {"$regex": f"^{date_prefix}"}
            param_idx += 1

        limit = 50
        if "LIMIT" in q.upper():
            match = re.search(r"LIMIT\s+(\d+)", q, re.IGNORECASE)
            if match:
                limit = int(match.group(1))

        flights = list(self.flights.find(query_filter).sort("departure_time", ASCENDING).limit(limit))
        enriched = [MongoRow(self._enrich_flight(f)) for f in flights]
        return MongoCursor(enriched)

    def _enrich_flight(self, f: dict) -> dict:
        """Joins airport names/cities and seat availability counts into flight."""
        data = dict(f)
        flight_id = data["id"]
        orig = self.airports.find_one({"code": data.get("origin_code")}) or {}
        dest = self.airports.find_one({"code": data.get("destination_code")}) or {}

        data["origin_city"] = orig.get("city", "")
        data["origin_name"] = orig.get("name", "")
        data["dest_city"] = dest.get("city", "")
        data["dest_name"] = dest.get("name", "")

        total_seats = self.seats.count_documents({"flight_id": flight_id})
        available_seats = self.seats.count_documents({"flight_id": flight_id, "is_booked": 0})
        data["total_seats"] = total_seats
        data["available_seats"] = available_seats
        return data

    def _handle_flights_insert(self, q: str, p: list) -> MongoCursor:
        # (flight_number, origin_code, destination_code, departure_time, arrival_time, aircraft_model, base_price, status)
        flight_id = self.get_next_id("flights")
        doc = {
            "id": flight_id,
            "flight_number": p[0],
            "origin_code": p[1],
            "destination_code": p[2],
            "departure_time": p[3],
            "arrival_time": p[4],
            "aircraft_model": p[5],
            "base_price": float(p[6]),
            "status": p[7]
        }
        self.flights.insert_one(doc)
        return MongoCursor(lastrowid=flight_id)

    def _handle_seats_select(self, q: str, p: list) -> MongoCursor:
        if "WHERE S.FLIGHT_ID = ?" in q.upper() or "WHERE FLIGHT_ID = ?" in q.upper():
            flight_id = int(p[0])
            seats = list(self.seats.find({"flight_id": flight_id}).sort("id", ASCENDING))
            return MongoCursor([MongoRow(s) for s in seats])

        if "WHERE ID = ?" in q.upper() or "WHERE S.ID = ?" in q.upper():
            seat_id = int(p[0])
            s = self.seats.find_one({"id": seat_id})
            return MongoCursor([MongoRow(s)] if s else [])

        return MongoCursor([])

    def _handle_seats_update(self, q: str, p: list) -> MongoCursor:
        # Lock seat
        if "SET LOCKED_UNTIL = ?, LOCK_TOKEN = ?" in q.upper():
            locked_until, lock_token, seat_id = p[0], p[1], int(p[2])
            res = self.seats.update_one(
                {"id": seat_id, "is_booked": 0},
                {"$set": {"locked_until": locked_until, "lock_token": lock_token}}
            )
            return MongoCursor(rowcount=res.modified_count)

        # Clear expired holds
        if "SET LOCKED_UNTIL = NULL, LOCK_TOKEN = NULL WHERE IS_BOOKED = 0" in q.upper():
            now_iso = p[0]
            self.seats.update_many(
                {"is_booked": 0, "locked_until": {"$ne": None, "$lt": now_iso}},
                {"$set": {"locked_until": None, "lock_token": None}}
            )
            return MongoCursor()

        # Unlock specific seat
        if "SET LOCKED_UNTIL = NULL, LOCK_TOKEN = NULL WHERE ID = ?" in q.upper():
            seat_id = int(p[0])
            self.seats.update_one({"id": seat_id}, {"$set": {"locked_until": None, "lock_token": None}})
            return MongoCursor()

        # Mark booked
        if "SET IS_BOOKED = 1" in q.upper():
            seat_id = int(p[0])
            self.seats.update_one(
                {"id": seat_id},
                {"$set": {"is_booked": 1, "locked_until": None, "lock_token": None}}
            )
            return MongoCursor()

        # Release seat (cancellation)
        if "SET IS_BOOKED = 0" in q.upper():
            seat_id = int(p[0])
            self.seats.update_one(
                {"id": seat_id},
                {"$set": {"is_booked": 0, "locked_until": None, "lock_token": None}}
            )
            return MongoCursor()

        return MongoCursor()

    def _handle_seats_insert(self, q: str, p: list) -> MongoCursor:
        seat_id = self.get_next_id("seats")
        doc = {
            "id": seat_id,
            "flight_id": int(p[0]),
            "seat_number": p[1],
            "cabin_class": p[2],
            "seat_type": p[3],
            "price_multiplier": float(p[4]),
            "seat_pitch": p[5],
            "has_power": int(p[6]),
            "has_extra_legroom": int(p[7]),
            "recline_deg": int(p[8]),
            "features": p[9],
            "is_booked": int(p[10]),
            "locked_until": None,
            "lock_token": None
        }
        self.seats.insert_one(doc)
        return MongoCursor(lastrowid=seat_id)

    def _handle_bookings_select(self, q: str, p: list) -> MongoCursor:
        # Lookup by PNR
        if "BOOKING_REFERENCE" in q.upper():
            pnr = p[0].strip().upper()
            filter_query = {"booking_reference": pnr}
            if len(p) > 1 and "PASSENGER_EMAIL" in q.upper():
                filter_query["passenger_email"] = p[1].strip().lower()

            b = self.bookings.find_one(filter_query)
            if not b:
                return MongoCursor([])
            return MongoCursor([MongoRow(self._enrich_booking(b))])

        # Lookup by user_id
        if "WHERE B.USER_ID = ?" in q.upper() or "WHERE USER_ID = ?" in q.upper():
            user_id = int(p[0])
            bookings = list(self.bookings.find({"user_id": user_id}).sort("created_at", DESCENDING))
            return MongoCursor([MongoRow(self._enrich_booking(b)) for b in bookings])

        return MongoCursor([])

    def _enrich_booking(self, b: dict) -> dict:
        data = dict(b)
        flight = self.flights.find_one({"id": data.get("flight_id")}) or {}
        orig = self.airports.find_one({"code": flight.get("origin_code")}) or {}
        dest = self.airports.find_one({"code": flight.get("destination_code")}) or {}

        data["flight_number"] = flight.get("flight_number", "")
        data["departure_time"] = flight.get("departure_time", "")
        data["arrival_time"] = flight.get("arrival_time", "")
        data["aircraft_model"] = flight.get("aircraft_model", "")
        data["origin_city"] = orig.get("city", "")
        data["origin_code"] = orig.get("code", "")
        data["dest_city"] = dest.get("city", "")
        data["dest_code"] = dest.get("code", "")
        return data

    def _handle_bookings_insert(self, q: str, p: list) -> MongoCursor:
        booking_id = self.get_next_id("bookings")
        doc = {
            "id": booking_id,
            "booking_reference": p[0],
            "flight_id": int(p[1]),
            "user_id": int(p[2]) if p[2] else None,
            "passenger_name": p[3],
            "passenger_email": p[4].strip().lower(),
            "passenger_phone": p[5],
            "total_amount": float(p[6]),
            "payment_status": p[7],
            "is_checked_in": 0,
            "cancellation_fee": 0.0,
            "refund_amount": 0.0,
            "cancelled_at": None,
            "cancellation_details": "",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.bookings.insert_one(doc)
        return MongoCursor(lastrowid=booking_id)

    def _handle_bookings_update(self, q: str, p: list) -> MongoCursor:
        if "IS_CHECKED_IN = 1" in q.upper():
            booking_id = int(p[0])
            self.bookings.update_one({"id": booking_id}, {"$set": {"is_checked_in": 1}})
        elif "PAYMENT_STATUS = 'CANCELLED'" in q.upper():
            # cancellation_fee, refund_amount, cancelled_at, cancellation_details, booking_id
            fee, refund, cancelled_at, details, booking_id = p[0], p[1], p[2], p[3], int(p[4])
            self.bookings.update_one(
                {"id": booking_id},
                {"$set": {
                    "payment_status": "Cancelled",
                    "cancellation_fee": float(fee),
                    "refund_amount": float(refund),
                    "cancelled_at": cancelled_at,
                    "cancellation_details": details
                }}
            )
        return MongoCursor()

    def _handle_booking_seats_select(self, q: str, p: list) -> MongoCursor:
        booking_id = int(p[0])
        b_seats = list(self.booking_seats.find({"booking_id": booking_id}))
        enriched = []
        for bs in b_seats:
            d = dict(bs)
            seat = self.seats.find_one({"id": d.get("seat_id")}) or {}
            d["cabin_class"] = seat.get("cabin_class", "Economy")
            d["seat_type"] = seat.get("seat_type", "Standard")
            enriched.append(MongoRow(d))
        return MongoCursor(enriched)

    def _handle_booking_seats_insert(self, q: str, p: list) -> MongoCursor:
        bs_id = self.get_next_id("booking_seats")
        doc = {
            "id": bs_id,
            "booking_id": int(p[0]),
            "seat_id": int(p[1]),
            "seat_number": p[2],
            "passenger_name": p[3],
            "passenger_age": int(p[4]),
            "passenger_gender": p[5],
            "price_paid": float(p[6])
        }
        self.booking_seats.insert_one(doc)
        return MongoCursor(lastrowid=bs_id)

    def _handle_booking_seats_delete(self, q: str, p: list) -> MongoCursor:
        booking_id = int(p[0])
        self.booking_seats.delete_many({"booking_id": booking_id})
        return MongoCursor()

    def _handle_booking_seats_update(self, q: str, p: list) -> MongoCursor:
        new_seat_id, new_seat_num, bs_id = int(p[0]), p[1], int(p[2])
        self.booking_seats.update_one(
            {"id": bs_id},
            {"$set": {"seat_id": new_seat_id, "seat_number": new_seat_num}}
        )
        return MongoCursor()

    def _handle_payments_select(self, q: str, p: list) -> MongoCursor:
        booking_id = int(p[0])
        payments = list(self.payments.find({"booking_id": booking_id}))
        return MongoCursor([MongoRow(p) for p in payments])

    def _handle_payments_insert(self, q: str, p: list) -> MongoCursor:
        pay_id = self.get_next_id("payments")
        doc = {
            "id": pay_id,
            "booking_id": int(p[0]),
            "transaction_id": p[1],
            "payment_method": p[2],
            "amount": float(p[3]),
            "currency": p[4],
            "status": p[5],
            "payment_details": p[6],
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.payments.insert_one(doc)
        return MongoCursor(lastrowid=pay_id)
