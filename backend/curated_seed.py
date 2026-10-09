"""Versioned, deterministic demo marketplace content.

The earlier catalogue expansion made hundreds of rows by copying a small set of
templates. This curated set replaces those seeded rows in discovery while
retaining their database records for existing reservation history.
"""

from datetime import timedelta
from itertools import combinations

from .booking_rules import booking_today


# Each tuple has a hand-written name, distinct destination, price, fixed Unsplash
# cover and a short scene description. The coordinates are approximate demo pins.
HOMES = [
    ("Cliffside Villa above Vagator", "Vagator, Goa", "India", "Villa", "Beachfront", 15800, "photo-1613490493576-7fde63acd811", 15.6002, 73.7355, "A shaded laterite terrace opens toward the Arabian Sea, with a plunge pool tucked behind palms."),
    ("Quiet Cedar Cabin in Old Manali", "Old Manali, Himachal Pradesh", "India", "Cabin", "Cabins", 6850, "photo-1449158743715-0a90ebb6d2d8", 32.2574, 77.1741, "Wake to cedar-scented air, then warm up by the wood stove after a walk beside the Beas."),
    ("Pink City Courtyard Haveli", "Brahmpuri, Jaipur, Rajasthan", "India", "Heritage home", "Design", 9400, "photo-1682414181845-a725f154a14a", 26.9298, 75.8302, "A restored fresco courtyard brings old Jaipur craft into a quiet, light-filled private stay."),
    ("Glass Cottage over the Tea Hills", "Coonoor, Tamil Nadu", "India", "Cottage", "Amazing views", 11200, "photo-1510798831971-661eb04b3739", 11.3510, 76.7950, "Tall windows frame tea gardens and Nilgiri clouds from a small deck made for slow mornings."),
    ("Lake-facing Heritage Suite", "Ambamata, Udaipur, Rajasthan", "India", "Heritage home", "Lakefront", 12600, "photo-1600607687920-4e2a09cf159d", 24.5881, 73.6764, "An arched sitting room looks over the lake, while a private balcony catches the evening light."),
    ("Forest A-frame outside Rishikesh", "Shivpuri near Rishikesh, Uttarakhand", "India", "Cabin", "Amazing views", 7900, "photo-1518780664697-55e3ad937233", 30.1034, 78.3247, "A-frame windows face sal forest; the walking path to the river starts just beyond the garden."),
    ("Sea Breeze House in South Goa", "Benaulim, Goa", "India", "Bungalow", "Beachfront", 8700, "photo-1499793983690-e29da59ef1c2", 15.2524, 73.9282, "This whitewashed bungalow has an outdoor shower, a hammock porch and an easy beach walk."),
    ("Minimal Loft near Bandra", "Pali Hill, Mumbai, Maharashtra", "India", "Loft", "Design", 10300, "photo-1522708323590-d24dbb6b0267", 19.0634, 72.8295, "A compact, carefully planned loft pairs warm oak joinery with a desk and a quiet courtyard outlook."),
    ("Stone Cottage among the Pines", "Mashobra, Himachal Pradesh", "India", "Cottage", "Countryside", 7600, "photo-1470770841072-f978cf4d019e", 31.1166, 77.2473, "Thick stone walls and a covered veranda make this hillside cottage feel snug in every season."),
    ("Aravalli House with a Rooftop", "Badi Lake Road, Udaipur, Rajasthan", "India", "Villa", "Amazing views", 14300, "photo-1600210492486-724fe5c67fb0", 24.6301, 73.6507, "A private rooftop gives wide Aravalli views, while the shaded courtyard stays cool through the day."),
    ("Fresco Room in Mandawa", "Ward 8, Mandawa, Rajasthan", "India", "Heritage home", "Design", 6200, "photo-1511818966892-d7d671e672a2", 28.0559, 75.1480, "Stay among hand-painted Shekhawati details in a family-restored haveli with a quiet inner court."),
    ("Coconut Grove Bungalow", "Awas, Alibaug, Maharashtra", "India", "Bungalow", "Tropical", 11900, "photo-1564013799919-ab600027ffc6", 18.6414, 72.8722, "A long garden path leads to a bright bungalow with a shaded dining pavilion and a small pool."),
    ("Old Delhi Rooftop Studio", "Hauz Khas Village, Delhi", "India", "Studio", "Design", 5650, "photo-1493809842364-78817add7ffb", 28.5546, 77.1947, "A private terrace sits above the lane, with a compact kitchen and a view of the old fort walls."),
    ("Coffee Blossom Farmstay", "Madikeri, Coorg, Karnataka", "India", "Farmhouse", "Countryside", 8100, "photo-1600585154340-be6161a56a0c", 12.4244, 75.7382, "The cottage is wrapped by coffee and pepper vines, and the host serves fruit from the orchard."),
    ("Blue Door Hideaway in Ooty", "Fern Hill, Ooty, Tamil Nadu", "India", "Cottage", "Cabins", 7350, "photo-1505693416388-ac5ce068fe85", 11.3948, 76.7041, "A blue door opens onto a sunny reading room, with eucalyptus trails a short walk away."),
    ("Tea Terrace at Munnar", "Pallivasal, Munnar, Kerala", "India", "Cottage", "Amazing views", 9800, "photo-1600566753086-00f18fb6b3ea", 10.0737, 77.0586, "A breakfast deck looks across layered tea slopes, and a fireplace makes misty evenings comfortable."),
    ("Backwater Houseboat in Kumarakom", "Kavanattinkara, Kumarakom, Kerala", "India", "Houseboat", "Lakefront", 15400, "photo-1540541338287-41700207dee6", 9.6175, 76.4301, "A two-bedroom boat glides through quiet canals with a cook preparing a changing Kerala menu."),
    ("French Quarter Balcony Flat", "White Town, Pondicherry, Puducherry", "India", "Apartment", "Design", 6800, "photo-1502672260266-1c1ef2d93688", 11.9338, 79.8330, "Pastel shutters open to a leafy street; cafés and the promenade are both close on foot."),
    ("Lonavala Pool House", "Tungarli, Lonavala, Maharashtra", "India", "Villa", "Amazing pools", 17600, "photo-1613977257592-4871e5fcd7c4", 18.7546, 73.4062, "A private pool, barbecue deck and monsoon valley view make this an easy group escape."),
    ("Shikara View Garden House", "Nishat, Srinagar, Kashmir", "India", "House", "Lakefront", 13200, "photo-1501785888041-af3ef285b470", 34.1294, 74.8837, "The flower garden opens toward Dal Lake, with a covered sitting room for crisp mornings."),
    ("Leh Stone Chalet", "Changspa, Leh, Ladakh", "India", "Chalet", "Amazing views", 8900, "photo-1464822759023-fed622ff2c3b", 34.1718, 77.5842, "A thick-walled chalet keeps the high-desert chill out and gives a clear view of the Stok range."),
    ("Garden Bungalow in Indiranagar", "Indiranagar, Bengaluru, Karnataka", "India", "Bungalow", "Countryside", 7200, "photo-1512917774080-9991f1c4c750", 12.9784, 77.6408, "A leafy private garden and a generous worktable make this bungalow a calm city base."),
    ("Skyline Penthouse in Jubilee Hills", "Jubilee Hills, Hyderabad, Telangana", "India", "Penthouse", "Design", 16800, "photo-1513584684374-8bab748fbf90", 17.4326, 78.4071, "Floor-to-ceiling windows open onto a broad skyline, with a dining balcony for long dinners."),
    ("Cedar Veranda in Shimla", "Chhota Shimla, Himachal Pradesh", "India", "Cabin", "Cabins", 7800, "photo-1449844908441-8829872d2607", 31.1048, 77.1734, "A cedar veranda overlooks the valley and a short woodland trail begins at the lane's end."),
    ("Orchard Farmhouse in Dehradun", "Rajpur Road, Dehradun, Uttarakhand", "India", "Farmhouse", "Countryside", 9100, "photo-1507089947368-19c1da9775ae", 30.3872, 78.0746, "Fruit trees surround the farmhouse, where a sunroom and outdoor table make family meals easy."),
    ("Glass Residence in Gurugram", "Sector 56, Gurugram, Haryana", "India", "Apartment", "Design", 11100, "photo-1600047509807-ba8f99d2cdde", 28.4257, 77.1025, "A bright high-rise apartment has blackout curtains, a fully equipped kitchen and a quiet study nook."),
    ("Hawa Mahal Lane Studio", "Badi Chaupar, Jaipur, Rajasthan", "India", "Studio", "Design", 4950, "photo-1600566753190-17f0baa2a6c3", 26.9239, 75.8267, "A petite studio with hand-blocked textiles sits within an easy walk of Jaipur's old bazaars."),
    ("Paris Rooftop Reading Flat", "Canal Saint-Martin, Paris", "France", "Apartment", "Design", 18900, "photo-1630699144886-d6d025f5d0f1", 48.8720, 2.3640, "A sloped-ceiling flat has a sunny roof terrace, shelves of novels and a market around the corner."),
    ("Trastevere Courtyard Loft", "Trastevere, Rome", "Italy", "Loft", "Design", 17300, "photo-1505691938895-1758d7feb511", 41.8897, 12.4692, "An old stone courtyard leads to a renovated loft with a long dining table and a walk-in shower."),
    ("Mews House near Regent's Canal", "Islington, London", "United Kingdom", "House", "Design", 21400, "photo-1600210492493-0946911123ea", 51.5402, -0.1024, "A tucked-away mews home pairs exposed brick with a small planted patio beside the canal path."),
    ("Quiet Compact Stay in Yanaka", "Yanaka, Tokyo", "Japan", "Tiny home", "Design", 12850, "photo-1600047509782-20d39509f26d", 35.7273, 139.7653, "A clever two-level stay uses warm hinoki wood and places neighborhood bakeries within a few minutes."),
    ("Marina View Apartment in Dubai", "Dubai Marina, Dubai", "United Arab Emirates", "Apartment", "Amazing views", 19800, "photo-1600121848594-d8644e57abab", 25.0805, 55.1403, "A shaded balcony faces the marina, with a pool and tram stop available in the building."),
    ("Bamboo Canopy Villa in Ubud", "Sayan, Ubud, Bali", "Indonesia", "Villa", "Tropical", 14900, "photo-1571896349842-33c89424de2d", -8.5069, 115.2625, "A bamboo pavilion sits above a green ravine, with an open-air bath and a private garden."),
    ("Phuket Sea-view Deck House", "Kata Noi, Phuket", "Thailand", "Villa", "Beachfront", 18400, "photo-1507525428034-b723cf961d3e", 7.7985, 98.2984, "The covered deck catches sea breezes all day, and a quiet cove is visible just below the house."),
    ("Valley Courtyard Home in Kathmandu", "Patan, Kathmandu", "Nepal", "Heritage home", "Design", 6400, "photo-1516483638261-f4dbaf036963", 27.6728, 85.3250, "Carved timber windows frame a private brick courtyard in the old city of Patan."),
    ("Pokhara Lakeside Cottage", "Lakeside, Pokhara", "Nepal", "Cottage", "Lakefront", 5300, "photo-1500375592092-40eb2168fd21", 28.2096, 83.9591, "A small garden cottage is set back from the lakeside road with a view toward the Annapurna range."),
    ("Galle Fort Courtyard House", "Galle Fort, Galle", "Sri Lanka", "Heritage home", "Design", 10100, "photo-1518837695005-2083093ee35b", 6.0270, 80.2168, "A quiet inner courtyard and wide shutters keep this restored fort house airy through the afternoon."),
    ("Ella Tea Bungalow", "Kithal Ella, Ella", "Sri Lanka", "Bungalow", "Countryside", 9150, "photo-1494526585095-c41746248156", 6.8667, 81.0466, "A hillside bungalow faces tea fields and the railway valley, with a covered porch for the rain."),
    ("Lanna Courtyard Stay in Chiang Mai", "Old City, Chiang Mai", "Thailand", "House", "Tropical", 6900, "photo-1560185008-b033106af5c3", 18.7883, 98.9853, "A teak-lined courtyard home has a shaded plunge pool and a small altar room kept by the family."),
    ("Riverside Loft in Bangkok", "Charoen Krung, Bangkok", "Thailand", "Loft", "Design", 10250, "photo-1484154218962-a197022b5858", 13.7191, 100.5140, "A converted riverside warehouse loft combines tall steel windows with a generous kitchen island."),
    ("Cloudline Chalet in Mussoorie", "Landour, Mussoorie, Uttarakhand", "India", "Chalet", "Amazing views", 13700, "photo-1500534623283-312aade485b7", 30.4598, 78.0750, "A slate-roof chalet looks over the Doon valley and keeps a sheltered firepit on the lawn."),
    ("Rainforest Cabin in Shillong", "Mawpat, Shillong, Meghalaya", "India", "Cabin", "Countryside", 6500, "photo-1473448912268-2022ce9509d8", 25.5788, 91.8933, "A cedar cabin sits beside a fern-lined path with a covered porch for listening to the rain."),
    ("Darjeeling Tea Estate Cottage", "Happy Valley, Darjeeling, West Bengal", "India", "Cottage", "Amazing views", 7100, "photo-1500530855697-b586d89ba3ee", 27.0360, 88.2530, "Tea rows roll toward the cottage, and on clear mornings Kanchenjunga appears beyond the roof."),
    ("Puri Dune House", "Baliapanda, Puri, Odisha", "India", "House", "Beachfront", 8250, "photo-1519046904884-53103b34b206", 19.7824, 85.7950, "A low dune garden buffers the sea wind, with an outdoor rinse area for sandy afternoons."),
    ("Waterside Loft in Fort Kochi", "Mattancherry, Kochi, Kerala", "India", "Loft", "Design", 8200, "photo-1554995207-c18c203602cb", 9.9570, 76.2590, "An airy upstairs loft overlooks a quiet lane of spice shops and the ferry landing."),
    ("Marine Drive Corner Apartment", "Churchgate, Mumbai, Maharashtra", "India", "Apartment", "Amazing views", 22400, "photo-1556912172-45b7abe8b7e1", 18.9352, 72.8264, "A generous corner living room faces the sea promenade, with a stocked kitchen for longer stays."),
    ("Jaisalmer Dune-side Haveli", "Malka Pol, Jaisalmer, Rajasthan", "India", "Heritage home", "Design", 11600, "photo-1523217582562-09d0def993a6", 26.9124, 70.9120, "Golden stonework surrounds a cool inner court, and the ramparts are a short evening walk away."),
    ("Garden House by the Dal", "Rainawari, Srinagar, Kashmir", "India", "House", "Lakefront", 10800, "photo-1600607687939-ce8a6c25118c", 34.0837, 74.8790, "A walled garden, carved screens and a heated sitting room make a peaceful base beside the lake."),
]


