from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Annotated
import os
import sqlite3

from fastapi import FastAPI, Depends, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl, field_validator
from . import database
from .blob_database import SnapshotConflict, SnapshotUnavailable


@asynccontextmanager
async def lifespan(app):
    database.initialize()
    yield


app = FastAPI(title="Airbnb Marketplace API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:3001,http://127.0.0.1:3001"
    ).split(","),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Demo-User"],
)


@app.exception_handler(SnapshotConflict)
async def snapshot_conflict_handler(request, exc):
    return JSONResponse(status_code=409, content={"detail": "Another reservation or edit was saved just now. Please try again."})


@app.exception_handler(SnapshotUnavailable)
async def snapshot_unavailable_handler(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


def get_db():
    db = database.connect()
    try:
        yield db
    finally:
        db.close()


DB = Annotated[sqlite3.Connection, Depends(get_db)]


def current_user(db: DB, x_demo_user: Annotated[int, Header()] = 1):
    user = db.execute("SELECT * FROM users WHERE id=?", (x_demo_user,)).fetchone()
    if not user:
        raise HTTPException(401, "Choose a valid demo profile.")
    return dict(user)


User = Annotated[dict, Depends(current_user)]


def require_host(user):
    if user["role"] != "host":
        raise HTTPException(403, "Switch to a host profile to manage listings.")


def listing_row(db, id, include_deleted=False):
    row = db.execute(
        "SELECT * FROM listings WHERE id=?"
        + ("" if include_deleted else " AND deleted=0"),
        (id,),
    ).fetchone()
    if not row:
        raise HTTPException(404, "This home is no longer available.")
    return row


def serialize_listing(db, row):
    result = dict(row)
    result["photos"] = [
        p[0]
        for p in db.execute(
            "SELECT url FROM photos WHERE listing_id=? ORDER BY position", (row["id"],)
        )
    ]
    result["amenities"] = [
        a[0]
        for a in db.execute(
            "SELECT a.name FROM amenities a JOIN listing_amenities la ON la.amenity_id=a.id WHERE la.listing_id=?",
            (row["id"],),
        )
    ]
    result["host"] = dict(
        db.execute("SELECT * FROM users WHERE id=?", (row["host_id"],)).fetchone()
    )
    stats = db.execute(
        "SELECT AVG(rating),COUNT(*) FROM reviews WHERE listing_id=?", (row["id"],)
    ).fetchone()
    result["rating"] = round(stats[0], 2) if stats[0] else None
    result["review_count"] = stats[1]
    return result


def validate_dates(check_in, check_out):
    if check_in < date.today():
        raise HTTPException(422, "Check-in must be today or later.")
    nights = (check_out - check_in).days
    if not 1 <= nights <= 90:
        raise HTTPException(422, "Choose a stay between 1 and 90 nights.")
    if check_out > date.today() + timedelta(days=730):
        raise HTTPException(422, "Choose dates within the next two years.")
    return nights


def price_quote(row, nights):
    subtotal = row["price"] * nights
    service = (subtotal * 14 + 50) // 100
    return dict(
        nights=nights,
        nightly_price=row["price"],
        subtotal=subtotal,
        cleaning_fee=row["cleaning_fee"],
        service_fee=service,
        total=subtotal + row["cleaning_fee"] + service,
        currency="INR",
    )


def check_available(db, id, check_in, check_out):
    if db.execute(
        "SELECT 1 FROM bookings WHERE listing_id=? AND status='confirmed' AND check_in < ? AND check_out > ?",
        (id, str(check_out), str(check_in)),
    ).fetchone():
        raise HTTPException(
            409, "Those dates have just been booked. Please choose another stay."
        )


@app.get("/api/health")
def health(db: DB):
    db.execute("SELECT 1")
    return {"status": "ok", "database": "sqlite"}


@app.get("/api/users")
def users(db: DB):
    return [dict(u) for u in db.execute("SELECT * FROM users WHERE id<=4")]


@app.get("/api/listings")
def listings(
    db: DB,
    q: str = "",
    category: str = "",
    property_type: str = "",
    min_price: int = 0,
    max_price: int = 1000000,
    guests: int = 1,
    amenities: str = "",
    check_in: date | None = None,
    check_out: date | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=50),
):
    clauses = ["deleted=0", "price>=?", "price<=?", "max_guests>=?"]
    args = [min_price, max_price, guests]
    if q:
        clauses += ["(location LIKE ? OR country LIKE ? OR title LIKE ?)"]
        args += [f"%{q}%"] * 3
    if category:
        clauses += ["category=?"]
        args += [category]
    if property_type:
        clauses += ["property_type=?"]
        args += [property_type]
    for amenity in filter(None, amenities.split(",")):
        clauses += [
            "EXISTS(SELECT 1 FROM listing_amenities la JOIN amenities a ON a.id=la.amenity_id WHERE la.listing_id=listings.id AND a.name=?)"
        ]
        args += [amenity]
    if bool(check_in) != bool(check_out):
        raise HTTPException(422, "Choose both check-in and checkout.")
    if check_in and check_out:
        validate_dates(check_in, check_out)
        clauses += [
            "NOT EXISTS(SELECT 1 FROM bookings b WHERE b.listing_id=listings.id AND b.status='confirmed' AND b.check_in < ? AND b.check_out > ?)"
        ]
        args += [str(check_out), str(check_in)]
    where = " AND ".join(clauses)
    total = db.execute("SELECT COUNT(*) FROM listings WHERE " + where, args).fetchone()[
        0
    ]
    rows = db.execute(
        "SELECT * FROM listings WHERE " + where + " ORDER BY id LIMIT ? OFFSET ?",
        args + [limit, (page - 1) * limit],
    ).fetchall()
    return {
        "items": [serialize_listing(db, r) for r in rows],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@app.get("/api/listings/{id}")
def listing(id: int, db: DB):
    result = serialize_listing(db, listing_row(db, id))
    result["reviews"] = [
        dict(r)
        for r in db.execute(
            "SELECT r.*,u.name,u.avatar FROM reviews r JOIN users u ON u.id=r.user_id WHERE listing_id=? ORDER BY created_at DESC",
            (id,),
        )
    ]
    result["unavailable"] = [
        dict(r)
        for r in db.execute(
            "SELECT check_in,check_out FROM bookings WHERE listing_id=? AND status='confirmed' AND check_out>=?",
            (id, str(date.today())),
        )
    ]
    return result


class BookingInput(BaseModel):
    listing_id: int
    check_in: date
    check_out: date
    guests: int = Field(ge=1, le=16)


@app.post("/api/quote")
def quote(body: BookingInput, db: DB):
    row = listing_row(db, body.listing_id)
    nights = validate_dates(body.check_in, body.check_out)
    if body.guests > row["max_guests"]:
        raise HTTPException(422, "This home cannot accommodate that many guests.")
    check_available(db, body.listing_id, body.check_in, body.check_out)
    return price_quote(row, nights)


@app.post("/api/bookings", status_code=201)
def book(body: BookingInput, db: DB, user: User):
    # The write lock covers the availability check and INSERT, preventing double booking.
    db.execute("BEGIN IMMEDIATE")
    try:
        row = listing_row(db, body.listing_id)
        if row["host_id"] == user["id"]:
            raise HTTPException(422, "You cannot book your own home.")
        cost = quote(body, db)
        cursor = db.execute(
            "INSERT INTO bookings(listing_id,user_id,check_in,check_out,guests,nightly_price,cleaning_fee,service_fee,total) VALUES(?,?,?,?,?,?,?,?,?)",
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
            ),
        )
        db.commit()
        return {"id": cursor.lastrowid, "status": "confirmed", **cost}
    except Exception:
        db.rollback()
        raise


