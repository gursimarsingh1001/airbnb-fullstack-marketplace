from test_api import client  # noqa: F401
from backend import database
from backend.catalogue import expand_catalogue


def test_sort_is_applied_before_pagination_and_filters(client):
    low = client.get('/api/listings?sort=price_low&limit=50').json()['items']
    assert len(low) == 44
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
        expand_catalogue(db)
        expand_catalogue(db)
        assert db.execute('SELECT COUNT(*) FROM listings').fetchone()[0] == 44
        assert db.execute('SELECT title FROM listings WHERE id=21').fetchone()[0] == 'An edited demo home'
        assert db.execute('SELECT deleted FROM listings WHERE id=22').fetchone()[0] == 1
        assert [tuple(row) for row in db.execute('SELECT * FROM bookings ORDER BY id')] == bookings
    homes = client.get('/api/listings?limit=50').json()['items']
    assert all(h['photos'] and h['amenities'] and h['latitude'] and h['longitude'] for h in homes)
