"""SQLite connection and schema. Money is stored as integer INR (no floating point)."""

import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).parent / "airbnb.db"))


def connect():
    if os.getenv("DATABASE_BLOB_ENABLED") == "1":
        from .blob_database import connect_snapshot

        return connect_snapshot()
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    return db


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('guest','host')),
 avatar TEXT NOT NULL, joined_year INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS listings (
 id INTEGER PRIMARY KEY AUTOINCREMENT, host_id INTEGER NOT NULL REFERENCES users(id),
 title TEXT NOT NULL, description TEXT NOT NULL, location TEXT NOT NULL,
 country TEXT NOT NULL, category TEXT NOT NULL, property_type TEXT NOT NULL,
 price INTEGER NOT NULL CHECK(price > 0), cleaning_fee INTEGER NOT NULL CHECK(cleaning_fee >= 0),
 max_guests INTEGER NOT NULL CHECK(max_guests BETWEEN 1 AND 16), bedrooms INTEGER NOT NULL CHECK(bedrooms > 0),
 beds INTEGER NOT NULL CHECK(beds > 0), bathrooms INTEGER NOT NULL CHECK(bathrooms > 0),
 latitude REAL NOT NULL DEFAULT 0, longitude REAL NOT NULL DEFAULT 0,
 superhost INTEGER NOT NULL DEFAULT 0, deleted INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS photos (
 id INTEGER PRIMARY KEY, listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
 url TEXT NOT NULL, position INTEGER NOT NULL, UNIQUE(listing_id, position)
);
CREATE TABLE IF NOT EXISTS amenities (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS listing_amenities (
 listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
 amenity_id INTEGER NOT NULL REFERENCES amenities(id), PRIMARY KEY(listing_id, amenity_id)
);
CREATE TABLE IF NOT EXISTS bookings (
 id INTEGER PRIMARY KEY AUTOINCREMENT, listing_id INTEGER NOT NULL REFERENCES listings(id),
 user_id INTEGER NOT NULL REFERENCES users(id), check_in TEXT NOT NULL, check_out TEXT NOT NULL,
 guests INTEGER NOT NULL CHECK(guests > 0), nightly_price INTEGER NOT NULL,
 cleaning_fee INTEGER NOT NULL, service_fee INTEGER NOT NULL, total INTEGER NOT NULL,
 status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, CHECK(check_out > check_in)
);
CREATE INDEX IF NOT EXISTS bookings_availability ON bookings(listing_id, status, check_in, check_out);
CREATE INDEX IF NOT EXISTS bookings_user ON bookings(user_id);
CREATE INDEX IF NOT EXISTS listings_host ON listings(host_id);
CREATE TABLE IF NOT EXISTS reviews (
 id INTEGER PRIMARY KEY, listing_id INTEGER NOT NULL REFERENCES listings(id),
 user_id INTEGER NOT NULL REFERENCES users(id), booking_id INTEGER UNIQUE REFERENCES bookings(id) ON DELETE SET NULL,
 rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
 comment TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS wishlists (
 user_id INTEGER NOT NULL REFERENCES users(id), listing_id INTEGER NOT NULL REFERENCES listings(id),
 PRIMARY KEY(user_id, listing_id)
);
"""


def initialize():
    from .blob_database import SnapshotConflict
    from .migrations import migrate
    from .seed import seed
    from .catalogue import expand_catalogue, expand_large_catalogue

    # A single transaction protects both first seed and additive upgrades. Retry
    # a cloud cold-start race against the winner's snapshot, never reset data.
    for attempt in range(3):
        db = connect()
        try:
            db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA)
            migrate(db)
            seed(db)
            expand_catalogue(db)
            expand_large_catalogue(db)
            db.commit()
            return
        except SnapshotConflict:
            db.rollback()
            if attempt == 2:
                raise
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
