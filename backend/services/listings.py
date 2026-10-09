"""Listing reads, serialization and atomic photo/amenity updates."""
from fastapi import HTTPException
from ..booking_rules import booking_today

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


def write_listing(db, body, user, id=None):
    db.execute("BEGIN IMMEDIATE")
    data = body.model_dump(exclude={"photos", "amenities"})
    if id:
        row = listing_row(db, id)
        if row["host_id"] != user["id"]:
            raise HTTPException(403, "Only the owner can edit this listing.")
        if db.execute("SELECT 1 FROM bookings WHERE listing_id=? AND status='confirmed' AND check_out>? AND guests>?", (id, str(booking_today()), body.max_guests)).fetchone():
            raise HTTPException(409, "Guest capacity cannot be reduced below an upcoming reservation's guest count.")
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


