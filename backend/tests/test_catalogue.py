from test_api import client  # noqa: F401
from backend import database


def test_sort_is_applied_before_pagination_and_filters(client):
    low_result = client.get('/api/listings?sort=price_low&limit=50').json()
    low = low_result['items']
    assert len(low) == low_result['total'] == 49
    assert [h['price'] for h in low] == sorted(h['price'] for h in low)
    page = client.get('/api/listings?sort=price_low&limit=5&page=2').json()['items']
    assert [h['id'] for h in page] == [h['id'] for h in low[5:10]]
    high = client.get('/api/listings?sort=price_high&q=Goa&limit=50').json()['items']
    assert all('Goa' in h['location'] for h in high)
    assert [h['price'] for h in high] == sorted((h['price'] for h in high), reverse=True)
    rated = client.get('/api/listings?sort=rating&limit=50').json()['items']
    assert [h['rating'] for h in rated] == sorted((h['rating'] for h in rated), reverse=True)
    assert client.get('/api/listings?sort=unknown').status_code == 422


def test_curated_catalogue_is_unique_and_covers_required_sections(client):
    homes_result = client.get('/api/listings?limit=50').json()
    homes = homes_result['items']
    assert homes_result['total'] == 49 and len(homes) == 49
    assert len({home['id'] for home in homes}) == 49
    assert len({home['title'] for home in homes}) == 49
    assert len({home['location'] for home in homes}) == 49
    assert len({home['description'] for home in homes}) == 49
    assert len({home['photos'][0] for home in homes}) == 49
    assert len({home['price'] for home in homes}) == 49
    assert len({home['rating'] for home in homes}) == 49
    assert len({home['review_count'] for home in homes}) == 49
    assert len({tuple(sorted(home['amenities'])) for home in homes}) == 49
    assert all(
        len(home['photos']) == (5 if home['id'] == 1 else 4)
        and home['latitude']
        and home['longitude']
        for home in homes
    )
    assert all(home['host']['avatar'].startswith('http') for home in homes)
    assert len({home['host']['name'] for home in homes}) == 49

    primary_photos = [home['photos'][0] for home in homes]
    host_names = [home['host']['name'] for home in homes]
    for kind, expected in [('experiences', 24), ('services', 20)]:
        result = client.get('/api/activities', params={'kind': kind, 'limit': 50}).json()
        rows = result['items']
        assert result['total'] == expected and len(rows) == expected
        assert len({row['id'] for row in rows}) == expected
        assert len({row['title'] for row in rows}) == expected
        assert len({row['description'] for row in rows}) == expected
        assert len({row['location'] for row in rows}) == expected
        assert len({row['photos'][0] for row in rows}) == expected
        assert len({row['price'] for row in rows}) == expected
        assert len({row['rating'] for row in rows}) == expected
        assert len({row['review_count'] for row in rows}) == expected
        assert len({row['host']['name'] for row in rows}) == expected
        assert all(len(row['photos']) == 3 and row['host']['avatar'].startswith('http') for row in rows)
        primary_photos.extend(row['photos'][0] for row in rows)
        host_names.extend(row['host']['name'] for row in rows)

    # Every visible offer has its own lead image and host identity, including
    # across the home, experience, and service marketplaces.
    assert len(primary_photos) == len(set(primary_photos))
    assert len(host_names) == len(set(host_names))


def test_seed_restart_is_idempotent_and_preserves_legacy_booking_history(client):
    with database.connect() as db:
        before = {
            table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            for table in ('listings', 'bookings', 'activities', 'activity_bookings', 'reviews', 'activity_reviews')
        }
        assert db.execute('SELECT deleted FROM listings WHERE id=2').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM bookings WHERE listing_id=2').fetchone()[0] > 0
    database.initialize()
    with database.connect() as db:
        after = {
            table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            for table in before
        }
    assert after == before
    assert client.get('/api/listings?limit=50').json()['total'] == 49


def test_map_pages_cover_every_active_home(client):
    page = client.get('/api/listings?limit=50&page=1').json()
    assert page['total'] == 49 and page['pages'] == 1
    assert len({home['id'] for home in page['items']}) == 49


def test_yesterday_rejected_at_india_midnight(client, monkeypatch):
    from datetime import datetime, timezone, timedelta
    from backend import booking_rules
    from backend.services.bookings import validate_dates
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


def test_curated_destinations_have_map_positions_and_search_matches(client):
    result = client.get('/api/listings?limit=50').json()['items']
    locations = [home['location'] for home in result]
    for city in ('Goa', 'Manali', 'Shimla', 'Jaipur', 'Udaipur', 'Mumbai', 'Delhi', 'Rishikesh', 'Mussoorie', 'Coorg', 'Ooty', 'Munnar', 'Pondicherry', 'Lonavala', 'Alibaug', 'Darjeeling', 'Srinagar', 'Leh', 'Bengaluru', 'Hyderabad', 'Bali', 'Dubai', 'London', 'Paris', 'Rome', 'Tokyo'):
        assert any(city.casefold() in location.casefold() for location in locations), city
    for home in result:
        found = client.get('/api/listings', params={'q': home['location'].split(',')[0], 'limit': 50}).json()['items']
        assert home['id'] in {item['id'] for item in found}
        assert -90 <= home['latitude'] <= 90 and -180 <= home['longitude'] <= 180
