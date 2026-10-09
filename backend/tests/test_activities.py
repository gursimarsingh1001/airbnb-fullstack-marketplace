from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from fastapi.testclient import TestClient
from test_api import client  # noqa: F401
from backend import database
from backend.main import app
from backend.booking_rules import booking_today
import sqlite3
import pytest


def payload(kind="experiences", time="10:00"):
    return dict(
        kind=kind,
        title="A hands-on local workshop",
        description="Enjoy a thoughtful and relaxed session with a friendly local provider.",
        location="Test City",
        country="India",
        category="Food & drink" if kind == "experiences" else "Private chefs",
        price=2000,
        price_type="person" if kind == "experiences" else "group",
        duration_minutes=60,
        capacity=4,
        language="English",
        setting="Indoor",
        service_location="At your stay",
        itinerary="Meet the host.\nEnjoy a guided session.",
        included="Materials and water",
        requirements="Arrive ten minutes early.",
        photos=["https://images.unsplash.com/photo-1556911220-bff31c812dba"],
        slots=[
            dict(
                day=str(booking_today() + timedelta(days=90)),
                start_time=time,
                capacity=4,
            )
        ],
    )


def create(client, kind="experiences", time="10:00", host=2):
    r = client.post(
        "/api/activities/host",
        json=payload(kind, time),
        headers={"X-Demo-User": str(host)},
    )
    assert r.status_code == 201, r.text
    a = client.get("/api/activities/" + str(r.json()["id"])).json()
    return a, a["slots"][0]["id"]


def book(client, slot, people=1, key="test-key-123", user=1):
    body = {"slot_id": slot, "people": people}
    q = client.post(
        "/api/activities/quote", json=body, headers={"X-Demo-User": str(user)}
    )
    if q.status_code != 200:
        return q
    return client.post(
        "/api/activities/bookings",
        json={**body, "expected_total": q.json()["total"]},
        headers={"X-Demo-User": str(user), "Idempotency-Key": key},
    )


def test_activity_seed_and_combined_search(client):
    for kind in ["experiences", "services"]:
        result = client.get(
            "/api/activities", params={"kind": kind, "limit": 50}
        ).json()
        expected_count = 24 if kind == "experiences" else 20
        assert result["total"] == expected_count and all(
            a["photos"] and a["review_count"] >= 100 for a in result["items"]
        )
        a = result["items"][0]
        detail = client.get(f"/api/activities/{a['id']}").json()
        assert detail["slots"] and detail["reviews"]
        result = client.get(
            "/api/activities",
            params={
                "kind": kind,
                "q": a["location"],
                "category": a["category"],
                "language": a["language"],
                "min_rating": 4,
                "day": detail["slots"][0]["day"],
                "people": 2,
                "time_of_day": "morning",
                "max_price": a["price"],
            },
        ).json()
        assert a["id"] in [i["id"] for i in result["items"]]
    assert (
        client.get(
            "/api/activities?kind=services&min_price=500&max_price=100"
        ).status_code
        == 422
    )
    assert (
        client.get("/api/activities?kind=experiences&min_rating=5.1").status_code == 422
    )
    with database.connect() as db:
        before = db.execute("SELECT COUNT(*) FROM activity_slots").fetchone()[0]
    database.initialize()
    with database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM activity_slots").fetchone()[0] == before


@pytest.mark.parametrize("kind", ["experiences", "services"])
def test_time_of_day_filters_respect_boundaries_and_remaining_capacity(client, kind):
    offerings = {}
    slots = {}
    for time in ["11:00", "12:00", "16:00", "17:00"]:
        offering, slot = create(client, kind, time)
        offerings[time] = offering["id"]
        slots[time] = slot

    params = {"kind": kind, "q": "Test City", "people": 4}
    for period, times in [("morning", ["11:00"]), ("afternoon", ["12:00", "16:00"]), ("evening", ["17:00"])]:
        response = client.get("/api/activities", params={**params, "time_of_day": period})
        assert response.status_code == 200
        assert {item["id"] for item in response.json()["items"]} == {offerings[time] for time in times}

    assert book(client, slots["12:00"], people=1).status_code == 201
    response = client.get("/api/activities", params={**params, "time_of_day": "afternoon"})
    assert {item["id"] for item in response.json()["items"]} == {offerings["16:00"]}


