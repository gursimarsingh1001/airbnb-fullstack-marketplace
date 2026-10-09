"""Public home discovery and demo profile endpoints."""
from datetime import date
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from ..dependencies import DB
from ..booking_rules import booking_today
from ..services.listings import listing_row, serialize_listing
from ..services.bookings import validate_dates

router = APIRouter()

@router.get("/api/health")
def health(db: DB):
    db.execute("SELECT 1")
    return {"status": "ok", "database": "sqlite", "booking_today": str(booking_today()), "date_policy": "Asia/Kolkata"}


@router.get("/api/users")
def users(db: DB):
    return [dict(u) for u in db.execute("SELECT * FROM users WHERE id<=4")]


@router.get("/api/listings")
def listings(
    db: DB,
    q: str = Query("", max_length=100),
    category: str = "",
    property_type: str = "",
    min_price: int = Query(0, ge=0, le=1000000),
    max_price: int = Query(1000000, ge=0, le=1000000),
    guests: int = Query(1, ge=1, le=16),
    amenities: str = "",
    bedrooms: int = Query(0, ge=0, le=20),
    beds: int = Query(0, ge=0, le=30),
    bathrooms: int = Query(0, ge=0, le=20),
    min_rating: float = Query(0, ge=0, le=5),
    max_rating: float = Query(5, ge=0, le=5),
    superhost: bool = False,
    check_in: date | None = None,
    check_out: date | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=50),
    sort: Literal['recommended', 'price_low', 'price_high', 'rating'] = 'recommended',
):
    if min_price > max_price:
        raise HTTPException(422, "Minimum price cannot exceed maximum price.")
    if min_rating > max_rating:
        raise HTTPException(422, "Minimum rating cannot exceed maximum rating.")
    q = q.strip()
    clauses = ["deleted=0", "price>=?", "price<=?", "max_guests>=?"]
    args = [min_price, max_price, guests]
    for column, value in [('bedrooms', bedrooms), ('beds', beds), ('bathrooms', bathrooms)]:
        clauses.append(column + '>=?'); args.append(value)
    if min_rating or max_rating < 5:
        clauses.append('(SELECT COALESCE(AVG(rating),0) FROM reviews WHERE listing_id=listings.id) BETWEEN ? AND ?')
        args += [min_rating, max_rating]
    if superhost:
        clauses.append('superhost=1')
    if q:
        clauses += ["(location LIKE ? OR country LIKE ? OR title LIKE ?)"]
        args += [f"%{q}%"] * 3
    if category:
        clauses += ["category=?"]
        args += [category]
    if property_type:
        clauses += ["property_type=?"]
        args += [property_type]
    for amenity in sorted({a.strip() for a in amenities.split(",") if a.strip()}):
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
    order = {'recommended': 'id', 'price_low': 'price ASC, id', 'price_high': 'price DESC, id',
             'rating': '(SELECT AVG(rating) FROM reviews WHERE listing_id=listings.id) DESC, id'}[sort]
    rows = db.execute(
        "SELECT * FROM listings WHERE " + where + " ORDER BY " + order + " LIMIT ? OFFSET ?",
        args + [limit, (page - 1) * limit],
    ).fetchall()
    return {
        "items": [serialize_listing(db, r) for r in rows],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@router.get("/api/listings/{id}")
def listing(id: int, db: DB):
    result = serialize_listing(db, listing_row(db, id))
    result["reviews"] = [
        dict(r)
        for r in db.execute(
            "SELECT r.id,r.rating,r.comment,r.created_at,u.name,u.avatar FROM reviews r JOIN users u ON u.id=r.user_id WHERE listing_id=? ORDER BY created_at DESC",
            (id,),
        )
    ]
    result["unavailable"] = [
        dict(r)
        for r in db.execute(
            "SELECT check_in,check_out FROM bookings WHERE listing_id=? AND status='confirmed' AND check_out>=?",
            (id, str(booking_today())),
        )
    ]
    return result


