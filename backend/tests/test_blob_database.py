"""Exercise real SQLite snapshots with an in-memory conditional object store."""
from threading import Lock
import httpx
import pytest
from backend.blob_database import BlobStore, connect_snapshot, SnapshotConflict, SnapshotUnavailable
from backend.database import SCHEMA
from backend.seed import seed


class ConditionalStore:
    def __init__(self):
        self.content = None
        self.etag = None
        self.version = 0
        self.lock = Lock()

    def read(self):
        with self.lock:
            return self.content, self.etag

    def write(self, content, etag):
        with self.lock:
            if etag != self.etag:
                raise SnapshotConflict()
            self.content = content
            self.version += 1
            self.etag = str(self.version)
            return self.etag


def test_snapshot_survives_connection_replacement_and_rejects_stale_writes():
    store = ConditionalStore()
    with connect_snapshot(store) as db:
        db.executescript(SCHEMA)
        seed(db)
    assert store.version == 1
    first, second = connect_snapshot(store), connect_snapshot(store)
    try:
        assert first.execute('SELECT COUNT(*) FROM listings').fetchone()[0] == 20
        first.execute("UPDATE listings SET title='First successful edit' WHERE id=4")
        first.commit()
        second.execute("UPDATE listings SET title='Stale overwrite' WHERE id=4")
        with pytest.raises(SnapshotConflict):
            second.commit()
    finally:
        first.close()
        second.close()
    with connect_snapshot(store) as fresh:
        assert fresh.execute('SELECT title FROM listings WHERE id=4').fetchone()[0] == 'First successful edit'
    assert store.version == 2  # Read-only requests never publish a snapshot.


def test_failed_transaction_never_reaches_durable_store():
    store = ConditionalStore()
    with connect_snapshot(store) as db:
        db.executescript(SCHEMA)
        seed(db)
    original = store.content
    with pytest.raises(ValueError):
        with connect_snapshot(store) as db:
            db.execute("UPDATE listings SET price=999 WHERE id=4")
            raise ValueError('Abort request')
    assert store.content == original


def test_schema_only_changes_are_published_and_read_only_commit_is_free():
    store = ConditionalStore()
    with connect_snapshot(store) as db:
        db.execute("CREATE TABLE migration_test (id INTEGER PRIMARY KEY)")
    assert store.version == 1
    with connect_snapshot(store) as db:
        db.execute("ALTER TABLE migration_test ADD COLUMN label TEXT")
    assert store.version == 2
    with connect_snapshot(store) as db:
        assert "label" in {r[1] for r in db.execute("PRAGMA table_info(migration_test)")}
    assert store.version == 2


def test_additive_migration_keeps_legacy_snapshot_bookings():
    from backend.migrations import migrate
    store = ConditionalStore()
    with connect_snapshot(store) as db:
        db.executescript(SCHEMA)
        seed(db)
    with connect_snapshot(store) as db:
        before = [tuple(row) for row in db.execute("SELECT id,total FROM bookings ORDER BY id")]
        db.execute("BEGIN IMMEDIATE")
        migrate(db)
    with connect_snapshot(store) as db:
        assert [tuple(row) for row in db.execute("SELECT id,total FROM bookings ORDER BY id")] == before
        assert "idempotency_key" in {r[1] for r in db.execute("PRAGMA table_info(bookings)")}
        migrate(db)
    assert store.version == 2


def test_private_blob_image_upload_and_fetch_use_generated_path(monkeypatch):
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "vercel_blob_rw_store123_suffix_secret")
    image = b"\x89PNG\r\n\x1a\nsmall test image"
    requests = []

    def put(url, *, params, headers, content, timeout):
        requests.append((url, params, headers, content, timeout))
        return httpx.Response(200, json={"url": "https://store.private.blob.vercel-storage.com/test"}, request=httpx.Request("PUT", url))

    def get(url, *, params, headers, timeout):
        requests.append((url, params, headers, timeout))
        return httpx.Response(200, content=image, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "put", put)
    monkeypatch.setattr(httpx, "get", get)
    store = BlobStore()
    key = store.put_image(image, "image/png")
    assert len(key) == 36 and key.endswith(".png")
    upload = requests[0]
    assert upload[1]["pathname"] == "airbnb/images/" + key
    assert upload[2]["x-vercel-blob-access"] == "private"
    assert upload[2]["x-content-type"] == "image/png" and upload[3] == image
    assert store.get_image(key) == image
    assert requests[1][0].endswith("/airbnb/images/" + key)


def test_blob_image_store_rejects_oversize_and_unknown_types(monkeypatch):
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "vercel_blob_rw_store123_suffix_secret")
    store = BlobStore()
    with pytest.raises(SnapshotUnavailable, match="upload limit"):
        store.put_image(b"x" * (3 * 1024 * 1024 + 1), "image/png")
    with pytest.raises(SnapshotUnavailable, match="upload limit"):
        store.put_image(b"x", "image/svg+xml")
