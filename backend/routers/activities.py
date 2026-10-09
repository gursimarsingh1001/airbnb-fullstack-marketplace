"""Experience and service HTTP endpoints."""
from datetime import date, datetime
from typing import Annotated, Literal
import hashlib
import json
import sqlite3
from fastapi import APIRouter, Header, HTTPException, Query
from ..dependencies import DB, User, require_host
from ..schemas.activities import Kind, ReservationInput, ActivityInput
from ..services.activity_clock import now_india
from ..services.activities import get_activity, serialize, slots_for, reservations, calculate, write

router = APIRouter(prefix="/api/activities", tags=["Experiences and services"])

@router.get("")
def browse(
    db: DB,
    kind: Kind,
    q: str = Query("", max_length=100),
    category: str = "",
    day: date | None = None,
    people: int = Query(1, ge=1, le=30),
    min_price: int = Query(0, ge=0),
    max_price: int = Query(1000000, ge=0),
    min_rating: float = Query(0, ge=0, le=5),
    duration: int = Query(480, ge=30, le=480),
    language: str = "",
    setting: str = "",
    service_location: str = "",
    time_of_day: Literal["", "morning", "afternoon", "evening"] = "",
    sort: Literal["recommended", "rating", "price_low"] = "recommended",
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
):
    if min_price > max_price:
        raise HTTPException(422, "Minimum price cannot exceed maximum price.")
    if day and day < now_india().date():
        raise HTTPException(422, "Choose today or a future date.")
    clauses = [
        "kind=?",
        "deleted=0",
        "price BETWEEN ? AND ?",
        "capacity>=?",
        "duration_minutes<=?",
    ]
    args = [kind, min_price, max_price, people, duration]
    if q.strip():
        clauses.append("(title LIKE ? OR location LIKE ? OR country LIKE ?)")
        args += ["%" + q.strip() + "%"] * 3
    for key, value in [
        ("category", category),
        ("language", language),
        ("setting", setting),
        ("service_location", service_location),
    ]:
        if value:
            clauses.append(key + "=?")
            args.append(value)
    rows = db.execute(
        "SELECT * FROM activities WHERE " + " AND ".join(clauses) + " ORDER BY id", args
    ).fetchall()
    items = []
    for row in rows:
        a = serialize(db, row)
        if (a["rating"] or 0) < min_rating:
            continue
        if day or time_of_day:
            slots = slots_for(db, row, day)

            def matches(s):
                if s["remaining"] < people:
                    return False
                hour = int(s["start_time"][:2])
                if time_of_day == "morning":
                    return hour < 12
                if time_of_day == "afternoon":
                    return 12 <= hour < 17
                if time_of_day == "evening":
                    return hour >= 17
                return True

            if not any(matches(s) for s in slots):
                continue
        items.append(a)
    if sort == "rating":
        items.sort(key=lambda a: -(a["rating"] or 0))
    if sort == "price_low":
        items.sort(key=lambda a: a["price"])
    return {
        "items": items[(page - 1) * limit : page * limit],
        "total": len(items),
        "pages": (len(items) + limit - 1) // limit,
        "page": page,
    }


@router.get("/favorites")
def favorites(db: DB, user: User):
    return [
        serialize(db, r)
        for r in db.execute(
            "SELECT a.* FROM activities a JOIN activity_favorites f ON f.activity_id=a.id WHERE f.user_id=? AND a.deleted=0",
            (user["id"],),
        )
    ]


@router.get("/bookings")
def bookings(db: DB, user: User):
    return reservations(
        db,
        db.execute(
            "SELECT * FROM activity_bookings WHERE user_id=? ORDER BY day,start_time",
            (user["id"],),
        ).fetchall(),
    )


@router.get("/host/dashboard")
def host_dashboard(db: DB, user: User):
    require_host(user)
    return {
        "items": [
            serialize(db, r)
            for r in db.execute(
                "SELECT * FROM activities WHERE host_id=? AND deleted=0 ORDER BY id DESC",
                (user["id"],),
            )
        ],
        "bookings": reservations(
            db,
            db.execute(
                "SELECT * FROM activity_bookings WHERE host_id=? ORDER BY day,start_time",
                (user["id"],),
            ).fetchall(),
        ),
    }


@router.post("/quote")
def quote(body: ReservationInput, db: DB, user: User):
    return calculate(db, body, user)[2]