HOST_NAMES = [
    "Aarav Mehta", "Meera Nair", "Kabir Sethi", "Ishita Rao", "Rohan Bhatia", "Ananya Iyer", "Arjun Kapur", "Neha Menon",
    "Vikram Shah", "Diya Patel", "Aditya Bose", "Sara D'Souza", "Rahul Khanna", "Tara Anand", "Karan Gill", "Maya Fernandes",
    "Naina Kapoor", "Dev Malhotra", "Pia Mukherjee", "Zoya Merchant", "Farhan Ali", "Samar Khurana", "Rhea Desai", "Vivan Sen",
    "Aditi Sood", "Nikhil Varma", "Leela George", "Harsh Vora", "Noor Qadri", "Keshav Pillai", "Ira Chawla", "Danish Mirza",
    "Anika Roy", "Om Prakash", "Shanaya Bedi", "Rehan Dutta", "Amara Joseph", "Veer Ahuja", "Saloni Wadhwa", "Yash Bansal",
    "Ishan Khatri", "Amita Lal", "Sana Qureshi", "Manav Gokhale", "Sonia Mathur", "Jayant Rao", "Kavya Iyer", "Naveen Thomas",
    "Mira Ghosh", "Anil Reddy", "Saira Siddiqui", "Parth Khanna", "Ayesha Baig", "Reva Narang", "Devika Das", "Mihir Luthra",
    "Sonal Ahuja", "Akash Bhalla", "Prisha Naik", "Haroon Sheikh", "Kriti Batra", "Nandita Bose", "Zain Ansari", "Raghav Chopra",
    "Nupur Bhandari", "Aarohi Suri", "Dilan Perera", "Rizwan Mir", "Tenzin Dorje", "Pema Sherpa", "Kiran Subramanian", "Aparna Menon",
    "Sahil Puri", "Laila Fernandes", "Mahi Saldanha", "Nirav Parikh", "Shreya Kulkarni", "Kunal Oberoi", "Amina Khan", "Ritwik Das",
    "Bina Mathew", "Uday Venkatesh", "Gauri Salvi", "Tushar Jindal", "Jaya Krishnan", "Ravinder Gill", "Madhavi Shetty", "Arun Sinha",
    "Rafiq Contractor", "Jhanvi Bhasin",
]