def test_experience_capacity_price_history_persistence_and_idempotency(client):
    a, slot = create(client)
    b = book(client, slot, 3)
    assert b.status_code == 201, b.text
    assert b.json()["total"] == 6600
    assert book(client, slot, 2, key="other-key").status_code == 409
    # Same exact request repeats despite reduced remaining availability.
    body = {"slot_id": slot, "people": 3, "expected_total": 6600}
    repeated = client.post(
        "/api/activities/bookings",
        json=body,
        headers={"Idempotency-Key": "test-key-123"},
    )
    assert repeated.json()["id"] == b.json()["id"]
    assert book(client, slot, 1, key="last-seat", user=5).status_code == 201
    assert book(client, slot, 1, key="too-many").status_code == 409
    edit = payload()
    edit["price"] = 9000
    assert (
        client.put(
            f"/api/activities/host/{a['id']}", json=edit, headers={"X-Demo-User": "2"}
        ).status_code
        == 200
    )
    with TestClient(app) as restarted:
        trips = restarted.get("/api/activities/bookings").json()
        assert any(x["id"] == b.json()["id"] and x["total"] == 6600 for x in trips)
        hosted = restarted.get(
            "/api/activities/host/dashboard", headers={"X-Demo-User": "2"}
        ).json()
        assert b.json()["id"] in [x["id"] for x in hosted["bookings"]]


def test_provider_conflicts_across_services_and_back_to_back(client):
    a, s1 = create(client, "services")
    _, s2 = create(client, "services", "10:30")
    _, s3 = create(client, "services", "11:00")
    assert book(client, s1).status_code == 201
    assert book(client, s2, key="overlap-key").status_code == 409
    assert book(client, s3, key="adjacent-key").status_code == 201
    _, s4 = create(client, "experiences", "10:15")
    assert book(client, s4, key="experience-conflict").status_code == 409
    assert (
        client.delete(
            f"/api/activities/host/{a['id']}", headers={"X-Demo-User": "2"}
        ).status_code
        == 409
    )


def test_simultaneous_experience_capacity_and_service_exclusivity(client):
    for kind in ["experiences", "services"]:
        a, slot = create(client, kind, host=3 if kind == "services" else 2)

        def submit(i):
            people = 3 if kind == "experiences" else 1
            return client.post(
                "/api/activities/bookings",
                json={
                    "slot_id": slot,
                    "people": people,
                    "expected_total": 6600 if kind == "experiences" else 2200,
                },
                headers={"Idempotency-Key": f"concurrent-{kind}-{i}"},
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, [1, 2]))
        assert sorted(results) == [201, 409]


def test_activity_ownership_cancellation_favorites_and_soft_delete(client):
    a, slot = create(client)
    aid = a["id"]
    b = book(client, slot).json()
    bid = b["id"]
    assert (
        client.put(
            f"/api/activities/host/{aid}", json=payload(), headers={"X-Demo-User": "3"}
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/activities/host/{aid}", headers={"X-Demo-User": "3"}
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/activities/bookings/{bid}", headers={"X-Demo-User": "5"}
        ).status_code
        == 404
    )
    assert all(
        v["id"] != bid
        for v in client.get(
            "/api/activities/bookings", headers={"X-Demo-User": "5"}
        ).json()
    )
    for _ in range(2):
        assert client.put(f"/api/activities/favorites/{aid}").status_code == 200
    assert len(client.get("/api/activities/favorites").json()) == 1
    assert (
        client.get("/api/activities/favorites", headers={"X-Demo-User": "5"}).json()
        == []
    )
    assert client.delete(f"/api/activities/bookings/{bid}").status_code == 200
    assert book(client, slot, key="after-cancel").status_code == 201
    for r in client.get("/api/activities/bookings").json():
        client.delete(f"/api/activities/bookings/{r['id']}")
    assert (
        client.delete(
            f"/api/activities/host/{aid}", headers={"X-Demo-User": "2"}
        ).status_code
        == 200
    )
    assert client.get(f"/api/activities/{aid}").status_code == 404
    assert client.get("/api/activities/favorites").json() == []
    assert (
        client.get("/api/activities/bookings").json()[0]["activity"]["title"]
        == a["title"]
    )


