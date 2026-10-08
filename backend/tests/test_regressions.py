"""Critical API and storage regressions, always using an isolated database."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.booking_rules import booking_today
from backend.main import app
from test_api import client, listing_payload, stay


@pytest.mark.parametrize("offset,nights", [(60, 3), (59, 2), (62, 3), (61, 1), (59, 5)])
def test_every_overlap_shape_is_rejected(client, offset, nights):
    assert client.post("/api/bookings", json=stay()).status_code == 201
    body = stay(offset=offset, nights=nights)
    assert client.post("/api/quote", json=body).status_code == 409
    assert client.post("/api/bookings", json=body).status_code == 409
    found = client.get("/api/listings", params={k: body[k] for k in ("check_in", "check_out")}).json()
    assert 4 not in {home["id"] for home in found["items"]}


def test_back_to_back_reservations_allowed_on_both_edges(client):
    assert client.post("/api/bookings", json=stay()).status_code == 201
    assert client.post("/api/bookings", json=stay(offset=57)).status_code == 201
    assert client.post("/api/bookings", json=stay(offset=63)).status_code == 201


@pytest.mark.parametrize("changes", [
    {"check_out": stay()["check_in"]},
    {"check_in": str(booking_today() - timedelta(days=1))},
    {"check_out": "2027-02-30"},
    {"guests": 0}, {"guests": -1}, {"guests": 1.5}, {"guests": True},
])
def test_invalid_stay_shapes(client, changes):
    assert client.post("/api/bookings", json={**stay(), **changes}).status_code == 422


def test_missing_deleted_listing_and_unknown_user_cannot_book(client):
    assert client.post("/api/bookings", json=stay(listing=9999)).status_code == 404
    assert client.post("/api/bookings", json=stay(), headers={"X-Demo-User": "9999"}).status_code == 401
    home = client.post("/api/host/listings", json=listing_payload(), headers={"X-Demo-User": "2"}).json()
    assert client.delete(f"/api/host/listings/{home['id']}", headers={"X-Demo-User": "2"}).status_code == 200
    assert client.post("/api/bookings", json=stay(listing=home["id"])).status_code == 404


def test_idempotent_retries_return_original_confirmed_price(client):
    body = stay()
    quote = client.post("/api/quote", json=body).json()
    body["expected_total"] = quote["total"]
    headers = {"Idempotency-Key": "checkout-retry-123"}
    first = client.post("/api/bookings", json=body, headers=headers)
    second = client.post("/api/bookings", json=body, headers=headers)
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert all(first.json()[key] == value for key, value in quote.items())
    assert client.post("/api/bookings", json={**body, "guests": 3}, headers=headers).status_code == 409
    with database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM bookings WHERE idempotency_key=?", (headers["Idempotency-Key"],)).fetchone()[0] == 1
    client.delete(f"/api/bookings/{first.json()['id']}")
    assert client.post("/api/bookings", json=body, headers=headers).status_code == 409


def test_simultaneous_same_key_returns_one_reservation(client):
    def submit(_):
        return client.post("/api/bookings", json=stay(), headers={"Idempotency-Key": "double-click-123"})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert [r.status_code for r in results] == [201, 201]
    assert len({r.json()["id"] for r in results}) == 1


def test_changed_price_requires_checkout_review(client):
    body = stay()
    quote = client.post("/api/quote", json=body).json()
    with database.connect() as db:
        db.execute("UPDATE listings SET price=price+100 WHERE id=4")
    assert client.post("/api/bookings", json={**body, "expected_total": quote["total"]}).status_code == 409
    assert not any(b["listing_id"] == 4 for b in client.get("/api/bookings").json())


def test_historical_price_and_private_scope(client):
    response = client.post("/api/bookings", json=stay()).json()
    with database.connect() as db:
        db.execute("UPDATE listings SET price=price+1000,cleaning_fee=2000 WHERE id=4")
    own = next(b for b in client.get("/api/bookings").json() if b["id"] == response["id"])
    assert own["total"] == response["total"] and own["nightly_price"] == response["nightly_price"]
    assert "idempotency_key" not in own and "request_fingerprint" not in own
    assert response["id"] not in {b["id"] for b in client.get("/api/bookings", headers={"X-Demo-User": "5"}).json()}
    host = client.get("/api/host/dashboard", headers={"X-Demo-User": "2"}).json()
    other_host = client.get("/api/host/dashboard", headers={"X-Demo-User": "3"}).json()
    assert response["id"] in {b["id"] for b in host["bookings"]}
    assert response["id"] not in {b["id"] for b in other_host["bookings"]}


@pytest.mark.parametrize("params", [{"guests": 0}, {"min_price": -1}, {"max_price": -1}, {"min_price": 2000, "max_price": 1000}, {"check_in": stay()["check_in"]}, {"page": 0}, {"limit": 51}])
def test_search_validation(client, params):
    assert client.get("/api/listings", params=params).status_code == 422


def test_combined_search_and_filtered_pagination(client):
    params = dict(q="Himachal", category="Cabins", property_type="Cabin", amenities="Wifi, Mountain view", min_price=6000, max_price=8000, guests=5, limit=1)
    pages = [client.get("/api/listings", params={**params, "page": page}).json() for page in (1, 2)]
    assert all(page["total"] == page["pages"] == 2 for page in pages)
    assert {page["items"][0]["id"] for page in pages} == {2, 13}
    body = stay(listing=2)
    assert client.post("/api/bookings", json=body).status_code == 201
    result = client.get("/api/listings", params={**params, "check_in": body["check_in"], "check_out": body["check_out"]}).json()
    assert result["total"] == result["pages"] == 1 and result["items"][0]["id"] == 13


def test_host_edit_replaces_relationships_atomically(client):
    headers = {"X-Demo-User": "2"}
    body = listing_payload()
    home = client.post("/api/host/listings", json=body, headers=headers).json()
    url = f"/api/host/listings/{home['id']}"
    edited = {**body, "photos": ["https://example.com/one.jpg", "https://example.com/two.jpg"], "amenities": ["Wifi", "Pool", "Pool"]}
    response = client.put(url, json=edited, headers=headers)
    assert response.status_code == 200
    assert response.json()["photos"] == edited["photos"]
    assert set(response.json()["amenities"]) == {"Wifi", "Pool"}
    assert client.put(url, json={**body, "amenities": ["Invalid"]}, headers=headers).status_code == 422
    persisted = client.get(f"/api/listings/{home['id']}").json()
    assert persisted["photos"] == edited["photos"] and set(persisted["amenities"]) == {"Wifi", "Pool"}
    assert client.delete(url, headers={"X-Demo-User": "3"}).status_code == 403
    assert client.get(f"/api/listings/{home['id']}").status_code == 200


@pytest.mark.parametrize("changes", [{"price": 0}, {"price": -1}, {"price": 500.5}, {"max_guests": 0}, {"max_guests": 17}, {"photos": ["javascript:alert(1)"]}, {"photos": []}, {"title": "   "}])
def test_bad_listing_input(client, changes):
    assert client.post("/api/host/listings", json={**listing_payload(), **changes}, headers={"X-Demo-User": "2"}).status_code == 422


def test_capacity_cannot_undercut_upcoming_reservations(client):
    headers = {"X-Demo-User": "2"}
    body = listing_payload()
    home = client.post("/api/host/listings", json=body, headers=headers).json()
    assert client.post("/api/bookings", json={**stay(listing=home["id"]), "guests": 4}).status_code == 201
    assert client.put(f"/api/host/listings/{home['id']}", json={**body, "max_guests": 2}, headers=headers).status_code == 409


def test_restart_initialization_preserves_all_user_data(client):
    headers = {"X-Demo-User": "2"}
    home = client.post("/api/host/listings", json=listing_payload(), headers=headers).json()
    booking = client.post("/api/bookings", json=stay(listing=home["id"])).json()
    client.put(f"/api/wishlists/{home['id']}")
    # A fresh ASGI lifespan runs the same initialization a restarted server uses.
    with TestClient(app) as restarted:
        assert restarted.get("/api/listings").json()["total"] == 21
        assert home["id"] in {h["id"] for h in restarted.get("/api/wishlists").json()}
        assert booking["id"] in {b["id"] for b in restarted.get("/api/bookings").json()}
        assert restarted.post("/api/bookings", json=stay(listing=home["id"])).status_code == 409
    with database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 60


@pytest.mark.parametrize("changes", [{"check_in": "2099-2-30"}, {"check_in": "2027-02-30"}, {"guests": 99}, {"nightly_price": -1}, {"service_fee": 0}, {"total": 1}, {"user_id": 2}])
def test_database_rejects_invalid_booking_records(client, changes):
    body = stay()
    quote = client.post("/api/quote", json=body).json()
    record = dict(**body, user_id=1, nightly_price=quote["nightly_price"], cleaning_fee=quote["cleaning_fee"], service_fee=quote["service_fee"], total=quote["total"])
    record.update(changes)
    with database.connect() as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO bookings(" + ",".join(record) + ") VALUES(" + ",".join("?" for _ in record) + ")", list(record.values()))


def test_database_blocks_overlap_and_historical_mutation(client):
    booked = client.post("/api/bookings", json=stay()).json()
    with database.connect() as db:
        with pytest.raises(sqlite3.IntegrityError, match="Conflicting reservation"):
            db.execute("INSERT INTO bookings(listing_id,user_id,check_in,check_out,guests,nightly_price,cleaning_fee,service_fee,total) SELECT listing_id,5,check_in,check_out,guests,nightly_price,cleaning_fee,service_fee,total FROM bookings WHERE id=?", (booked["id"],))
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("UPDATE bookings SET total=1 WHERE id=?", (booked["id"],))


def test_date_policy_is_explicit_utc(client):
    health = client.get("/api/health").json()
    assert health["booking_today"] == str(booking_today()) and health["date_policy"] == "UTC"
    assert client.post("/api/bookings", json=stay(offset=0, nights=1)).status_code == 201