HOME_RATINGS = [4.52, 4.53, 4.54, 4.55, 4.56, 4.57, 4.58, 4.59, 4.60, 4.61, 4.62, 4.63, 4.64, 4.65, 4.66, 4.67, 4.68, 4.69, 4.70, 4.71, 4.72, 4.73, 4.74, 4.75, 4.76, 4.77, 4.78, 4.79, 4.80, 4.81, 4.82, 4.83, 4.84, 4.85, 4.86, 4.87, 4.88, 4.89, 4.90, 4.91, 4.92, 4.93, 4.94, 4.95, 4.96, 4.97, 4.98, 4.99]
HOME_REVIEW_COUNTS = [103, 117, 129, 142, 156, 169, 183, 197, 211, 226, 241, 257, 273, 289, 307, 326, 347, 369, 392, 416, 441, 467, 493, 512, 101, 109, 121, 134, 148, 161, 175, 189, 203, 218, 233, 249, 265, 281, 299, 318, 339, 361, 384, 408, 433, 459, 485, 508]

EXPERIENCES = [
    ("Old Delhi Street-food Walk with Rafi", "Chandni Chowk, Delhi", "India", "Food & drink", 1850, 150, 8, "person", "photo-1556911220-bff31c812dba", "Taste crisp jalebi, seasonal fruit and family-run kebabs while Rafi shares the market's food history."),
    ("Sunrise Ridge Hike above Manali", "Vashisht, Manali", "India", "Adventure", 2450, 210, 8, "person", "photo-1551632811-561732d1e306", "Climb a quiet ridge before the valley wakes, with tea and a packed breakfast at the viewpoint."),
    ("Goan Seafood Cook-along at Home", "Fontainhas, Panaji, Goa", "India", "Food & drink", 3200, 180, 6, "person", "photo-1733959541069-1a289a05a59f", "Shop for the day's catch, then learn a family masala and cook lunch in a Portuguese-era kitchen."),
    ("Jaipur Block-printing Studio Session", "Sanganer, Jaipur", "India", "Art & creativity", 2100, 150, 8, "person", "photo-1493106641515-6b5631de4bb9", "Carve a small motif and print a cotton scarf with a fourth-generation artisan in Sanganer."),
    ("Mumbai Night-photo Walk", "Kala Ghoda, Mumbai", "India", "Photography", 2800, 120, 5, "person", "photo-1452587925148-ce544e77e70d", "Practice low-light street photography through the old lanes and waterfront, with personal camera tips."),
    ("Udaipur Heritage Cycle Loop", "Gangaur Ghat, Udaipur", "India", "Culture & history", 1950, 180, 8, "person", "photo-1524492412937-b28074a5d7da", "Ride the lake edge and lesser-known havelis with a local historian, pausing for chai by the ghats."),
    ("Kerala Backwater Canoe at First Light", "Kainakary, Alappuzha", "India", "Nature & outdoors", 3600, 180, 6, "person", "photo-1472746729193-36ad213ac4a5", "Paddle narrow canals as fishermen set out, then share a simple breakfast on a shaded bank."),
    ("Bali Temple and Village Morning", "Ubud, Bali", "Indonesia", "Culture & history", 4100, 240, 8, "person", "photo-1750850234201-f7f2533e3043", "Visit a family temple with a village guide, learn the offering ritual and finish among rice terraces."),
    ("Fresh Pasta in a Roman Kitchen", "Trastevere, Rome", "Italy", "Food & drink", 5200, 180, 6, "person", "photo-1551183053-bf91a1d81141", "Roll two pasta shapes by hand and sit down to the meal with a Roman home cook."),
    ("Hidden Paris Through a Film Camera", "Le Marais, Paris", "France", "Photography", 4600, 150, 6, "person", "photo-1494438639946-1ebd1d20bf85", "Frame quiet courtyards and small shopfronts on a relaxed analog-photo walk through the Marais."),
    ("Kangra Valley Tea and Tasting", "Palampur, Himachal Pradesh", "India", "Food & drink", 1650, 120, 10, "person", "photo-1517457373958-b7bdd4587205", "Walk the tea rows with a grower and compare three local harvests over fresh parathas."),
    ("Rann of Kutch Stargazing Camp", "Dhordo, Gujarat", "India", "Nature & outdoors", 2900, 150, 12, "person", "photo-1470252649378-9c29740c9fa8", "Read the desert sky with a local naturalist and hear how the salt flats change between seasons."),
    ("Kochi Spice-lane History Walk", "Mattancherry, Kochi", "India", "History", 1750, 135, 10, "person", "photo-1708668984945-309e431c61f0", "Trace a spice route through warehouses and synagogues with stories from three generations of traders."),
    ("A Potter's Wheel in Khurja", "Khurja, Uttar Pradesh", "India", "Art & creativity", 2250, 150, 6, "person", "photo-1513364776144-60967b0f800f", "Throw a small cup at a family pottery studio and decorate it with a blue-glaze pattern."),
    ("Coastal Kayak around Nerul Creek", "Nerul, Goa", "India", "Sports", 3100, 120, 6, "person", "photo-1621002478474-8068f2a7d47d", "Follow mangrove channels by kayak with a safety-trained guide and a short beach break."),
    ("Old Lucknow Awadhi Supper", "Chowk, Lucknow", "India", "Food & drink", 3400, 180, 8, "person", "photo-1535898331935-2d274aff0fbc", "Meet a home cook for a slow supper of seasonal Awadhi dishes and stories behind each recipe."),
    ("Kumaon Forest-bird Morning", "Pangot, Uttarakhand", "India", "Nature & outdoors", 2300, 180, 8, "person", "photo-1657739749545-6bed5be48455", "Look for Himalayan birdlife on an easy forest walk with binoculars and a field notebook provided."),
    ("A Raga Listening Room in Varanasi", "Assi Ghat, Varanasi", "India", "Music", 2700, 120, 10, "person", "photo-1514525253161-7a46d19cd819", "Listen to a short live raga recital and learn how the time of day shapes its mood."),
    ("Dharamshala Tibetan Bread Workshop", "McLeod Ganj, Dharamshala", "India", "Food & drink", 2050, 120, 8, "person", "photo-1704428381339-3b3087053b3a", "Make tingmo and warm butter tea with a local baker in a small neighborhood kitchen."),
    ("Srinagar Old-city Woodcarving Visit", "Zaina Kadal, Srinagar", "India", "Art & creativity", 2500, 150, 6, "person", "photo-1579783902614-a3fb3927b6a5", "Watch a master carve walnut wood and try a small practice motif under careful guidance."),
    ("Pondicherry French Quarter Sketch Walk", "White Town, Puducherry", "India", "Art & creativity", 2150, 150, 8, "person", "photo-1689760661369-8d37f5ad7517", "Sketch pastel façades and bougainvillea balconies with a designer who knows the quiet lanes."),
    ("Night Market Beats in Bangkok", "Talat Noi, Bangkok", "Thailand", "Nightlife", 3050, 180, 8, "person", "photo-1511379938547-c1f69419868d", "Explore small live-music rooms and late-night snacks with a Bangkok-based radio host."),
    ("Alpine Flower Trail near Leh", "Saboo, Leh, Ladakh", "India", "Adventure", 3250, 240, 6, "person", "photo-1691215168429-9e4eed9c43a8", "Take an acclimatization-friendly walk past high-altitude gardens with a local mountain guide."),
    ("Rooftop Yoga at Dawn in Rishikesh", "Tapovan, Rishikesh", "India", "Wellness", 1600, 75, 10, "person", "photo-1544367567-0f2fcb009e0b", "Start with breathwork and a gentle flow as the first light moves over the Ganges valley."),
]

