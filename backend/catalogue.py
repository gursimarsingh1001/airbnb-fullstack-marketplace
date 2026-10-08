"""Additive fictional catalogue expansion; never replaces existing homes or bookings."""

DESTINATIONS = [
    ('Candolim, Goa', 15.518, 73.762, 'Beachfront', 'Villa', 8900),
    ('Palolem, Goa', 15.010, 74.023, 'Beachfront', 'Cottage', 4600),
    ('Assagao, Goa', 15.601, 73.775, 'Amazing pools', 'Villa', 13500),
    ('Rishikesh, Uttarakhand', 30.087, 78.268, 'Amazing views', 'Apartment', 3800),
    ('Nainital, Uttarakhand', 29.391, 79.454, 'Lakefront', 'Cottage', 6100),
    ('Mussoorie, Uttarakhand', 30.459, 78.064, 'Cabins', 'Cabin', 8900),
    ('Dharamshala, Himachal Pradesh', 32.219, 76.323, 'Cabins', 'Cabin', 4900),
    ('Bir, Himachal Pradesh', 32.040, 76.720, 'Tiny homes', 'Tiny home', 3200),
    ('Munnar, Kerala', 10.089, 77.059, 'Countryside', 'Cottage', 5800),
    ('Wayanad, Kerala', 11.685, 76.132, 'Tropical', 'Villa', 7400),
    ('Kumarakom, Kerala', 9.617, 76.430, 'Lakefront', 'Cottage', 6800),
    ('Kochi, Kerala', 9.966, 76.242, 'Design', 'Apartment', 3500),
    ('Pondicherry, Tamil Nadu', 11.934, 79.830, 'Design', 'Apartment', 4300),
    ('Kodaikanal, Tamil Nadu', 10.239, 77.490, 'Cabins', 'Cabin', 6200),
    ('Chikmagalur, Karnataka', 13.316, 75.773, 'Countryside', 'Cottage', 5100),
    ('Gokarna, Karnataka', 14.547, 74.318, 'Beachfront', 'Cottage', 4100),
    ('Pushkar, Rajasthan', 26.489, 74.552, 'Design', 'Villa', 7100),
    ('Jodhpur, Rajasthan', 26.294, 73.019, 'Design', 'Apartment', 5600),
    ('Mahabaleshwar, Maharashtra', 17.923, 73.658, 'Amazing views', 'Villa', 9800),
    ('Panchgani, Maharashtra', 17.924, 73.800, 'Amazing pools', 'Villa', 11900),
    ('Darjeeling, West Bengal', 27.041, 88.266, 'Amazing views', 'Cottage', 4700),
    ('Gangtok, Sikkim', 27.338, 88.607, 'Amazing views', 'Apartment', 3900),
    ('Shillong, Meghalaya', 25.578, 91.893, 'Countryside', 'Cottage', 5200),
    ('Srinagar, Kashmir', 34.084, 74.797, 'Lakefront', 'Cottage', 8200),
]


def expand_catalogue(db):
    db.execute('CREATE TABLE IF NOT EXISTS demo_content_versions (version TEXT PRIMARY KEY)')
    if db.execute("SELECT 1 FROM demo_content_versions WHERE version='catalogue-v2'").fetchone():
        return
    for index, (location, lat, lon, category, kind, price) in enumerate(DESTINATIONS):
        template = db.execute('SELECT * FROM listings WHERE category=? ORDER BY id LIMIT 1', (category,)).fetchone()
        if not template:
            continue
        town = location.split(',')[0]
        title = f"{['The slow living', 'Sunlit', 'The peaceful', 'A little'][index % 4]} {kind.lower()} in {town}"
        description = (f"Make yourself at home in {town}. This fictional {kind.lower()} pairs a comfortable private space "
                       "with a relaxed outdoor corner for morning coffee. Cook together in the equipped kitchen, "
                       "unwind with a book, and explore the neighbourhood at your own pace.\n\n"
                       "Fresh linen, Wi-Fi and thoughtful local recommendations are included. "
                       "Photos are illustrative and the map shows an approximate town location.")
        capacity = 2 if kind == 'Tiny home' else 4 if kind in ('Apartment', 'Cottage') else 6
        cursor = db.execute('''INSERT INTO listings(host_id,title,description,location,country,category,
            property_type,price,cleaning_fee,max_guests,bedrooms,beds,bathrooms,latitude,longitude,superhost)
            VALUES(2,?,?,?,'India',?,?,?,?,?,?,?,2,?,?,?)''',
            (title, description, location, category, kind, price, 650, capacity,
             1 if capacity == 2 else 2, 1 if capacity == 2 else 3, lat, lon, int(index % 3 != 0)))
        listing_id = cursor.lastrowid
        db.execute('INSERT INTO photos(listing_id,url,position) SELECT ?,url,position FROM photos WHERE listing_id=?', (listing_id, template['id']))
        db.execute('INSERT INTO listing_amenities SELECT ?,amenity_id FROM listing_amenities WHERE listing_id=?', (listing_id, template['id']))
        db.execute("INSERT INTO reviews(listing_id,user_id,rating,comment) VALUES(?,5,?,?)",
                   (listing_id, 4 if index % 4 == 0 else 5, 'A comfortable, thoughtfully arranged stay. We enjoyed the quiet mornings and helpful local tips.'))
    db.execute("INSERT INTO demo_content_versions VALUES('catalogue-v2')")