def booking_list(db, rows):
    return [
        {
            **dict(r),
            "listing": serialize_listing(db, listing_row(db, r["listing_id"], True)),
            "guest_name": db.execute(
                "SELECT name FROM users WHERE id=?", (r["user_id"],)
            ).fetchone()[0],
        }
        for r in rows
    ]


@app.get("/api/bookings")
def trips(db: DB, user: User):
    return booking_list(
        db,
        db.execute(
            "SELECT * FROM bookings WHERE user_id=? ORDER BY check_in DESC",
            (user["id"],),
        ).fetchall(),
    )


@app.delete("/api/bookings/{id}")
def cancel(id: int, db: DB, user: User):
    row = db.execute(
        "SELECT * FROM bookings WHERE id=? AND user_id=?", (id, user["id"])
    ).fetchone()
    if not row:
        raise HTTPException(404, "Booking not found.")
    if row["check_in"] < str(date.today()):
        raise HTTPException(422, "Past stays cannot be cancelled.")
    db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (id,))
    db.commit()
    return {"status": "cancelled"}


@app.get("/api/wishlists")
def wishlist(db: DB, user: User):
    return [
        serialize_listing(db, r)
        for r in db.execute(
            "SELECT l.* FROM listings l JOIN wishlists w ON w.listing_id=l.id WHERE w.user_id=? AND l.deleted=0",
            (user["id"],),
        )
    ]


