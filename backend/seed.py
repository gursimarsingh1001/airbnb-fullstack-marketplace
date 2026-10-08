from datetime import timedelta
from .booking_rules import booking_today


def photo(key):
    return f"https://images.unsplash.com/{key}?auto=format&fit=crop&w=1200&q=85"


HOMES = [
    (
        "A little closer to paradise",
        "Ubud, Bali",
        "Indonesia",
        "Tropical",
        "Villa",
        12400,
        "photo-1613977257363-707ba9348227",
        -8.5069,
        115.2625,
    ),
    (
        "The hillside hideaway",
        "Manali, Himachal Pradesh",
        "India",
        "Cabins",
        "Cabin",
        6850,
        "photo-1449158743715-0a90ebb6d2d8",
        32.2396,
        77.1887,
    ),
    (
        "Slow days by the sea",
        "Anjuna, Goa",
        "India",
        "Beachfront",
        "Villa",
        9200,
        "photo-1613490493576-7fde63acd811",
        15.5739,
        73.7448,
    ),
    (
        "A cabin above the clouds",
        "Jibhi, Himachal Pradesh",
        "India",
        "Amazing views",
        "Cabin",
        5400,
        "photo-1449158743715-0a90ebb6d2d8",
        31.5937,
        77.3528,
    ),
    (
        "Your own slice of Tuscany",
        "Florence, Tuscany",
        "Italy",
        "Countryside",
        "Villa",
        18700,
        "photo-1470770841072-f978cf4d019e",
        43.7696,
        11.2558,
    ),
    (
        "An escape in the coffee hills",
        "Coorg, Karnataka",
        "India",
        "Countryside",
        "Cottage",
        7800,
        "photo-1449844908441-8829872d2607",
        12.3375,
        75.8069,
    ),
    (
        "Ocean air, everywhere",
        "Varkala, Kerala",
        "India",
        "Beachfront",
        "Cottage",
        4950,
        "photo-1499793983690-e29da59ef1c2",
        8.7379,
        76.7163,
    ),
    (
        "The glasshouse in the woods",
        "Ooty, Tamil Nadu",
        "India",
        "Design",
        "Cabin",
        11200,
        "photo-1510798831971-661eb04b3739",
        11.4102,
        76.6950,
    ),
    (
        "A pool with a point of view",
        "Alibaug, Maharashtra",
        "India",
        "Amazing pools",
        "Villa",
        15900,
        "photo-1613977257592-4871e5fcd7c4",
        18.6414,
        72.8722,
    ),
    (
        "Life on the lake",
        "Udaipur, Rajasthan",
        "India",
        "Lakefront",
        "Apartment",
        8600,
        "photo-1600607687920-4e2a09cf159d",
        24.5854,
        73.7125,
    ),
    (
        "The little woodland retreat",
        "Mukteshwar, Uttarakhand",
        "India",
        "Tiny homes",
        "Tiny home",
        4200,
        "photo-1518780664697-55e3ad937233",
        29.4722,
        79.6479,
    ),
    (
        "Sun-drenched island living",
        "Canggu, Bali",
        "Indonesia",
        "Tropical",
        "Villa",
        13800,
        "photo-1571896349842-33c89424de2d",
        -8.6478,
        115.1385,
    ),
    (
        "A home among the pines",
        "Shimla, Himachal Pradesh",
        "India",
        "Cabins",
        "Cabin",
        7200,
        "photo-1510798831971-661eb04b3739",
        31.1048,
        77.1734,
    ),
    (
        "Where the ocean meets the sky",
        "Santorini",
        "Greece",
        "Amazing views",
        "Villa",
        22400,
        "photo-1613490493576-7fde63acd811",
        36.3932,
        25.4615,
    ),
    (
        "A quiet corner of the city",
        "Jaipur, Rajasthan",
        "India",
        "Design",
        "Apartment",
        5900,
        "photo-1600210492486-724fe5c67fb0",
        26.9124,
        75.7873,
    ),
    (
        "Weekend at the farmhouse",
        "Lonavala, Maharashtra",
        "India",
        "Amazing pools",
        "Villa",
        14600,
        "photo-1613977257363-707ba9348227",
        18.7546,
        73.4062,
    ),
    (
        "The lakeside cottage",
        "Nainital, Uttarakhand",
        "India",
        "Lakefront",
        "Cottage",
        6300,
        "photo-1470770841072-f978cf4d019e",
        29.3919,
        79.4542,
    ),
    (
        "A small home, a big escape",
        "Wayanad, Kerala",
        "India",
        "Tiny homes",
        "Tiny home",
        4800,
        "photo-1449844908441-8829872d2607",
        11.6854,
        76.1320,
    ),
    (
        "Your private tropical garden",
        "Siolim, Goa",
        "India",
        "Tropical",
        "Villa",
        11900,
        "photo-1613977257592-4871e5fcd7c4",
        15.6177,
        73.7678,
    ),
    (
        "Morning light in the mountains",
        "Rishikesh, Uttarakhand",
        "India",
        "Amazing views",
        "Apartment",
        5100,
        "photo-1600607687939-ce8a6c25118c",
        30.0869,
        78.2676,
    ),
]


