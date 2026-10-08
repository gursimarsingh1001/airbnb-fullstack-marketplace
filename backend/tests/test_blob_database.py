"""Exercise real SQLite snapshots with an in-memory conditional object store."""
from threading import Lock
import pytest
from backend.blob_database import connect_snapshot, SnapshotConflict
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