@app.put("/api/wishlists/{id}")
def save(id: int, db: DB, user: User):
    listing_row(db, id)
    db.execute("INSERT OR IGNORE INTO wishlists VALUES(?,?)", (user["id"], id))
    db.commit()
    return {"saved": True}


@app.delete("/api/wishlists/{id}")
def unsave(id: int, db: DB, user: User):
    db.execute(
        "DELETE FROM wishlists WHERE user_id=? AND listing_id=?", (user["id"], id)
    )
    db.commit()
    return {"saved": False}


class ListingInput(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=30, max_length=5000)
    location: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=80)
    category: str
    property_type: str
    price: int = Field(ge=500, le=1000000)
    cleaning_fee: int = Field(default=900, ge=0, le=100000)
    max_guests: int = Field(ge=1, le=16)
    bedrooms: int = Field(ge=1, le=20)
    beds: int = Field(ge=1, le=30)
    bathrooms: int = Field(ge=1, le=20)
    photos: list[HttpUrl] = Field(min_length=1, max_length=12)
    amenities: list[str] = Field(max_length=12)

    @field_validator("title", "description", "location", "country", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("category")
    @classmethod
    def valid_category(cls, value):
        if value not in [
            "Tropical",
            "Cabins",
            "Beachfront",
            "Amazing views",
            "Countryside",
            "Design",
            "Amazing pools",
            "Lakefront",
            "Tiny homes",
        ]:
            raise ValueError("Choose a valid category")
        return value

    @field_validator("property_type")
    @classmethod
    def valid_type(cls, value):
        if value not in ["Villa", "Cabin", "Cottage", "Apartment", "Tiny home"]:
            raise ValueError("Choose a valid property type")
        return value


def write_listing(db, body, user, id=None):
    data = body.model_dump(exclude={"photos", "amenities"})
    if id:
        row = listing_row(db, id)
        if row["host_id"] != user["id"]:
            raise HTTPException(403, "Only the owner can edit this listing.")
        db.execute(
            "UPDATE listings SET " + ",".join(f"{k}=?" for k in data) + " WHERE id=?",
            list(data.values()) + [id],
        )
        db.execute("DELETE FROM photos WHERE listing_id=?", (id,))
        db.execute("DELETE FROM listing_amenities WHERE listing_id=?", (id,))
    else:
        data["host_id"] = user["id"]
        id = db.execute(
            "INSERT INTO listings("
            + ",".join(data)
            + ") VALUES("
            + ",".join("?" for _ in data)
            + ")",
            list(data.values()),
        ).lastrowid
    db.executemany(
        "INSERT INTO photos(listing_id,url,position) VALUES(?,?,?)",
        [(id, str(url), n) for n, url in enumerate(body.photos)],
    )
    for amenity in set(body.amenities):
        row = db.execute("SELECT id FROM amenities WHERE name=?", (amenity,)).fetchone()
        if not row:
            raise HTTPException(422, "Unknown amenity: " + amenity)
        db.execute("INSERT INTO listing_amenities VALUES(?,?)", (id, row[0]))
    db.commit()
    return serialize_listing(db, listing_row(db, id))


@app.post("/api/host/listings", status_code=201)
def create_listing(body: ListingInput, db: DB, user: User):
    require_host(user)
    return write_listing(db, body, user)


@app.put("/api/host/listings/{id}")
def update_listing(id: int, body: ListingInput, db: DB, user: User):
    require_host(user)
    return write_listing(db, body, user, id)


@app.delete("/api/host/listings/{id}")
def delete_listing(id: int, db: DB, user: User):
    require_host(user)
    db.execute("BEGIN IMMEDIATE")
    row = listing_row(db, id)
    if row["host_id"] != user["id"]:
        raise HTTPException(403, "Only the owner can delete this listing.")
    if db.execute(
        "SELECT 1 FROM bookings WHERE listing_id=? AND status='confirmed' AND check_out>?",
        (id, str(date.today())),
    ).fetchone():
        raise HTTPException(
            409,
            "This listing has upcoming reservations. It can be deleted after those stays finish.",
        )
    db.execute("UPDATE listings SET deleted=1 WHERE id=?", (id,))
    db.commit()
    return {"deleted": True}


@app.get("/api/host/dashboard")
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


# Production serves the Next.js static export and API from the same origin.
static_dir = Path(__file__).parent.parent / "frontend" / "out"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