def test_activity_input_and_price_validation(client):
    assert client.post("/api/activities/host", json=payload()).status_code == 403
    for update in [
        {"price": -1},
        {"capacity": 0},
        {"photos": ["javascript:alert(1)"]},
        {"photos": ["http://example.com/photo.jpg"]},
        {"slots": []},
        {"category": "Unknown"},
    ]:
        assert (
            client.post(
                "/api/activities/host",
                json={**payload(), **update},
                headers={"X-Demo-User": "2"},
            ).status_code
            == 422
        )
    p = payload()
    p["slots"][0]["day"] = str(booking_today() - timedelta(days=1))
    assert (
        client.post(
            "/api/activities/host", json=p, headers={"X-Demo-User": "2"}
        ).status_code
        == 422
    )
    a, slot = create(client)
    assert book(client, slot, 5).status_code == 422
    assert book(client, slot, user=2).status_code == 422
    assert (
        client.post(
            "/api/activities/bookings",
            json={"slot_id": slot, "people": 1, "expected_total": 1},
            headers={"Idempotency-Key": "wrong-price"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/activities/bookings", json={"slot_id": slot, "people": 1}
        ).status_code
        == 422
    )
    book(client, slot, 3)
    p = payload()
    p["slots"][0]["capacity"] = 2
    assert (
        client.put(
            f"/api/activities/host/{a['id']}", json=p, headers={"X-Demo-User": "2"}
        ).status_code
        == 409
    )


def test_home_extended_filters_combine(client):
    result = client.get(
        "/api/listings",
        params={
            "bedrooms": 2,
            "beds": 2,
            "bathrooms": 2,
            "min_rating": 4.9,
            "superhost": "true",
            "limit": 50,
        },
    ).json()
    assert result["total"] > 0
    assert all(
        h["bedrooms"] >= 2
        and h["beds"] >= 2
        and h["bathrooms"] >= 2
        and h["rating"] >= 4.9
        and h["superhost"]
        for h in result["items"]
    )
    assert client.get("/api/listings?min_rating=5&max_rating=4").status_code == 422
    assert client.get("/api/listings?bedrooms=-1").status_code == 422


def test_activity_database_guards_and_cancelled_retry(client):
    _, slot = create(client)
    result = book(client, slot, 4).json()
    with database.connect() as db:
        row = dict(
            db.execute(
                "SELECT * FROM activity_bookings WHERE id=?", (result["id"],)
            ).fetchone()
        )
        row.pop("id")
        row["idempotency_key"] = "direct-insert-key"
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO activity_bookings ("
                + ",".join(row)
                + ") VALUES ("
                + ",".join("?" for _ in row)
                + ")",
                list(row.values()),
            )
        db.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "UPDATE activity_bookings SET total=1 WHERE id=?", (result["id"],)
            )
        db.rollback()
    assert client.delete(f"/api/activities/bookings/{result['id']}").status_code == 200
    body = {"slot_id": slot, "people": 4, "expected_total": 8800}
    assert (
        client.post(
            "/api/activities/bookings",
            json=body,
            headers={"Idempotency-Key": "test-key-123"},
        ).status_code
        == 409
    )
    assert book(client, slot, 4, key="new-reservation-key").status_code == 201


def test_activity_pagination_and_removed_availability_survive_restart(client):
    first = client.get("/api/activities?kind=experiences&page=1").json()
    second = client.get("/api/activities?kind=experiences&page=2").json()
    assert len(first["items"]) == 12 and len(second["items"]) == 12
    assert not {a["id"] for a in first["items"]} & {a["id"] for a in second["items"]}
    activity_id = first["items"][0]["id"]
    a = client.get(f"/api/activities/{activity_id}").json()
    removed = a["slots"][0]["id"]
    p = {k: a[k] for k in payload() if k not in ("slots", "photos")}
    p["photos"] = a["photos"]
    p["slots"] = [
        {k: s[k] for k in ("day", "start_time", "capacity")} for s in a["slots"][1:]
    ]
    assert (
        client.put(
            f"/api/activities/host/{activity_id}",
            json=p,
            headers={"X-Demo-User": str(a["host"]["id"])},
        ).status_code
        == 200
    )
    database.initialize()
    assert removed not in [
        s["id"] for s in client.get(f"/api/activities/{activity_id}").json()["slots"]
    ]
