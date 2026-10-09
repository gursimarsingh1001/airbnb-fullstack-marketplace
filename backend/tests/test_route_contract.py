"""Keep published API paths stable as implementation modules are reorganized."""
from backend.main import app

def test_public_api_routes_are_preserved():
    actual = {(method, route.path) for route in app.routes
              if hasattr(route, "methods") and route.path.startswith("/api/")
              for method in route.methods}
    expected = {
        ('DELETE', '/api/activities/bookings/{bid}'),
        ('DELETE', '/api/activities/favorites/{aid}'),
        ('DELETE', '/api/activities/host/{aid}'),
        ('DELETE', '/api/bookings/{id}'),
        ('DELETE', '/api/host/listings/{id}'),
        ('DELETE', '/api/wishlists/{id}'),
        ('GET', '/api/activities'),
        ('GET', '/api/activities/bookings'),
        ('GET', '/api/activities/favorites'),
        ('GET', '/api/activities/host/dashboard'),
        ('GET', '/api/activities/{aid}'),
        ('GET', '/api/bookings'),
        ('GET', '/api/health'),
        ('GET', '/api/host/dashboard'),
        ('GET', '/api/listings'),
        ('GET', '/api/listings/{id}'),
        ('GET', '/api/photos/{key}'),
        ('GET', '/api/users'),
        ('GET', '/api/wishlists'),
        ('POST', '/api/activities/bookings'),
        ('POST', '/api/activities/host'),
        ('POST', '/api/activities/quote'),
        ('POST', '/api/bookings'),
        ('POST', '/api/bookings/{id}/review'),
        ('POST', '/api/host/listings'),
        ('POST', '/api/host/photos'),
        ('POST', '/api/quote'),
        ('PUT', '/api/activities/favorites/{aid}'),
        ('PUT', '/api/activities/host/{aid}'),
        ('PUT', '/api/host/listings/{id}'),
        ('PUT', '/api/wishlists/{id}'),
    }
    assert actual == expected
