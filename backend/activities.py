"""Experiences and services API: shared content, explicit capacity/time rules."""

from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Literal
import hashlib
import json
import sqlite3
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from .dependencies import DB, User, require_host
from .activity_seed import EXPERIENCES, SERVICES

router = APIRouter(prefix="/api/activities", tags=["Experiences and services"])
Kind = Literal["experiences", "services"]


def now_india():
    return datetime.now(timezone(timedelta(minutes=330))).replace(tzinfo=None)


def get_activity(db, aid, deleted=False):
    row = db.execute(
        "SELECT * FROM activities WHERE id=?" + ("" if deleted else " AND deleted=0"),
        (aid,),
    ).fetchone()
    if not row:
        raise HTTPException(404, "This offering is no longer available.")
    return row


def serialize(db, row):
    a = dict(row)
    a["photos"] = [
        r[0]
        for r in db.execute(
            "SELECT url FROM activity_photos WHERE activity_id=? ORDER BY position",
            (a["id"],),
        )
    ]
    a["host"] = dict(
        db.execute("SELECT * FROM users WHERE id=?", (a["host_id"],)).fetchone()
    )
    stats = db.execute(
        "SELECT AVG(rating),COUNT(*) FROM activity_reviews WHERE activity_id=?",
        (a["id"],),
    ).fetchone()
    a["rating"] = round(stats[0], 2) if stats[0] else None
    a["review_count"] = stats[1]
    return a


def available(db, a, s):
    start = datetime.fromisoformat(s["day"] + "T" + s["start_time"])
    end = start + timedelta(minutes=a["duration_minutes"])
    if not s["active"] or start <= now_india() or end.date() != start.date():
        return 0
    occupied = db.execute(
        """SELECT 1 FROM activity_bookings WHERE host_id=? AND day=? AND status='confirmed'
        AND start_time<? AND end_time>? AND (?='services' OR kind='services' OR slot_id!=?)""",
        (
            a["host_id"],
            s["day"],
            end.strftime("%H:%M"),
            s["start_time"],
            a["kind"],
            s["id"],
        ),
    ).fetchone()
    if occupied:
        return 0
    used = db.execute(
        "SELECT COALESCE(SUM(people),0) FROM activity_bookings WHERE slot_id=? AND status='confirmed'",
        (s["id"],),
    ).fetchone()[0]
    return max(0, min(a["capacity"], s["capacity"]) - used)


def slots_for(db, a, day=None):
    rows = db.execute(
        "SELECT * FROM activity_slots WHERE activity_id=? AND active=1 AND day>=?"
        + (" AND day=?" if day else "")
        + " ORDER BY day,start_time",
        [a["id"], str(now_india().date())] + ([str(day)] if day else []),
    ).fetchall()
    return [{**dict(s), "remaining": available(db, a, s)} for s in rows]


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
                hour = int(s["start_time"][:2])
                return s["remaining"] >= people and (
                    not time_of_day
                    or (
                        hour < 12
                        if time_of_day == "morning"
                        else (
                            12 <= hour < 17
                            if time_of_day == "afternoon"
                            else hour >= 17
                        )
                    )
                )

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


