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


def expand_large_catalogue(db):
    """Add 196 varied fictional stays once, for a 240-home initial catalogue."""
    if db.execute("SELECT 1 FROM demo_content_versions WHERE version='catalogue-v3'").fetchone():
        return
    templates = db.execute('SELECT * FROM listings WHERE id<=44 ORDER BY id').fetchall()
    names = ['Terrace retreat', 'Garden hideaway', 'Sunrise house', 'Courtyard escape',
             'The reading room', 'Quiet mornings', 'The weekend home', 'Little sanctuary']
    for i in range(196):
        source = templates[i % len(templates)]
        variant = i // len(templates)
        town = source['location'].split(',')[0]
        title = f"{names[(i + variant) % len(names)]} in {town} · {variant + 1}"
        price = max(1800, source['price'] + (i % 9 - 4) * 450)
        latitude = source['latitude'] + ((i % 7) - 3) * .008
        longitude = source['longitude'] + ((i % 11) - 5) * .008
        cursor = db.execute('''INSERT INTO listings(host_id,title,description,location,country,category,
            property_type,price,cleaning_fee,max_guests,bedrooms,beds,bathrooms,latitude,longitude,superhost)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (source['host_id'], title,
             f"A fictional {source['property_type'].lower()} in {town}, with space to relax and make yourself at home. "
             "Enjoy a well-equipped kitchen, fresh linens and a comfortable living area. "
             "Your host can suggest local walks and places to eat. Photos are illustrative; map positions are approximate.",
             source['location'], source['country'], source['category'], source['property_type'], price,
             source['cleaning_fee'], source['max_guests'], source['bedrooms'], source['beds'], source['bathrooms'],
             latitude, longitude, int(i % 3 != 0)))
        lid = cursor.lastrowid
        photos = db.execute('SELECT url FROM photos WHERE listing_id=? ORDER BY position', (source['id'],)).fetchall()
        # Alternate exterior and interior covers while retaining complete galleries.
        offset = i % min(3, len(photos)) if photos else 0
        photos = photos[offset:] + photos[:offset]
        db.executemany('INSERT INTO photos(listing_id,url,position) VALUES(?,?,?)', [(lid, row['url'], n) for n, row in enumerate(photos)])
        db.execute('INSERT INTO listing_amenities SELECT ?,amenity_id FROM listing_amenities WHERE listing_id=?', (lid, source['id']))
        db.execute('INSERT INTO reviews(listing_id,user_id,rating,comment) VALUES(?,5,?,?)',
                   (lid, 4 if i % 5 == 0 else 5, 'A relaxing stay with comfortable rooms and a helpful host. We enjoyed exploring the area.'))
    db.execute("INSERT INTO demo_content_versions VALUES('catalogue-v3')")

# Broaden coverage rather than placing more variants in the same resort towns.
REGIONAL_DESTINATIONS = [
    ('Delhi', 'India', 28.614, 77.209), ('Mumbai, Maharashtra', 'India', 19.076, 72.878),
    ('Bengaluru, Karnataka', 'India', 12.972, 77.595), ('Hyderabad, Telangana', 'India', 17.385, 78.487),
    ('Chennai, Tamil Nadu', 'India', 13.083, 80.271), ('Kolkata, West Bengal', 'India', 22.573, 88.364),
    ('Ahmedabad, Gujarat', 'India', 23.023, 72.571), ('Varanasi, Uttar Pradesh', 'India', 25.318, 82.974),
    ('Amritsar, Punjab', 'India', 31.634, 74.873), ('Lucknow, Uttar Pradesh', 'India', 26.847, 80.946),
    ('Bhopal, Madhya Pradesh', 'India', 23.260, 77.413), ('Raipur, Chhattisgarh', 'India', 21.251, 81.630),
    ('Ranchi, Jharkhand', 'India', 23.344, 85.310), ('Patna, Bihar', 'India', 25.594, 85.138),
    ('Guwahati, Assam', 'India', 26.145, 91.736), ('Tawang, Arunachal Pradesh', 'India', 27.586, 91.859),
    ('Imphal, Manipur', 'India', 24.817, 93.937), ('Aizawl, Mizoram', 'India', 23.728, 92.718),
    ('Agartala, Tripura', 'India', 23.831, 91.287), ('Kohima, Nagaland', 'India', 25.675, 94.108),
    ('Leh, Ladakh', 'India', 34.153, 77.577), ('Port Blair, Andaman Islands', 'India', 11.623, 92.726),
    ('Puri, Odisha', 'India', 19.814, 85.831), ('Visakhapatnam, Andhra Pradesh', 'India', 17.687, 83.218),
    ('Kathmandu', 'Nepal', 27.717, 85.324), ('Pokhara', 'Nepal', 28.210, 83.986),
    ('Galle', 'Sri Lanka', 6.053, 80.221), ('Ella', 'Sri Lanka', 6.867, 81.047),
    ('Phuket', 'Thailand', 7.881, 98.392), ('Chiang Mai', 'Thailand', 18.788, 98.985),
    ('Bangkok', 'Thailand', 13.756, 100.502), ('Colombo', 'Sri Lanka', 6.927, 79.861),
]


def expand_regional_catalogue(db):
    """32 new destinations, once; no updates to user-created content."""
    if db.execute("SELECT 1 FROM demo_content_versions WHERE version='catalogue-v4'").fetchone():
        return
    for index, (location, country, latitude, longitude) in enumerate(REGIONAL_DESTINATIONS):
        category = 'Amazing views' if index in (15, 16, 17, 19, 20, 25, 27) else 'Beachfront' if index in (21, 22, 23, 26, 28) else 'Design'
        source = db.execute('SELECT * FROM listings WHERE category=? ORDER BY id LIMIT 1', (category,)).fetchone()
        if not source:
            continue
        title = f"{['The sunlit home', 'A quiet corner', 'The open-window retreat', 'Your little getaway'][index % 4]} in {location.split(',')[0]}"
        lid = db.execute('''INSERT INTO listings(host_id,title,description,location,country,category,
            property_type,price,cleaning_fee,max_guests,bedrooms,beds,bathrooms,latitude,longitude,superhost)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (2 + index % 3, title, f'A fictional demo home in {location}, {country}. Settle into a comfortable private space with a kitchen, fresh linen and room to unwind. Photography is illustrative and the map position is approximate.',
             location, country, category, source['property_type'], 3200 + index % 8 * 700, 650, 4, 2, 2, 2, latitude, longitude, int(index % 3 == 0))).lastrowid
        db.execute('INSERT INTO photos(listing_id,url,position) SELECT ?,url,position FROM photos WHERE listing_id=?', (lid, source['id']))
        db.execute('INSERT INTO listing_amenities SELECT ?,amenity_id FROM listing_amenities WHERE listing_id=?', (lid, source['id']))
        db.execute('INSERT INTO reviews(listing_id,user_id,rating,comment) VALUES(?,5,5,?)', (lid, 'A comfortable base for exploring the area. We loved the relaxed mornings.'))
    db.execute("INSERT INTO demo_content_versions VALUES('catalogue-v4')")
