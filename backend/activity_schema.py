"""Additive schema for shared experiences and services; no home tables changed."""

STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS activities (
 id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL CHECK(kind IN ('experiences','services')),
 host_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, description TEXT NOT NULL,
 location TEXT NOT NULL, country TEXT NOT NULL, category TEXT NOT NULL,
 price INTEGER NOT NULL CHECK(typeof(price)='integer' AND price>0),
 price_type TEXT NOT NULL CHECK(price_type IN ('person','group')),
 duration_minutes INTEGER NOT NULL CHECK(duration_minutes BETWEEN 30 AND 480),
 capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 30), language TEXT NOT NULL,
 setting TEXT NOT NULL CHECK(setting IN ('Indoor','Outdoor','Either')),
 service_location TEXT NOT NULL CHECK(service_location IN ('At your stay','Provider location','Either')),
 itinerary TEXT NOT NULL, included TEXT NOT NULL, requirements TEXT NOT NULL,
 deleted INTEGER NOT NULL DEFAULT 0, seeded INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS activity_photos (
 id INTEGER PRIMARY KEY, activity_id INTEGER NOT NULL REFERENCES activities(id),
 url TEXT NOT NULL, position INTEGER NOT NULL, UNIQUE(activity_id,position))""",
    """CREATE TABLE IF NOT EXISTS activity_slots (
 id INTEGER PRIMARY KEY AUTOINCREMENT, activity_id INTEGER NOT NULL REFERENCES activities(id),
 day TEXT NOT NULL CHECK(length(day)=10 AND date(day,'+0 days')=day),
 start_time TEXT NOT NULL CHECK(length(start_time)=5 AND start_time GLOB '[0-2][0-9]:[0-5][0-9]' AND start_time<'24:00'),
 capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 30), active INTEGER NOT NULL DEFAULT 1,
 UNIQUE(activity_id,day,start_time))""",
    """CREATE TABLE IF NOT EXISTS activity_bookings (
 id INTEGER PRIMARY KEY AUTOINCREMENT, activity_id INTEGER NOT NULL REFERENCES activities(id),
 slot_id INTEGER NOT NULL REFERENCES activity_slots(id), user_id INTEGER NOT NULL REFERENCES users(id),
 host_id INTEGER NOT NULL REFERENCES users(id), kind TEXT NOT NULL CHECK(kind IN ('experiences','services')),
 day TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL CHECK(end_time>start_time),
 people INTEGER NOT NULL CHECK(typeof(people)='integer' AND people BETWEEN 1 AND 30),
 unit_price INTEGER NOT NULL CHECK(typeof(unit_price)='integer' AND unit_price>0),
 price_type TEXT NOT NULL CHECK(price_type IN ('person','group')),
 subtotal INTEGER NOT NULL, service_fee INTEGER NOT NULL, total INTEGER NOT NULL,
 status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled')),
 idempotency_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id,idempotency_key),
 CHECK(subtotal=unit_price*CASE WHEN price_type='person' THEN people ELSE 1 END),
 CHECK(service_fee=CAST((subtotal*10+50)/100 AS INTEGER)), CHECK(total=subtotal+service_fee))""",
    """CREATE INDEX IF NOT EXISTS activity_provider_time ON activity_bookings(host_id,day,status,start_time,end_time)""",
    """CREATE INDEX IF NOT EXISTS activity_booking_slot ON activity_bookings(slot_id,status)""",
    """CREATE INDEX IF NOT EXISTS activity_booking_user ON activity_bookings(user_id)""",
    """CREATE INDEX IF NOT EXISTS activity_slot_day ON activity_slots(activity_id,day,active)""",
    """CREATE TABLE IF NOT EXISTS activity_favorites (
 user_id INTEGER NOT NULL REFERENCES users(id), activity_id INTEGER NOT NULL REFERENCES activities(id),
 PRIMARY KEY(user_id,activity_id))""",
    """CREATE TABLE IF NOT EXISTS activity_reviews (
 id INTEGER PRIMARY KEY, activity_id INTEGER NOT NULL REFERENCES activities(id),
 user_id INTEGER NOT NULL REFERENCES users(id), rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
 comment TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TRIGGER IF NOT EXISTS activity_booking_guard BEFORE INSERT ON activity_bookings BEGIN
 SELECT CASE WHEN NOT EXISTS (
 SELECT 1 FROM activity_slots s JOIN activities a ON a.id=s.activity_id
 WHERE s.id=NEW.slot_id AND a.id=NEW.activity_id AND s.active=1 AND a.deleted=0
 AND a.host_id=NEW.host_id AND a.kind=NEW.kind AND NEW.user_id!=a.host_id
 AND s.day=NEW.day AND s.start_time=NEW.start_time AND NEW.people<=s.capacity AND NEW.people<=a.capacity
 AND NEW.unit_price=a.price AND NEW.price_type=a.price_type
 AND NEW.end_time=strftime('%H:%M',s.day||' '||s.start_time, '+'||a.duration_minutes||' minutes')
 AND s.day||' '||s.start_time>strftime('%Y-%m-%d %H:%M','now','+330 minutes'))
 THEN RAISE(ABORT,'Invalid activity reservation') END;
 SELECT CASE WHEN (SELECT COALESCE(SUM(people),0) FROM activity_bookings WHERE slot_id=NEW.slot_id AND status='confirmed')+NEW.people>
 (SELECT min(s.capacity,a.capacity) FROM activity_slots s JOIN activities a ON a.id=s.activity_id WHERE s.id=NEW.slot_id)
 THEN RAISE(ABORT,'Activity capacity exceeded') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM activity_bookings b WHERE b.host_id=NEW.host_id AND b.day=NEW.day AND b.status='confirmed'
 AND b.start_time<NEW.end_time AND b.end_time>NEW.start_time
 AND (NEW.kind='services' OR b.kind='services' OR b.slot_id!=NEW.slot_id))
 THEN RAISE(ABORT,'Provider time is already reserved') END;
 END""",
    """CREATE TRIGGER IF NOT EXISTS activity_booking_immutable BEFORE UPDATE ON activity_bookings
 WHEN NEW.status!='cancelled' OR NEW.activity_id!=OLD.activity_id OR NEW.slot_id!=OLD.slot_id OR NEW.user_id!=OLD.user_id
 OR NEW.host_id!=OLD.host_id OR NEW.day!=OLD.day OR NEW.start_time!=OLD.start_time OR NEW.end_time!=OLD.end_time
 OR NEW.people!=OLD.people OR NEW.unit_price!=OLD.unit_price OR NEW.total!=OLD.total OR NEW.subtotal!=OLD.subtotal
 OR NEW.service_fee!=OLD.service_fee OR NEW.price_type!=OLD.price_type OR NEW.kind!=OLD.kind
 OR NEW.idempotency_key!=OLD.idempotency_key OR NEW.fingerprint!=OLD.fingerprint
 BEGIN SELECT RAISE(ABORT,'Only cancellation is allowed'); END""",
]


def migrate_activities(db):
    if db.execute("SELECT 1 FROM schema_migrations WHERE version=4").fetchone():
        return
    for statement in STATEMENTS:
        db.execute(statement)
    db.execute("INSERT INTO schema_migrations(version) VALUES(4)")
