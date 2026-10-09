"""Original illustrative seed content with rolling future demo availability."""

from datetime import date, timedelta
from .booking_rules import booking_today

EXPERIENCES = [
    ("Food & drink", "Cook a regional feast", "photo-1556911220-bff31c812dba"),
    (
        "Culture & history",
        "Walk the old city with a storyteller",
        "photo-1524492412937-b28074a5d7da",
    ),
    (
        "Nature & outdoors",
        "Follow a local trail at sunrise",
        "photo-1551632811-561732d1e306",
    ),
    (
        "Art & creativity",
        "Shape your own pottery keepsake",
        "photo-1493106641515-6b5631de4bb9",
    ),
    ("Sports", "Discover the coast by kayak", "photo-1472746729193-36ad213ac4a5"),
    (
        "Wellness",
        "A gentle yoga and breathwork session",
        "photo-1544367567-0f2fcb009e0b",
    ),
    (
        "Nightlife",
        "Live music and neighbourhood stories",
        "photo-1514525253161-7a46d19cd819",
    ),
    (
        "Hidden gems",
        "Markets and hidden courtyards",
        "photo-1516483638261-f4dbaf036963",
    ),
    (
        "Food & drink",
        "Learn the art of handmade pasta",
        "photo-1551183053-bf91a1d81141",
    ),
    (
        "Art & creativity",
        "Capture the city on a photo walk",
        "photo-1452587925148-ce544e77e70d",
    ),
]
SERVICES = [
    (
        "Private chefs",
        "A seasonal dinner at your stay",
        "photo-1556911220-bff31c812dba",
    ),
    ("Photography", "Portraits from your holiday", "photo-1452587925148-ce544e77e70d"),
    ("Massage", "A relaxing massage session", "photo-1540555700478-4be289fbecef"),
    (
        "Personal training",
        "A personal movement session",
        "photo-1517836357463-d25dfeac3438",
    ),
    ("Beauty", "Makeup for a special evening", "photo-1524504388940-b1c1722653e1"),
    ("Hair styling", "Hair styling for your occasion", "photo-1562322140-8baeececf3df"),
    (
        "Spa & wellness",
        "A restorative wellness ritual",
        "photo-1540555700478-4be289fbecef",
    ),
    ("Catering", "A relaxed brunch for your group", "photo-1555939594-58d7cb561ad1"),
    (
        "Private guides",
        "Your personalised local itinerary",
        "photo-1524492412937-b28074a5d7da",
    ),
    ("Photography", "Golden-hour couple portraits", "photo-1519741497674-611481863552"),
]
CITIES = [
    ("Goa", "India"),
    ("Jaipur", "India"),
    ("Bali", "Indonesia"),
    ("Manali", "India"),
    ("Rome", "Italy"),
    ("Mumbai", "India"),
    ("Barcelona", "Spain"),
    ("Delhi", "India"),
    ("London", "United Kingdom"),
    ("Udaipur", "India"),
]


