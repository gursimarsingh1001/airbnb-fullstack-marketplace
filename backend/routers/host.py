"""Owner-scoped home management endpoints."""
from fastapi import APIRouter, HTTPException
from ..dependencies import DB, User, require_host
from ..booking_rules import booking_today

from ..schemas.homes import ListingInput
from ..services.listings import listing_row, serialize_listing, write_listing
from ..services.bookings import booking_list

router = APIRouter()

@router.post("/api/host/listings", status_code=201)
def create_listing(body: ListingInput, db: DB, user: User):
    require_host(user)
    return write_listing(db, body, user)


@router.put("/api/host/listings/{id}")
def update_listing(id: int, body: ListingInput, db: DB, user: User):
    require_host(user)
    return write_listing(db, body, user, id)


@router.delete("/api/host/listings/{id}")
def delete_listing(id: int, db: DB, user: User):
    require_host(user)
    db.execute("BEGIN IMMEDIATE")
    row = listing_row(db, id)
    if row["host_id"] != user["id"]:
        raise HTTPException(403, "Only the owner can delete this listing.")
    if db.execute(
        "SELECT 1 FROM bookings WHERE listing_id=? AND status='confirmed' AND check_out>?",
        (id, str(booking_today())),
    ).fetchone():
        raise HTTPException(
            409,
            "This listing has upcoming reservations. It can be deleted after those stays finish.",
        )
    db.execute("UPDATE listings SET deleted=1 WHERE id=?", (id,))
    db.commit()
    return {"deleted": True}


@router.get("/api/host/dashboard")
def dashboard(db: DB, user: User):
    require_host(user)
    homes = [
        serialize_listing(db, r)
        for r in db.execute(
            "SELECT * FROM listings WHERE host_id=? AND deleted=0 ORDER BY id DESC",
            (user["id"],),
        )
    ]
    reservations = booking_list(
        db,
        db.execute(
            "SELECT b.* FROM bookings b JOIN listings l ON l.id=b.listing_id WHERE l.host_id=? ORDER BY b.check_in",
            (user["id"],),
        ).fetchall(),
    )
    return {"listings": homes, "bookings": reservations}


