"""Home availability rules and historical reservation serialization."""
from datetime import date, timedelta
from fastapi import HTTPException
from ..booking_rules import booking_today, stored_quote
from .listings import listing_row, serialize_listing

def validate_dates(check_in, check_out):
    if check_in < booking_today():
        raise HTTPException(422, "Check-in must be today or later.")
    nights = (check_out - check_in).days
    if not 1 <= nights <= 90:
        raise HTTPException(422, "Choose a stay between 1 and 90 nights.")
    if check_out > booking_today() + timedelta(days=730):
        raise HTTPException(422, "Choose dates within the next two years.")
    return nights


def check_available(db, id, check_in, check_out):
    if db.execute(
        "SELECT 1 FROM bookings WHERE listing_id=? AND status='confirmed' AND check_in < ? AND check_out > ?",
        (id, str(check_out), str(check_in)),
    ).fetchone():
        raise HTTPException(
            409, "Those dates have just been booked. Please choose another stay."
        )


def booking_list(db, rows):
    return [
        {
            **{k: r[k] for k in r.keys() if k not in ("idempotency_key", "request_fingerprint")},
            **stored_quote(r),
            "reviewed": bool(db.execute("SELECT 1 FROM reviews WHERE booking_id=?", (r["id"],)).fetchone()),
            "listing": serialize_listing(db, listing_row(db, r["listing_id"], True)),
            "guest_name": db.execute(
                "SELECT name FROM users WHERE id=?", (r["user_id"],)
            ).fetchone()[0],
        }
        for r in rows
    ]


