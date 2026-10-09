"""Home quote, checkout, Trips, cancellation and review endpoints."""
import hashlib
import json
from typing import Annotated
from fastapi import APIRouter, Header, HTTPException
from ..dependencies import DB, User
from ..booking_rules import booking_today, price_quote, stored_quote
from ..schemas.homes import BookingInput, ReviewInput
from ..services.listings import listing_row
from ..services.bookings import validate_dates, check_available, booking_list

router = APIRouter()

@router.post("/api/quote")
def quote(body: BookingInput, db: DB):
    row = listing_row(db, body.listing_id)
    nights = validate_dates(body.check_in, body.check_out)
    if body.guests > row["max_guests"]:
        raise HTTPException(422, "This home cannot accommodate that many guests.")
    check_available(db, body.listing_id, body.check_in, body.check_out)
    return price_quote(row, nights)


@router.post("/api/bookings", status_code=201)
def book(
    body: BookingInput,
    db: DB,
    user: User,
    idempotency_key: Annotated[str | None, Header(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")] = None,
):
    # The write lock covers the availability check and INSERT, preventing double booking.
    db.execute("BEGIN IMMEDIATE")
    try:
        fingerprint = hashlib.sha256(json.dumps(body.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
        if idempotency_key:
            existing = db.execute("SELECT * FROM bookings WHERE user_id=? AND idempotency_key=?", (user["id"], idempotency_key)).fetchone()
            if existing:
                if existing["request_fingerprint"] != fingerprint:
                    raise HTTPException(409, "This checkout was already submitted with different details. Start a new checkout.")
                if existing["status"] != "confirmed":
                    raise HTTPException(409, "This reservation was cancelled. Start a new checkout to book again.")
                return {"id": existing["id"], "status": "confirmed", **stored_quote(existing)}
        row = listing_row(db, body.listing_id)
        if row["host_id"] == user["id"]:
            raise HTTPException(422, "You cannot book your own home.")
        cost = quote(body, db)
        if body.expected_total is not None and body.expected_total != cost["total"]:
            raise HTTPException(409, "The price changed. Review the updated price before confirming your stay.")
        cursor = db.execute(
            "INSERT INTO bookings(listing_id,user_id,check_in,check_out,guests,nightly_price,cleaning_fee,service_fee,total,idempotency_key,request_fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                body.listing_id,
                user["id"],
                str(body.check_in),
                str(body.check_out),
                body.guests,
                cost["nightly_price"],
                cost["cleaning_fee"],
                cost["service_fee"],
                cost["total"],
                idempotency_key,
                fingerprint if idempotency_key else None,
            ),
        )
        db.commit()
        return {"id": cursor.lastrowid, "status": "confirmed", **cost}
    except Exception:
        db.rollback()
        raise


@router.get("/api/bookings")
def trips(db: DB, user: User):
    return booking_list(
        db,
        db.execute(
            "SELECT * FROM bookings WHERE user_id=? ORDER BY check_in DESC",
            (user["id"],),
        ).fetchall(),
    )


@router.post("/api/bookings/{id}/review", status_code=201)
def leave_review(id: int, body: ReviewInput, db: DB, user: User):
    db.execute("BEGIN IMMEDIATE")
    try:
        booking = db.execute(
            "SELECT * FROM bookings WHERE id=? AND user_id=?", (id, user["id"])
        ).fetchone()
        if not booking:
            raise HTTPException(404, "Completed reservation not found.")
        if booking["status"] != "confirmed" or booking["check_out"] > str(booking_today()):
            raise HTTPException(422, "You can leave a review after your confirmed stay is complete.")
        if db.execute("SELECT 1 FROM reviews WHERE booking_id=?", (id,)).fetchone():
            raise HTTPException(409, "You have already reviewed this stay.")
        cursor = db.execute(
            "INSERT INTO reviews(listing_id,user_id,booking_id,rating,comment) VALUES(?,?,?,?,?)",
            (booking["listing_id"], user["id"], id, body.rating, body.comment),
        )
        db.commit()
        return {"id": cursor.lastrowid, "booking_id": id, "rating": body.rating, "comment": body.comment}
    except Exception:
        db.rollback()
        raise


@router.delete("/api/bookings/{id}")
def cancel(id: int, db: DB, user: User):
    row = db.execute(
        "SELECT * FROM bookings WHERE id=? AND user_id=?", (id, user["id"])
    ).fetchone()
    if not row:
        raise HTTPException(404, "Booking not found.")
    if row["check_in"] < str(booking_today()):
        raise HTTPException(422, "Past stays cannot be cancelled.")
    db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (id,))
    db.commit()
    return {"status": "cancelled"}