def reservations(db, rows):
    return [
        {k: r[k] for k in r.keys() if k not in ("fingerprint", "idempotency_key")}
        | {
            "activity": serialize(db, get_activity(db, r["activity_id"], True)),
            "guest_name": db.execute(
                "SELECT name FROM users WHERE id=?", (r["user_id"],)
            ).fetchone()[0],
        }
        for r in rows
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


class ReservationInput(BaseModel):
    slot_id: int = Field(strict=True, ge=1)
    people: int = Field(strict=True, ge=1, le=30)
    expected_total: int | None = Field(None, strict=True, ge=1)


def calculate(db, body, user):
    s = db.execute(
        "SELECT * FROM activity_slots WHERE id=?", (body.slot_id,)
    ).fetchone()
    if not s:
        raise HTTPException(404, "Time slot not found.")
    a = get_activity(db, s["activity_id"])
    if a["host_id"] == user["id"]:
        raise HTTPException(422, "You cannot reserve your own offering.")
    if body.people > a["capacity"] or body.people > s["capacity"]:
        raise HTTPException(422, "This session cannot accommodate that many people.")
    if datetime.fromisoformat(s["day"] + "T" + s["start_time"]) <= now_india():
        raise HTTPException(422, "Choose a future date and time (India time).")
    if available(db, a, s) < body.people:
        raise HTTPException(
            409,
            "This time is unavailable or has insufficient seats. Choose another slot.",
        )
    subtotal = a["price"] * (body.people if a["price_type"] == "person" else 1)
    fee = (subtotal * 10 + 50) // 100
    end = (
        datetime.fromisoformat(s["day"] + "T" + s["start_time"])
        + timedelta(minutes=a["duration_minutes"])
    ).strftime("%H:%M")
    return (
        a,
        s,
        {
            "unit_price": a["price"],
            "price_type": a["price_type"],
            "people": body.people,
            "subtotal": subtotal,
            "service_fee": fee,
            "total": subtotal + fee,
            "day": s["day"],
            "start_time": s["start_time"],
            "end_time": end,
        },
    )


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


class SlotInput(BaseModel):
    day: date
    start_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    capacity: int = Field(strict=True, ge=1, le=30)


class ActivityInput(BaseModel):
    kind: Kind
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=30, max_length=5000)
    location: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=80)
    category: str
    price: int = Field(strict=True, ge=100, le=1000000)
    price_type: Literal["person", "group"] = "person"
    duration_minutes: int = Field(strict=True, ge=30, le=480)
    capacity: int = Field(strict=True, ge=1, le=30)
    language: Literal["English", "Hindi", "Italian", "Spanish", "Indonesian"] = (
        "English"
    )
    setting: Literal["Indoor", "Outdoor", "Either"] = "Either"
    service_location: Literal["At your stay", "Provider location", "Either"] = "Either"
    itinerary: str = Field(min_length=10, max_length=3000)
    included: str = Field(min_length=5, max_length=2000)
    requirements: str = Field(min_length=5, max_length=2000)
    photos: list[HttpUrl] = Field(min_length=1, max_length=12)
    slots: list[SlotInput] = Field(min_length=1, max_length=240)

    @field_validator(
        "title",
        "description",
        "location",
        "country",
        "itinerary",
        "included",
        "requirements",
        mode="before",
    )
    @classmethod
    def trim(cls, v):
        return v.strip() if isinstance(v, str) else v

    @model_validator(mode="after")
    def valid(self):
        categories = [
            r[0] for r in (EXPERIENCES if self.kind == "experiences" else SERVICES)
        ]
        if self.category not in categories:
            raise ValueError("Choose a valid category for this offering.")
        if self.kind == "experiences" and self.price_type != "person":
            raise ValueError("Experiences are priced per person.")
        if any(p.scheme != "https" for p in self.photos):
            raise ValueError("Use HTTPS photo URLs.")
        seen = set()
        for s in self.slots:
            start = datetime.fromisoformat(str(s.day) + "T" + s.start_time)
            if start <= now_india() or s.day > now_india().date() + timedelta(days=730):
                raise ValueError(
                    "Availability must be in the future, within two years."
                )
            if (start + timedelta(minutes=self.duration_minutes)).date() != s.day:
                raise ValueError("Sessions must end before midnight.")
            if s.capacity > self.capacity:
                raise ValueError("Slot capacity cannot exceed the offering capacity.")
            key = (s.day, s.start_time)
            if key in seen:
                raise ValueError("Availability contains duplicate time slots.")
            seen.add(key)
        return self


def write(db, body, user, aid=None):
    require_host(user)
    db.execute("BEGIN IMMEDIATE")
    try:
        data = body.model_dump(exclude={"photos", "slots"})
        if aid:
            a = get_activity(db, aid)
            if a["host_id"] != user["id"]:
                raise HTTPException(403, "Only the owner can edit this offering.")
            if a["kind"] != body.kind:
                raise HTTPException(422, "The offering type cannot be changed.")
            future = db.execute(
                "SELECT * FROM activity_bookings WHERE activity_id=? AND status='confirmed' AND day||' '||end_time>?",
                (aid, now_india().strftime("%Y-%m-%d %H:%M")),
            ).fetchall()
            if future and body.duration_minutes != a["duration_minutes"]:
                raise HTTPException(
                    409, "Duration cannot change while upcoming reservations exist."
                )
            for b in future:
                slot = next(
                    (
                        s
                        for s in body.slots
                        if str(s.day) == b["day"] and s.start_time == b["start_time"]
                    ),
                    None,
                )
                used = db.execute(
                    "SELECT SUM(people) FROM activity_bookings WHERE slot_id=? AND status='confirmed'",
                    (b["slot_id"],),
                ).fetchone()[0]
                if slot is None or slot.capacity < used or body.capacity < used:
                    raise HTTPException(
                        409,
                        "Keep booked slots and sufficient capacity for existing reservations.",
                    )
            db.execute(
                "UPDATE activities SET "
                + ",".join(k + "=?" for k in data)
                + " WHERE id=?",
                list(data.values()) + [aid],
            )
            db.execute("DELETE FROM activity_photos WHERE activity_id=?", (aid,))
            db.execute("UPDATE activity_slots SET active=0 WHERE activity_id=?", (aid,))
        else:
            data["host_id"] = user["id"]
            aid = db.execute(
                "INSERT INTO activities("
                + ",".join(data)
                + ") VALUES("
                + ",".join("?" for _ in data)
                + ")",
                list(data.values()),
            ).lastrowid
        db.executemany(
            "INSERT INTO activity_photos(activity_id,url,position) VALUES(?,?,?)",
            [(aid, str(p), i) for i, p in enumerate(body.photos)],
        )
        for s in body.slots:
            db.execute(
                """INSERT INTO activity_slots(activity_id,day,start_time,capacity) VALUES(?,?,?,?)
                ON CONFLICT(activity_id,day,start_time) DO UPDATE SET capacity=excluded.capacity,active=1""",
                (aid, str(s.day), s.start_time, s.capacity),
            )
        db.commit()
        return serialize(db, get_activity(db, aid))
    except Exception:
        db.rollback()
        raise


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