SERVICES = [
    ("Private Goan Dinner by Chef Riya", "Assagao, Goa", "India", "Private chefs", 12600, 180, 8, "group", "photo-1556761175-b413da4baf72", "A seasonal coastal menu is cooked in your villa kitchen and served family-style on the terrace."),
    ("Sunset Couple Photography in Udaipur", "Ambamata, Udaipur", "India", "Photography", 7800, 90, 2, "group", "photo-1519741497674-611481863552", "A relaxed golden-hour portrait session around the lake, with a private gallery of edited images."),
    ("In-villa Deep-tissue Massage", "Candolim, Goa", "India", "Massage", 4200, 90, 2, "person", "photo-1540555700478-4be289fbecef", "A licensed therapist brings a table, fresh linens and a pressure plan tailored to each guest."),
    ("Morning Yoga at Your Stay with Arjun", "Vagator, Goa", "India", "Yoga", 2900, 60, 6, "person", "photo-1506126613408-eca07ce68773", "A private instructor adjusts a calm mobility and breath session to the group's experience."),
    ("Personal Fitness Session with Neha", "Bandra, Mumbai", "India", "Personal training", 3600, 60, 4, "person", "photo-1517836357463-d25dfeac3438", "A bodyweight or strength session uses the equipment available at your accommodation."),
    ("Family Holiday Portraits in Jaipur", "Civil Lines, Jaipur", "India", "Photography", 6500, 75, 8, "group", "photo-1500648767791-00dcc994a43e", "A patient family photographer captures candid portraits and delivers a small edited collection."),
    ("Private Heritage Guide in Jaipur", "Pink City, Jaipur", "India", "Private guides", 5200, 180, 6, "group", "photo-1534528741775-53994a69daeb", "A licensed guide builds an unhurried route around your interests, with entry timing advice."),
    ("Kerala Brunch Spread at Your Stay", "Fort Kochi, Kochi", "India", "Catering", 8400, 150, 10, "group", "photo-1715985160053-d339e8b6eb94", "A home caterer prepares appam, stew and seasonal sides in your kitchen and leaves it ready to serve."),
    ("Wedding-ready Hair Styling in Delhi", "Hauz Khas, Delhi", "India", "Hair styling", 3100, 75, 2, "person", "photo-1562322140-8baeececf3df", "A traveling stylist brings a compact kit and creates a polished look after a short consultation."),
    ("Natural Makeup for a Special Evening", "Indiranagar, Bengaluru", "India", "Beauty", 3900, 90, 2, "person", "photo-1524504388940-b1c1722653e1", "A makeup artist uses a skin-first routine and adapts the finish to your event and preferences."),
    ("Aromatherapy Reset at Your Apartment", "Jubilee Hills, Hyderabad", "India", "Spa & wellness", 4700, 90, 2, "person", "photo-1519014816548-bf5fe059798b", "A calming in-home ritual combines warm towels, aromatherapy and a gentle guided wind-down."),
    ("In-home Sushi Dinner for Four", "Bandra West, Mumbai", "India", "Private chefs", 14800, 210, 4, "group", "photo-1556911220-e15b29be8c8f", "A sushi chef brings the day's ingredients and prepares a tasting menu at your dining table."),
    ("Pet-friendly Trail Walk in Coorg", "Madikeri, Coorg", "India", "Private guides", 2800, 120, 6, "group", "photo-1661574069725-cb55d93ca682", "A local naturalist chooses a shaded, dog-friendly route and brings water and basic trail supplies."),
    ("At-home Nail Art for a Celebration", "White Town, Puducherry", "India", "Beauty", 2600, 90, 2, "person", "photo-1522335789203-aabd1fc54bc9", "A nail artist brings a clean portable kit and creates a design from your saved inspiration."),
    ("Sound-bath Wind-down in Rishikesh", "Tapovan, Rishikesh", "India", "Spa & wellness", 3300, 60, 8, "group", "photo-1518611012118-696072aa579a", "A facilitator brings bowls and mats for a gentle evening sound session in your living room."),
    ("Villa Barbecue Setup in Alibaug", "Awas, Alibaug", "India", "Catering", 9600, 150, 10, "group", "photo-1725640534065-70510eefe989", "A cook handles marinades, sides and the grill setup, then leaves the outdoor table ready for dinner."),
    ("Bali Villa Flower and Fruit Setup", "Sayan, Ubud", "Indonesia", "Spa & wellness", 5600, 60, 4, "group", "photo-1497366754035-f200968a6e72", "A local stylist arranges tropical flowers, fruit and a small welcome tray before check-in."),
    ("London Mews Home Deep Clean", "Islington, London", "United Kingdom", "Housekeeping", 7200, 180, 4, "group", "photo-1521791136064-7986c2920216", "A vetted two-person team refreshes the kitchen, bathrooms and linens during a longer stay."),
    ("Private Airport Transfer in Leh", "Leh Airport, Ladakh", "India", "Private guides", 3400, 60, 4, "group", "photo-1507003211169-0a1dd7228f2d", "A local driver meets your flight, tracks delays and makes a gentle acclimatization stop if requested."),
    ("Custom Flower Bouquet in Paris", "Le Marais, Paris", "France", "Catering", 5800, 45, 2, "group", "photo-1531058020387-3be344556be6", "A neighborhood florist delivers a seasonal bouquet arranged around your preferred colors and vase."),
]