def seed_activities(db):
    if not db.execute(
        "SELECT 1 FROM demo_content_versions WHERE version='activities-v1'"
    ).fetchone():
        for kind, templates in [("experiences", EXPERIENCES), ("services", SERVICES)]:
            for i in range(20):
                category, title, photo = templates[i % 10]
                city, country = CITIES[(i + (2 if i >= 10 else 0)) % 10]
                title += f" in {city}"
                aid = db.execute(
                    """INSERT INTO activities(kind,host_id,title,description,location,country,category,price,price_type,
                    duration_minutes,capacity,language,setting,service_location,itinerary,included,requirements,seeded)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
                    (
                        kind,
                        2 + i % 3,
                        title,
                        f"Spend time discovering {city} with a thoughtful local host. This fictional offering pairs personal attention with a relaxed pace. All images and reviews are illustrative demo content.",
                        city,
                        country,
                        category,
                        1800 + (i % 7) * 650,
                        "person" if kind == "experiences" or i % 2 else "group",
                        60 + (i % 3) * 30,
                        8 if kind == "experiences" else 6,
                        "English" if i % 3 else "Hindi",
                        "Outdoor" if i % 2 else "Indoor",
                        "At your stay" if i % 2 else "Provider location",
                        "Meet your host and get comfortable.\nEnjoy a guided, hands-on session.\nFinish with time for questions and local recommendations.",
                        "Equipment and materials\nGuidance from your host\nDrinking water",
                        "Arrive 10 minutes early. Tell the provider about accessibility needs or dietary requirements before your session. No real appointments are provided by this educational demo.",
                    ),
                ).lastrowid
                for n, p in enumerate([photo, photo, photo]):
                    db.execute(
                        "INSERT INTO activity_photos(activity_id,url,position) VALUES(?,?,?)",
                        (
                            aid,
                            f"https://images.unsplash.com/{p}?auto=format&fit=crop&w=1200&q=80",
                            n,
                        ),
                    )
                for uid, rating in [(5, 5), (6, 4 if i % 3 == 0 else 5)]:
                    db.execute(
                        "INSERT INTO activity_reviews(activity_id,user_id,rating,comment) VALUES(?,?,?,?)",
                        (
                            aid,
                            uid,
                            rating,
                            "A thoughtful host, a friendly welcome, and a memorable part of our trip.",
                        ),
                    )
        db.execute("INSERT INTO demo_content_versions VALUES('activities-v1')")
    # Repair only the known broken demo asset; preserve provider photos and edits.
    db.execute(
        "UPDATE activity_photos SET url=replace(url,?,?) WHERE url LIKE ? AND activity_id IN (SELECT id FROM activities WHERE seeded=1)",
        (
            "photo-1565193298595-6ba6e8b29d16",
            "photo-1493106641515-6b5631de4bb9",
            "https://images.unsplash.com/photo-1565193298595-6ba6e8b29d16%",
        ),
    )
    # Only extend beyond the previous horizon; never recreate a provider-removed slot.
    key = "activity-slots-through"
    db.execute(
        "CREATE TABLE IF NOT EXISTS demo_seed_state (key TEXT PRIMARY KEY,value TEXT NOT NULL)"
    )
    row = db.execute("SELECT value FROM demo_seed_state WHERE key=?", (key,)).fetchone()
    horizon = booking_today() + timedelta(days=60)
    first = (
        booking_today() + timedelta(days=1)
        if not row
        else date.fromisoformat(row[0]) + timedelta(days=1)
    )
    if first <= horizon:
        slots = []
        for a in db.execute(
            "SELECT id,capacity FROM activities WHERE seeded=1 AND deleted=0"
        ):
            for offset in range((horizon - first).days + 1):
                for time in ["09:00", "14:00", "18:00"]:
                    slots.append(
                        (
                            a["id"],
                            str(first + timedelta(days=offset)),
                            time,
                            a["capacity"],
                        )
                    )
        db.executemany(
            "INSERT OR IGNORE INTO activity_slots(activity_id,day,start_time,capacity) VALUES(?,?,?,?)",
            slots,
        )
        db.execute(
            "INSERT OR REPLACE INTO demo_seed_state VALUES(?,?)", (key, str(horizon))
        )
    if not db.execute(
        "SELECT 1 FROM demo_content_versions WHERE version='activity-bookings-v1'"
    ).fetchone():
        for kind, uid, offset in [("experiences", 5, 7), ("services", 6, 8)]:
            a = db.execute(
                "SELECT * FROM activities WHERE kind=? AND seeded=1 ORDER BY id LIMIT 1",
                (kind,),
            ).fetchone()
            if not a:
                continue
            s = db.execute(
                "SELECT * FROM activity_slots WHERE activity_id=? AND day=? ORDER BY start_time LIMIT 1",
                (a["id"], str(booking_today() + timedelta(days=offset))),
            ).fetchone()
            if not s:
                continue
            from datetime import datetime

            end = (
                datetime.fromisoformat(s["day"] + "T" + s["start_time"])
                + timedelta(minutes=a["duration_minutes"])
            ).strftime("%H:%M")
            subtotal = a["price"] * (2 if a["price_type"] == "person" else 1)
            fee = (subtotal * 10 + 50) // 100
            db.execute(
                """INSERT INTO activity_bookings(activity_id,slot_id,user_id,host_id,kind,day,start_time,end_time,
                people,unit_price,price_type,subtotal,service_fee,total,idempotency_key,fingerprint)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    a["id"],
                    s["id"],
                    uid,
                    a["host_id"],
                    kind,
                    s["day"],
                    s["start_time"],
                    end,
                    2,
                    a["price"],
                    a["price_type"],
                    subtotal,
                    fee,
                    subtotal + fee,
                    "demo-" + kind,
                    "seed",
                ),
            )
        db.execute("INSERT INTO demo_content_versions VALUES('activity-bookings-v1')")