@router.post("/bookings", status_code=201)
def reserve(
    body: ReservationInput,
    db: DB,
    user: User,
    idempotency_key: Annotated[
        str, Header(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    ],
):
    db.execute("BEGIN IMMEDIATE")
    try:
        fingerprint = hashlib.sha256(
            json.dumps(body.model_dump(), sort_keys=True).encode()
        ).hexdigest()
        old = db.execute(
            "SELECT * FROM activity_bookings WHERE user_id=? AND idempotency_key=?",
            (user["id"], idempotency_key),
        ).fetchone()
        if old:
            if old["fingerprint"] != fingerprint or old["status"] != "confirmed":
                raise HTTPException(
                    409, "This request key was already used. Start a new reservation."
                )
            return reservations(db, [old])[0]
        a, s, cost = calculate(db, body, user)
        if body.expected_total is None or cost["total"] != body.expected_total:
            raise HTTPException(409, "Review the current price before confirming.")
        values = {
            "activity_id": a["id"],
            "slot_id": s["id"],
            "user_id": user["id"],
            "host_id": a["host_id"],
            "kind": a["kind"],
            **cost,
            "idempotency_key": idempotency_key,
            "fingerprint": fingerprint,
        }
        bid = db.execute(
            "INSERT INTO activity_bookings("
            + ",".join(values)
            + ") VALUES("
            + ",".join("?" for _ in values)
            + ")",
            list(values.values()),
        ).lastrowid
        db.commit()
        return reservations(
            db,
            [
                db.execute(
                    "SELECT * FROM activity_bookings WHERE id=?", (bid,)
                ).fetchone()
            ],
        )[0]
    except sqlite3.IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            409, "This time is no longer available. Refresh and try again."
        ) from exc
    except Exception:
        db.rollback()
        raise


@router.delete("/bookings/{bid}")
def cancel(bid: int, db: DB, user: User):
    db.execute("BEGIN IMMEDIATE")
    row = db.execute(
        "SELECT * FROM activity_bookings WHERE id=? AND user_id=?", (bid, user["id"])
    ).fetchone()
    if not row:
        raise HTTPException(404, "Reservation not found.")
    if datetime.fromisoformat(row["day"] + "T" + row["start_time"]) <= now_india():
        raise HTTPException(422, "A started session cannot be cancelled.")
    db.execute("UPDATE activity_bookings SET status='cancelled' WHERE id=?", (bid,))
    db.commit()
    return {"status": "cancelled"}


@router.post("/host", status_code=201)
def create(body: ActivityInput, db: DB, user: User):
    return write(db, body, user)


@router.put("/host/{aid}")
def update(aid: int, body: ActivityInput, db: DB, user: User):
    return write(db, body, user, aid)


@router.delete("/host/{aid}")
def remove(aid: int, db: DB, user: User):
    require_host(user)
    db.execute("BEGIN IMMEDIATE")
    a = get_activity(db, aid)
    if a["host_id"] != user["id"]:
        raise HTTPException(403, "Only the owner can remove this offering.")
    if db.execute(
        "SELECT 1 FROM activity_bookings WHERE activity_id=? AND status='confirmed' AND day||' '||end_time>?",
        (aid, now_india().strftime("%Y-%m-%d %H:%M")),
    ).fetchone():
        raise HTTPException(
            409,
            "This offering has upcoming reservations. Remove it after they finish or are cancelled.",
        )
    db.execute("UPDATE activities SET deleted=1 WHERE id=?", (aid,))
    db.commit()
    return {"deleted": True}


@router.put("/favorites/{aid}")
def save(aid: int, db: DB, user: User):
    get_activity(db, aid)
    db.execute(
        "INSERT OR IGNORE INTO activity_favorites VALUES(?,?)", (user["id"], aid)
    )
    db.commit()
    return {"saved": True}


@router.delete("/favorites/{aid}")
def unsave(aid: int, db: DB, user: User):
    db.execute(
        "DELETE FROM activity_favorites WHERE user_id=? AND activity_id=?",
        (user["id"], aid),
    )
    db.commit()
    return {"saved": False}


@router.get("/{aid}")
def detail(aid: int, db: DB):
    a = get_activity(db, aid)
    return {
        **serialize(db, a),
        "slots": slots_for(db, a),
        "reviews": [
            dict(r)
            for r in db.execute(
                """SELECT r.*,u.name,u.avatar FROM activity_reviews r JOIN users u ON u.id=r.user_id WHERE activity_id=? ORDER BY r.id DESC""",
                (aid,),
            )
        ],
    }