AMENITY_POOL = ["Pool", "Ocean view", "Mountain view", "Free parking", "Air conditioning", "Heating", "Workspace", "Washer", "Garden", "Fireplace", "Hot tub", "Balcony", "BBQ", "EV charger", "Breakfast", "Pet friendly"]
HOME_AMENITY_PAIRS = list(combinations(AMENITY_POOL, 2))[:48]
HOME_RATING_COMMENTS = [
    "The room was beautifully prepared and the host made arrival easy.",
    "We loved the location and found thoughtful touches in every room.",
    "A restful stay with a comfortable bed and clear local recommendations.",
    "The photos matched the space and the neighborhood was a delight to explore.",
    "The kitchen was well equipped and the view made breakfast memorable.",
    "Communication was quick, and the home felt calm after busy days out.",
    "The linens were fresh and the small details made this feel personal.",
    "We would happily return for another weekend in this part of town.",
]
ACTIVITY_REVIEW_COUNTS = [101, 109, 118, 127, 137, 148, 160, 173, 187, 202, 218, 235, 253, 272, 292, 313, 335, 358, 382, 407, 433, 460, 488, 517]
SERVICE_REVIEW_COUNTS = [105, 114, 124, 135, 147, 160, 174, 189, 205, 222, 240, 259, 279, 300, 322, 345, 369, 394, 420, 447]


