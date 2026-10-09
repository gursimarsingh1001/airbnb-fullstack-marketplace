"""Offering reads, capacity, provider conflicts, prices and atomic edits."""
from datetime import datetime, timedelta
from fastapi import HTTPException
from ..dependencies import require_host
from .activity_clock import now_india

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


