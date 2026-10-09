from test_api import client  # noqa: F401
from backend import database
from backend.catalogue import expand_catalogue, expand_large_catalogue, expand_regional_catalogue


def test_sort_is_applied_before_pagination_and_filters(client):
    low = client.get('/api/listings?sort=price_low&limit=50').json()['items']
    assert len(low) == 50
    assert [h['price'] for h in low] == sorted(h['price'] for h in low)
    page = client.get('/api/listings?sort=price_low&limit=5&page=2').json()['items']
    assert [h['id'] for h in page] == [h['id'] for h in low[5:10]]
    high = client.get('/api/listings?sort=price_high&q=Goa&limit=50').json()['items']
    assert all('Goa' in h['location'] for h in high)
    assert [h['price'] for h in high] == sorted((h['price'] for h in high), reverse=True)
    rated = client.get('/api/listings?sort=rating&limit=50').json()['items']
    assert [h['rating'] for h in rated] == sorted((h['rating'] for h in rated), reverse=True)
    assert client.get('/api/listings?sort=unknown').status_code == 422


def test_catalogue_expansion_is_idempotent_and_preserves_edits(client):
    with database.connect() as db:
        db.execute("UPDATE listings SET title='An edited demo home' WHERE id=21")
        db.execute('UPDATE listings SET deleted=1 WHERE id=22')
        bookings = [tuple(row) for row in db.execute('SELECT * FROM bookings ORDER BY id')]
        expand_regional_catalogue(db)
        expand_regional_catalogue(db)
        expand_catalogue(db)
        expand_large_catalogue(db)
        expand_large_catalogue(db)
        assert db.execute('SELECT COUNT(*) FROM listings').fetchone()[0] == 272
        assert db.execute('SELECT title FROM listings WHERE id=21').fetchone()[0] == 'An edited demo home'
        assert db.execute('SELECT deleted FROM listings WHERE id=22').fetchone()[0] == 1
        assert [tuple(row) for row in db.execute('SELECT * FROM bookings ORDER BY id')] == bookings
    homes = client.get('/api/listings?limit=50').json()['items']
    assert all(h['photos'] and h['amenities'] and h['latitude'] and h['longitude'] for h in homes)


def test_all_map_pages_cover_catalogue(client):
    ids = []
    for page in range(1, 7):
        result = client.get(f'/api/listings?limit=50&page={page}').json()
        assert result['total'] == 272 and result['pages'] == 6
        ids.extend(item['id'] for item in result['items'])
    assert len(ids) == len(set(ids)) == 272


def test_yesterday_rejected_at_india_midnight(client, monkeypatch):
    from datetime import datetime, timezone, timedelta
    from backend import booking_rules
    from backend.main import validate_dates
    from fastapi import HTTPException
    import pytest
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 8, 19, tzinfo=timezone.utc).astimezone(tz)
    monkeypatch.setattr(booking_rules, 'datetime', FrozenDateTime)
    assert str(booking_rules.booking_today()) == '2026-10-09'
    yesterday = booking_rules.booking_today() - timedelta(days=1)
    with pytest.raises(HTTPException) as error:
        validate_dates(yesterday, yesterday + timedelta(days=2))
    assert error.value.status_code == 422

def test_regional_destinations_are_searchable_with_map_positions(client):
    from backend.catalogue import REGIONAL_DESTINATIONS
    for location, country, latitude, longitude in REGIONAL_DESTINATIONS:
        result = client.get('/api/listings', params={'q': location.split(',')[0], 'limit': 50}).json()
        assert any(h['country'] == country and h['latitude'] == latitude and h['longitude'] == longitude and h['photos'] for h in result['items']), location