def _photo(photo_id: str, width: int = 1200) -> str:
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w={width}&q=82"


def _avatar(photo_id: str) -> str:
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=160&h=160&q=80"


def _ensure_hosts(db) -> list[int]:
    for offset, name in enumerate(HOST_NAMES):
        user_id = 100 + offset
        gender = "women" if offset % 2 else "men"
        portrait = offset // 2 + 1
        avatar = f"https://randomuser.me/api/portraits/{gender}/{portrait}.jpg"
        joined_year = 2012 + (offset * 7) % 13
        db.execute(
            "INSERT OR IGNORE INTO users(id,name,role,avatar,joined_year) VALUES(?,?,'host',?,?)",
            (user_id, name, avatar, joined_year),
        )
        db.execute(
            "UPDATE users SET name=?,avatar=?,joined_year=? WHERE id=? AND role='host'",
            (name, avatar, joined_year, user_id),
        )
    for user_id, gender, portrait in ((2, "women", 94), (3, "men", 94), (4, "women", 95)):
        db.execute(
            "UPDATE users SET avatar=? WHERE id=? AND role='host' AND avatar NOT LIKE 'http%'",
            (f"https://randomuser.me/api/portraits/{gender}/{portrait}.jpg", user_id),
        )
    return list(range(100, 100 + len(HOST_NAMES)))


def _add_home_reviews(db, listing_id: int, home_index: int, target: float, count: int) -> None:
    five_star_count = round((target - 4) * count)
    first_day = booking_today()
    rows = []
    for index in range(count):
        rating = 5 if index < five_star_count else 4
        comment = f"{HOME_RATING_COMMENTS[(home_index + index) % len(HOME_RATING_COMMENTS)]} {HOMES[home_index][0]} — visit note {index + 1}."
        rows.append((listing_id, (1, 5, 6)[index % 3], rating, comment, str(first_day - timedelta(days=30 + index))))
    db.executemany(
        "INSERT INTO reviews(listing_id,user_id,rating,comment,created_at) VALUES(?,?,?,?,?)",
        rows,
    )


def _add_activity_reviews(db, activity_id: int, title: str, count: int, base_rating: float) -> None:
    five_star_count = round((base_rating - 4) * count)
    db.executemany(
        "INSERT INTO activity_reviews(activity_id,user_id,rating,comment) VALUES(?,?,?,?)",
        [
            (activity_id, (1, 5, 6)[index % 3], 5 if index < five_star_count else 4,
             f"{title} was thoughtfully run; note {index + 1} from a demo guest.")
            for index in range(count)
        ],
    )