def seed(db):
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return
    db.executemany(
        "INSERT INTO users VALUES (?,?,?,?,?)",
        [
            (1, "Alex Morgan", "guest", "AM", 2024),
            (2, "Ananya Sharma", "host", "AS", 2018),
            (3, "Marco Rossi", "host", "MR", 2016),
            (4, "Made Putra", "host", "MP", 2019),
            (5, "Sarah Chen", "guest", "SC", 2022),
            (6, "Rohan Kapoor", "guest", "RK", 2021),
        ],
    )
    amenities = [
        "Wifi",
        "Kitchen",
        "Free parking",
        "Air conditioning",
        "Pool",
        "Mountain view",
        "Beach access",
        "Washer",
        "Workspace",
        "Garden",
        "Lake view",
        "Hot tub",
    ]
    db.executemany("INSERT INTO amenities(name) VALUES (?)", [(a,) for a in amenities])
    interiors = [
        "photo-1600210492486-724fe5c67fb0",
        "photo-1600607687920-4e2a09cf159d",
        "photo-1600607687939-ce8a6c25118c",
        "photo-1616486338812-3dadae4b4ace",
    ]
    for i, (title, loc, country, cat, kind, price, img, lat, lon) in enumerate(
        HOMES, 1
    ):
        host = (
            4 if country == "Indonesia" else 3 if country in ["Italy", "Greece"] else 2
        )
        desc = f"Take a breath. You have arrived at {title.lower()}, a thoughtfully designed {kind.lower()} in {loc}. Wake up slowly, settle into your favourite corner, and make yourself at home.\n\nThe space brings together natural materials, comfortable beds, and little details that make a stay special. Share breakfast on the terrace or spend an unhurried afternoon exploring the neighbourhood.\n\nYou will have the entire place to yourself, a fully equipped kitchen, fresh linens, and a local host happy to share their favourite hidden gems."
        db.execute(
            """INSERT INTO listings(id,host_id,title,description,location,country,category,property_type,price,cleaning_fee,max_guests,bedrooms,beds,bathrooms,latitude,longitude,superhost)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                i,
                host,
                title,
                desc,
                loc,
                country,
                cat,
                kind,
                price,
                900,
                2 if kind == "Tiny home" else 6,
                1 if kind == "Tiny home" else 2,
                1 if kind == "Tiny home" else 3,
                2,
                lat,
                lon,
                int(i % 4 != 0),
            ),
        )
        db.executemany(
            "INSERT INTO photos(listing_id,url,position) VALUES (?,?,?)",
            [(i, photo(p), n) for n, p in enumerate([img] + interiors)],
        )
        names = ["Wifi", "Kitchen", "Free parking", "Garden", "Workspace"]
        if cat in ["Tropical", "Amazing pools"]:
            names += ["Pool", "Air conditioning"]
        if cat in ["Amazing views", "Cabins"]:
            names += ["Mountain view", "Hot tub"]
        if cat == "Beachfront":
            names += ["Beach access", "Air conditioning"]
        if cat == "Lakefront":
            names += ["Lake view"]
        for a in names:
            db.execute(
                "INSERT INTO listing_amenities SELECT ?,id FROM amenities WHERE name=?",
                (i, a),
            )
        for j, (uid, comment) in enumerate(
            [
                (
                    5,
                    "Such a beautiful space. The photos really do not do it justice. Everything was thoughtfully prepared and we felt at home immediately.",
                ),
                (
                    6,
                    "A wonderful few days away. The location is peaceful, the beds are very comfortable, and our host had brilliant local recommendations.",
                ),
                (
                    1,
                    "One of our favourite stays. Morning coffee on the terrace was the highlight. We would happily come back.",
                ),
            ]
        ):
            db.execute(
                "INSERT INTO reviews(listing_id,user_id,rating,comment,created_at) VALUES (?,?,?,?,?)",
                (
                    i,
                    uid,
                    4 if i % 3 == 0 and j == 1 else 5,
                    comment,
                    str(booking_today() - timedelta(days=20 + j * 24)),
                ),
            )
    for lid, uid, days in [(1, 5, 7), (2, 1, 14), (3, 6, 5), (5, 5, 21)]:
        p = HOMES[lid - 1][5]
        subtotal = p * 3
        fee = (subtotal * 14 + 50) // 100
        db.execute(
            "INSERT INTO bookings(listing_id,user_id,check_in,check_out,guests,nightly_price,cleaning_fee,service_fee,total) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                lid,
                uid,
                str(booking_today() + timedelta(days=days)),
                str(booking_today() + timedelta(days=days + 3)),
                2,
                p,
                900,
                fee,
                subtotal + 900 + fee,
            ),
        )
    db.execute("INSERT INTO wishlists VALUES(1,1)")
