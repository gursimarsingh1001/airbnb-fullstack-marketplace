from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
import sqlite3
import pytest
from fastapi.testclient import TestClient
from backend import database
from backend.main import app
from backend.booking_rules import booking_today


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_BLOB_ENABLED", raising=False)
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def stay(listing=4, offset=60, nights=3):
    start = booking_today() + timedelta(days=offset)
    return {
        "listing_id": listing,
        "check_in": str(start),
        "check_out": str(start + timedelta(days=nights)),
        "guests": 2,
    }


def listing_payload():
    return dict(
        title="A test cottage in the mountains",
        description="A lovely quiet home with fresh mountain air and everything you need.",
        location="Test Valley",
        country="India",
        category="Cabins",
        property_type="Cabin",
        price=5000,
        cleaning_fee=500,
        max_guests=4,
        bedrooms=2,
        beds=2,
        bathrooms=1,
        photos=["https://images.unsplash.com/photo-1510798831971-661eb04b3739"],
        amenities=["Wifi", "Kitchen"],
    )


def test_search_filters_pagination_and_seed(client):
    first = client.get("/api/listings").json()
    assert first["total"] == 20 and len(first["items"]) == 15
    second = client.get("/api/listings?page=2").json()
    assert len(second["items"]) == 5
    assert not ({x["id"] for x in first["items"]} & {x["id"] for x in second["items"]})
    found = client.get("/api/listings?q=goa&amenities=Pool&max_price=12000").json()[
        "items"
    ]
    assert found and all(
        "Goa" in x["location"] and "Pool" in x["amenities"] and x["price"] <= 12000
        for x in found
    )
    assert client.get("/api/listings?q=nonexistent").json()["total"] == 0


def test_booking_quote_persistence_and_cancellation(client):
    body = stay()
    quote = client.post("/api/quote", json=body).json()
    assert quote["total"] == 5400 * 3 + 900 + 2268
    booking = client.post("/api/bookings", json=body)
    assert booking.status_code == 201
    bid = booking.json()["id"]
    assert any(b["id"] == bid for b in client.get("/api/bookings").json())
    with database.connect() as db:
        assert (
            db.execute("SELECT total FROM bookings WHERE id=?", (bid,)).fetchone()[0]
            == quote["total"]
        )
    assert client.post("/api/bookings", json=body).status_code == 409
    assert (
        client.delete(f"/api/bookings/{bid}", headers={"X-Demo-User": "5"}).status_code
        == 404
    )
    assert client.delete(f"/api/bookings/{bid}").status_code == 200
    assert client.post("/api/bookings", json=body).status_code == 201


def test_overlap_edges_and_availability_search(client):
    assert client.post("/api/bookings", json=stay()).status_code == 201
    for offset, nights in [(59, 2), (61, 1), (59, 5), (62, 2)]:
        assert (
            client.post(
                "/api/bookings", json=stay(offset=offset, nights=nights)
            ).status_code
            == 409
        )
    assert client.post("/api/bookings", json=stay(offset=63)).status_code == 201
    body = stay()
    result = client.get(
        "/api/listings",
        params={"check_in": body["check_in"], "check_out": body["check_out"]},
    ).json()
    assert 4 not in [x["id"] for x in result["items"]]


def test_concurrent_requests_cannot_double_book(client):
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(
            pool.map(
                lambda _: client.post("/api/bookings", json=stay()).status_code,
                range(2),
            )
        )
    assert sorted(statuses) == [201, 409]


@pytest.mark.parametrize(
    "changes",
    [
        {"guests": 17},
        {"guests": 7},
        {"check_in": "2000-01-01"},
        {"check_out": "2000-01-01"},
        {"check_in": "not-a-date"},
    ],
)
def test_invalid_booking_rejected(client, changes):
    assert client.post("/api/bookings", json={**stay(), **changes}).status_code == 422


def test_host_ownership_crud_and_soft_delete(client):
    body = listing_payload()
    host = {"X-Demo-User": "2"}
    assert client.post("/api/host/listings", json=body).status_code == 403
    created = client.post("/api/host/listings", json=body, headers=host)
    assert created.status_code == 201
    id = created.json()["id"]
    assert (
        client.put(
            f"/api/host/listings/{id}",
            json={**body, "price": 8000},
            headers={"X-Demo-User": "3"},
        ).status_code
        == 403
    )
    assert (
        client.put(
            f"/api/host/listings/{id}", json={**body, "price": 8000}, headers=host
        ).json()["price"]
        == 8000
    )
    assert (
        client.post("/api/bookings", json=stay(listing=id), headers=host).status_code
        == 422
    )
    reservation = client.post("/api/bookings", json=stay(listing=id)).json()["id"]
    assert client.delete(f"/api/host/listings/{id}", headers=host).status_code == 409
    client.delete(f"/api/bookings/{reservation}")
    assert client.delete(f"/api/host/listings/{id}", headers=host).status_code == 200
    assert client.get(f"/api/listings/{id}").status_code == 404
    assert any(b["id"] == reservation for b in client.get("/api/bookings").json())


def test_wishlist_is_per_user_and_idempotent(client):
    client.put("/api/wishlists/3")
    client.put("/api/wishlists/3")
    assert len([h for h in client.get("/api/wishlists").json() if h["id"] == 3]) == 1
    assert client.get("/api/wishlists", headers={"X-Demo-User": "2"}).json() == []
    client.delete("/api/wishlists/3")
    assert 3 not in [h["id"] for h in client.get("/api/wishlists").json()]


def test_bad_listing_rolls_back(client):
    result = client.post(
        "/api/host/listings",
        headers={"X-Demo-User": "2"},
        json={**listing_payload(), "amenities": ["Invented amenity"]},
    )
    assert result.status_code == 422
    assert client.get("/api/listings").json()["total"] == 20