def _legacy_demo_listing_ids(db) -> list[int]:
    """Recognize old generated seed titles without guessing user-created rows."""
    from .seed import HOMES as ORIGINAL_HOMES

    versions = {row[0] for row in db.execute("SELECT version FROM demo_content_versions")}
    base_titles = {row[0] for row in ORIGINAL_HOMES}
    v2_starts = ("The slow living ", "Sunlit ", "The peaceful ", "A little ")
    v3_starts = ("Terrace retreat in ", "Garden hideaway in ", "Sunrise house in ", "Courtyard escape in ",
                 "The reading room in ", "Quiet mornings in ", "The weekend home in ", "Little sanctuary in ")
    v4_starts = ("The sunlit home in ", "A quiet corner in ", "The open-window retreat in ", "Your little getaway in ")
    rows = db.execute("SELECT id,title FROM listings WHERE id<=272 AND deleted=0").fetchall()
    result = []
    for row in rows:
        title = row["title"]
        if row["id"] <= 20 and title in base_titles:
            result.append(row["id"])
        elif "catalogue-v2" in versions and row["id"] <= 44 and title.startswith(v2_starts) and " in " in title:
            result.append(row["id"])
        elif "catalogue-v3" in versions and row["id"] <= 240 and title.startswith(v3_starts) and " · " in title:
            result.append(row["id"])
        elif "catalogue-v4" in versions and row["id"] <= 272 and title.startswith(v4_starts) and " in " in title:
            result.append(row["id"])
    return result


def _seed_homes(db, host_ids: list[int]) -> None:
    # Keep the original seeded catalogue and any linked reservations for history,
    # but remove template-generated demo rows from discovery once only.
    legacy_ids = [listing_id for listing_id in _legacy_demo_listing_ids(db) if listing_id != 1]
    db.executemany("UPDATE listings SET seeded=1,deleted=1 WHERE id=?", [(listing_id,) for listing_id in legacy_ids])
    # Keep the original completed-stay demo home live so its review walkthrough
    # remains reachable, while giving it a non-repeated cover photo.
    db.execute("UPDATE listings SET seeded=1 WHERE id=1")
    db.execute(
        "UPDATE photos SET url=? WHERE listing_id=1 AND position=0 AND url LIKE '%photo-1613977257363-707ba9348227%'",
        (_photo("photo-1616486338812-3dadae4b4ace"),),
    )
    photo_ids = [record[6] for record in HOMES]
    amenity_rows = [("Wifi",), ("Kitchen",), ("Beach access",), ("Lake view",)] + [(name,) for name in AMENITY_POOL]
    db.executemany("INSERT OR IGNORE INTO amenities(name) VALUES(?)", amenity_rows)
    for index, record in enumerate(HOMES):
        title, location, country, property_type, category, price, photo_id, latitude, longitude, story = record
        # The first two curated homes get their own existing demo hosts. Listing
        # 1 keeps its original host so its review walkthrough remains intact.
        host_id = 2 if index == 0 else 3 if index == 1 else host_ids[index - 2]
        bedroom_count = 1 + (index * 3) % 4
        max_guests = min(10, max(6 if property_type == "Cabin" else 1, 2 * bedroom_count + (1 if index % 3 == 0 else 0)))
        cleaning_fee = 550 + ((index * 347) % 1650)
        description = (
            f"{story}\n\n"
            f"This {property_type.lower()} is arranged for up to {max_guests} guests, with a private kitchen, fresh linens and a locally made welcome guide. "
            f"Your host can point you toward favorite places around {location.split(',')[0]}. All listing details and images are illustrative demo content."
        )
        cursor = db.execute(
            """INSERT INTO listings(host_id,title,description,location,country,category,property_type,
            price,cleaning_fee,max_guests,bedrooms,beds,bathrooms,latitude,longitude,superhost,seeded)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
            (host_id, title, description, location, country, category, property_type, price, cleaning_fee,
             max_guests, bedroom_count, bedroom_count + index % 3, max(1, (bedroom_count + 1) // 2),
             latitude, longitude, int(index % 3 != 1)),
        )
        listing_id = cursor.lastrowid
        # The cover is unique. The three supporting gallery frames are selected
        # from nearby property styles and rotate per listing, never one shared array.
        gallery = [photo_id] + [photo_ids[(index + offset) % len(photo_ids)] for offset in (1, 8, 17)]
        db.executemany(
            "INSERT INTO photos(listing_id,url,position) VALUES(?,?,?)",
            [(listing_id, _photo(image), position) for position, image in enumerate(gallery)],
        )
        pair = HOME_AMENITY_PAIRS[index]
        selected = {"Wifi", "Kitchen", *pair}
        if category == "Beachfront":
            selected.add("Beach access")
        elif category == "Lakefront":
            selected.add("Lake view")
        elif category in ("Cabins", "Amazing views"):
            selected.add("Mountain view")
        for name in selected:
            db.execute(
                "INSERT INTO listing_amenities(listing_id,amenity_id) SELECT ?,id FROM amenities WHERE name=?",
                (listing_id, name),
            )
        _add_home_reviews(db, listing_id, index, HOME_RATINGS[index], HOME_REVIEW_COUNTS[index])


def _seed_activities(db, host_ids: list[int]) -> None:
    db.execute("UPDATE activities SET deleted=1 WHERE seeded=1 AND deleted=0")
    for kind, rows, review_counts in (
        ("experiences", EXPERIENCES, ACTIVITY_REVIEW_COUNTS),
        ("services", SERVICES, SERVICE_REVIEW_COUNTS),
    ):
        photo_ids = [row[8] for row in rows]
        for index, record in enumerate(rows):
            title, location, country, category, price, duration, capacity, price_type, primary_photo, story = record
            host_offset = 46 + index if kind == "experiences" else 70 + index
            host_id = host_ids[host_offset]
            setting = "Outdoor" if any(term in category.lower() for term in ("nature", "adventure", "sports", "photography")) else "Indoor"
            service_location = "Provider location" if kind == "experiences" else "At your stay"
            description = f"{story} The small-group format leaves time for questions and personal recommendations from your local host. This is a fictional demo offering."
            included = "Local host guidance\nAll listed materials\nA short neighborhood recommendation list"
            itinerary = f"Meet your host in {location.split(',')[0]}.\n{story}\nWrap up with time for questions and local recommendations."
            requirements = f"Please arrive 10 minutes early for {title}. Share accessibility or dietary needs with the host before the session."
            activity_id = db.execute(
                """INSERT INTO activities(kind,host_id,title,description,location,country,category,price,price_type,
                duration_minutes,capacity,language,setting,service_location,itinerary,included,requirements,seeded)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
                (kind, host_id, title, description, location, country, category, price, price_type, duration,
                 capacity, "English" if index % 3 else "Hindi", setting, service_location,
                 itinerary, included, requirements),
            ).lastrowid
            gallery = [primary_photo, photo_ids[(index + 1) % len(photo_ids)], photo_ids[(index + 4) % len(photo_ids)]]
            db.executemany(
                "INSERT INTO activity_photos(activity_id,url,position) VALUES(?,?,?)",
                [(activity_id, _photo(image), position) for position, image in enumerate(gallery)],
            )
            count = review_counts[index]
            rating = (4.54 + index * 0.02) if kind == "experiences" else (4.55 + index * 0.02)
            _add_activity_reviews(db, activity_id, title, count, rating)
            for offset in range(1, 61):
                day = booking_today() + timedelta(days=offset)
                for start_time in ("09:00", "14:00", "18:00"):
                    db.execute(
                        "INSERT OR IGNORE INTO activity_slots(activity_id,day,start_time,capacity) VALUES(?,?,?,?)",
                        (activity_id, str(day), start_time, capacity),
                    )


