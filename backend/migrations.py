"""Additive, versioned schema upgrades; existing reservations are never reset."""

BOOKING_INSERT_GUARD = """
CREATE TRIGGER IF NOT EXISTS bookings_validate_insert
BEFORE INSERT ON bookings
BEGIN
 SELECT CASE WHEN
   length(NEW.check_in) != 10 OR length(NEW.check_out) != 10 OR
   NEW.check_in NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' OR
   NEW.check_out NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' OR
   date(NEW.check_in, '+0 days') IS NOT NEW.check_in OR
   date(NEW.check_out, '+0 days') IS NOT NEW.check_out OR
   NEW.check_in < date('now', '+330 minutes') OR
   julianday(NEW.check_out) - julianday(NEW.check_in) NOT BETWEEN 1 AND 90 OR
   NEW.check_out > date('now', '+330 minutes', '+730 days')
 THEN RAISE(ABORT, 'Invalid booking dates') END;
 SELECT CASE WHEN NOT EXISTS (
   SELECT 1 FROM listings l WHERE l.id=NEW.listing_id AND l.deleted=0
     AND NEW.user_id != l.host_id AND typeof(NEW.guests)='integer'
     AND NEW.guests BETWEEN 1 AND l.max_guests
 ) THEN RAISE(ABORT, 'Invalid listing or guest capacity') END;
 SELECT CASE WHEN
   typeof(NEW.nightly_price)!='integer' OR NEW.nightly_price<=0 OR
   typeof(NEW.cleaning_fee)!='integer' OR NEW.cleaning_fee<0 OR
   typeof(NEW.service_fee)!='integer' OR NEW.service_fee<0 OR
   typeof(NEW.total)!='integer' OR NEW.total<=0 OR
   NEW.service_fee != CAST((NEW.nightly_price * CAST(julianday(NEW.check_out)-julianday(NEW.check_in) AS INTEGER)*14+50)/100 AS INTEGER) OR
   NEW.total != NEW.nightly_price * CAST(julianday(NEW.check_out)-julianday(NEW.check_in) AS INTEGER)+NEW.cleaning_fee+NEW.service_fee OR
   NOT EXISTS(SELECT 1 FROM listings WHERE id=NEW.listing_id AND price=NEW.nightly_price AND cleaning_fee=NEW.cleaning_fee)
 THEN RAISE(ABORT, 'Invalid booking price') END;
 SELECT CASE WHEN NEW.status='confirmed' AND EXISTS (
   SELECT 1 FROM bookings b WHERE b.listing_id=NEW.listing_id AND b.status='confirmed'
     AND b.check_in<NEW.check_out AND b.check_out>NEW.check_in
 ) THEN RAISE(ABORT, 'Conflicting reservation') END;
END
"""

BOOKING_IMMUTABLE_GUARD = """
CREATE TRIGGER IF NOT EXISTS bookings_preserve_details
BEFORE UPDATE OF listing_id,user_id,check_in,check_out,guests,nightly_price,cleaning_fee,service_fee,total,idempotency_key,request_fingerprint ON bookings
WHEN NEW.listing_id IS NOT OLD.listing_id OR NEW.user_id IS NOT OLD.user_id OR
 NEW.check_in IS NOT OLD.check_in OR NEW.check_out IS NOT OLD.check_out OR
 NEW.guests IS NOT OLD.guests OR NEW.nightly_price IS NOT OLD.nightly_price OR
 NEW.cleaning_fee IS NOT OLD.cleaning_fee OR NEW.service_fee IS NOT OLD.service_fee OR
 NEW.total IS NOT OLD.total OR NEW.idempotency_key IS NOT OLD.idempotency_key OR
 NEW.request_fingerprint IS NOT OLD.request_fingerprint
BEGIN
 SELECT RAISE(ABORT, 'Reservation details are immutable');
END
"""

BOOKING_STATUS_GUARD = """
CREATE TRIGGER IF NOT EXISTS bookings_cancel_only
BEFORE UPDATE OF status ON bookings
WHEN OLD.status='cancelled' AND NEW.status!='cancelled'
BEGIN
 SELECT RAISE(ABORT, 'Cancelled reservations cannot be reactivated');
END
"""


def migrate(db):
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    if not db.execute("SELECT 1 FROM schema_migrations WHERE version=1").fetchone():
        columns = {row[1] for row in db.execute("PRAGMA table_info(bookings)")}
        for column in ("idempotency_key", "request_fingerprint"):
            if column not in columns:
                db.execute(f"ALTER TABLE bookings ADD COLUMN {column} TEXT")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS bookings_idempotency ON bookings(user_id,idempotency_key) WHERE idempotency_key IS NOT NULL")
        db.execute(BOOKING_INSERT_GUARD)
        db.execute(BOOKING_IMMUTABLE_GUARD)
        db.execute(BOOKING_STATUS_GUARD)
        db.execute("INSERT INTO schema_migrations(version) VALUES(1)")
    if not db.execute("SELECT 1 FROM schema_migrations WHERE version=2").fetchone():
        columns = {row[1] for row in db.execute("PRAGMA table_info(reviews)")}
        if "booking_id" not in columns:
            db.execute("ALTER TABLE reviews ADD COLUMN booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS reviews_booking_unique ON reviews(booking_id) WHERE booking_id IS NOT NULL")
        db.execute("""CREATE TRIGGER IF NOT EXISTS reviews_completed_stay_guard
            BEFORE INSERT ON reviews WHEN NEW.booking_id IS NOT NULL
            BEGIN
              SELECT CASE WHEN NOT EXISTS (
                SELECT 1 FROM bookings b WHERE b.id=NEW.booking_id
                  AND b.listing_id=NEW.listing_id AND b.user_id=NEW.user_id
                  AND b.status='confirmed' AND b.check_out<=date('now', '+330 minutes')
              ) THEN RAISE(ABORT, 'Review requires a completed confirmed stay') END;
            END""")
        db.execute("INSERT INTO schema_migrations(version) VALUES(2)")

    if not db.execute("SELECT 1 FROM schema_migrations WHERE version=3").fetchone():
        db.execute("DROP TRIGGER IF EXISTS bookings_validate_insert")
        db.execute(BOOKING_INSERT_GUARD)
        db.execute("DROP TRIGGER IF EXISTS reviews_completed_stay_guard")
        db.execute("""CREATE TRIGGER reviews_completed_stay_guard
            BEFORE INSERT ON reviews WHEN NEW.booking_id IS NOT NULL
            BEGIN
              SELECT CASE WHEN NOT EXISTS (
                SELECT 1 FROM bookings b WHERE b.id=NEW.booking_id
                  AND b.listing_id=NEW.listing_id AND b.user_id=NEW.user_id
                  AND b.status='confirmed' AND b.check_out<=date('now', '+330 minutes')
              ) THEN RAISE(ABORT, 'Review requires a completed confirmed stay') END;
            END""")
        db.execute("INSERT INTO schema_migrations(version) VALUES(3)")

    if not db.execute("SELECT 1 FROM schema_migrations WHERE version=5").fetchone():
        columns = {row[1] for row in db.execute("PRAGMA table_info(listings)")}
        if "seeded" not in columns:
            db.execute("ALTER TABLE listings ADD COLUMN seeded INTEGER NOT NULL DEFAULT 0")
        db.execute("INSERT INTO schema_migrations(version) VALUES(5)")