def _upgrade_curated_marketplace_v2(db, host_ids: list[int]) -> None:
    """Refresh seed-owned primary photos and assign one distinct host per offer."""
    for index, record in enumerate(HOMES):
        title, _, _, _, _, _, photo_id, *_ = record
        row = db.execute(
            "SELECT id FROM listings WHERE title=? AND seeded=1 AND deleted=0 ORDER BY id DESC LIMIT 1",
            (title,),
        ).fetchone()
        if not row:
            continue
        host_id = 2 if index == 0 else 3 if index == 1 else host_ids[index - 2]
        db.execute("UPDATE listings SET host_id=? WHERE id=?", (host_id, row[0]))
        db.execute(
            "UPDATE photos SET url=? WHERE listing_id=? AND position=0",
            (_photo(photo_id), row[0]),
        )

    for kind, rows, host_offset in (
        ("experiences", EXPERIENCES, 46),
        ("services", SERVICES, 70),
    ):
        for index, record in enumerate(rows):
            title, _, _, _, _, _, _, _, photo_id, _ = record
            row = db.execute(
                "SELECT id FROM activities WHERE kind=? AND title=? AND seeded=1 AND deleted=0 ORDER BY id DESC LIMIT 1",
                (kind, title),
            ).fetchone()
            if not row:
                continue
            db.execute(
                "UPDATE activities SET host_id=? WHERE id=?",
                (host_ids[host_offset + index], row[0]),
            )
            db.execute(
                "UPDATE activity_photos SET url=? WHERE activity_id=? AND position=0",
                (_photo(photo_id), row[0]),
            )


def seed_curated_marketplace(db) -> None:
    """Install the quality demo catalog once; never reset user-created records."""
    db.execute("CREATE TABLE IF NOT EXISTS demo_content_versions (version TEXT PRIMARY KEY)")
    if db.execute("SELECT 1 FROM demo_content_versions WHERE version='curated-marketplace-v3'").fetchone():
        return
    assert len(HOST_NAMES) == 90 and len(set(HOST_NAMES)) == len(HOST_NAMES)
    assert len(HOMES) >= 48 and len({row[0] for row in HOMES}) == len(HOMES)
    assert len({row[6] for row in HOMES}) == len(HOMES)
    assert len({row[1] for row in HOMES}) == len(HOMES)
    assert len({row[5] for row in HOMES}) == len(HOMES)
    assert len(set(HOME_RATINGS)) == len(HOMES) == len(set(HOME_REVIEW_COUNTS))
    assert len({row[0] for row in EXPERIENCES}) == len(EXPERIENCES)
    assert len({row[8] for row in EXPERIENCES}) == len(EXPERIENCES)
    assert len({row[4] for row in EXPERIENCES}) == len(EXPERIENCES)
    assert len({row[0] for row in SERVICES}) == len(SERVICES)
    assert len({row[8] for row in SERVICES}) == len(SERVICES)
    assert len({row[4] for row in SERVICES}) == len(SERVICES)
    all_cover_ids = [row[6] for row in HOMES] + [row[8] for row in EXPERIENCES] + [row[8] for row in SERVICES]
    assert len(all_cover_ids) == len(set(all_cover_ids))
    host_ids = _ensure_hosts(db)
    if db.execute("SELECT 1 FROM demo_content_versions WHERE version='curated-marketplace-v1'").fetchone():
        _upgrade_curated_marketplace_v2(db, host_ids)
        db.execute("INSERT INTO demo_content_versions(version) VALUES('curated-marketplace-v3')")
        return
    _seed_homes(db, host_ids)
    _seed_activities(db, host_ids)
    db.execute("INSERT INTO demo_content_versions(version) VALUES('curated-marketplace-v1')")
    _upgrade_curated_marketplace_v2(db, host_ids)
    db.execute("INSERT INTO demo_content_versions(version) VALUES('curated-marketplace-v3')")
