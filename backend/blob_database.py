"""Durable SQLite snapshots for the zero-cost Vercel Hobby demo.

Each request reads the latest private snapshot, opens its own SQLite connection,
and publishes writes with an ETag compare-and-swap. A stale writer gets a conflict
instead of overwriting another reservation. This is intentionally for a small
assignment dataset, not a substitute for a database server at production scale.

Wire headers follow Vercel's official Blob SDK (put-helpers.ts and get.ts).
"""

import os
import sqlite3
import tempfile
import hashlib
from pathlib import Path
from uuid import uuid4

import httpx

PATHNAME = "airbnb/database.sqlite"
MAX_DATABASE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_BYTES = 3 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class SnapshotConflict(Exception):
    pass


class SnapshotUnavailable(Exception):
    pass


class BlobStore:
    def __init__(self):
        self.token = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
        if not self.token:
            raise SnapshotUnavailable("Private database storage is not connected.")
        # Standard Blob tokens encode the store identifier as their fourth part.
        parts = self.token.split("_")
        if len(parts) < 5 or parts[:3] != ["vercel", "blob", "rw"]:
            raise SnapshotUnavailable("Invalid database storage configuration.")
        self.store_id = parts[3]
        self.url = f"https://{self.store_id.lower()}.private.blob.vercel-storage.com/{PATHNAME}"

    def put_image(self, content, content_type):
        if len(content) > MAX_IMAGE_BYTES or content_type not in IMAGE_TYPES:
            raise SnapshotUnavailable("Image exceeds the demo upload limit or has an unsupported type.")
        key = f"{uuid4().hex}.{IMAGE_TYPES[content_type]}"
        pathname = f"airbnb/images/{key}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "x-api-version": "12",
            "x-vercel-blob-store-id": self.store_id,
            "x-vercel-blob-access": "private",
            "x-content-type": content_type,
            "x-add-random-suffix": "0",
            "x-allow-overwrite": "0",
            "x-cache-control-max-age": "31536000",
        }
        try:
            response = httpx.put(
                "https://blob.vercel-storage.com",
                params={"pathname": pathname},
                headers=headers,
                content=content,
                timeout=20,
            )
            response.raise_for_status()
            try:
                uploaded = response.json()
            except ValueError as exc:
                raise SnapshotUnavailable("Image storage did not confirm the upload.") from exc
            if not uploaded.get("url"):
                raise SnapshotUnavailable("Image storage did not confirm the upload.")
            return key
        except httpx.HTTPError as exc:
            raise SnapshotUnavailable("Image storage is temporarily unavailable.") from exc

    def get_image(self, key):
        content_type = next((mime for mime, ext in IMAGE_TYPES.items() if key.endswith("." + ext)), None)
        if not content_type:
            return None
        pathname = f"airbnb/images/{key}"
        url = f"https://{self.store_id.lower()}.private.blob.vercel-storage.com/{pathname}"
        try:
            response = httpx.get(
                url,
                params={"cache": "0"},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=20,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            if len(response.content) > MAX_IMAGE_BYTES:
                raise SnapshotUnavailable("Stored image exceeds the demo upload limit.")
            return response.content
        except httpx.HTTPError as exc:
            raise SnapshotUnavailable("Image storage is temporarily unavailable.") from exc

    def read(self):
        try:
            response = httpx.get(
                self.url,
                params={"cache": "0"},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=20,
            )
            if response.status_code == 404:
                return None, None
            response.raise_for_status()
            if len(response.content) > MAX_DATABASE_BYTES:
                raise SnapshotUnavailable("Demo database storage limit reached.")
            etag = response.headers.get("etag")
            if not etag:
                raise SnapshotUnavailable("Database version could not be verified.")
            return response.content, etag
        except httpx.HTTPError as exc:
            raise SnapshotUnavailable("Database storage is temporarily unavailable.") from exc

    def write(self, content, etag):
        if len(content) > MAX_DATABASE_BYTES:
            raise SnapshotUnavailable("Demo database storage limit reached.")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "x-api-version": "12",
            "x-vercel-blob-store-id": self.store_id,
            "x-vercel-blob-access": "private",
            "x-content-type": "application/vnd.sqlite3",
            "x-add-random-suffix": "0",
            "x-allow-overwrite": "1" if etag else "0",
            "x-cache-control-max-age": "60",
        }
        if etag:
            headers["x-if-match"] = etag
        try:
            response = httpx.put(
                "https://blob.vercel-storage.com",
                params={"pathname": PATHNAME},
                headers=headers,
                content=content,
                timeout=25,
            )
            if response.status_code in (409, 412):
                raise SnapshotConflict("The database changed. Please try again.")
            if response.status_code == 400 and "already exists" in response.text.lower():
                raise SnapshotConflict("The database was initialized by another request.")
            response.raise_for_status()
            result = response.json()
            if not result.get("etag"):
                raise SnapshotUnavailable("Database write version could not be verified.")
            return result["etag"]
        except httpx.HTTPError as exc:
            raise SnapshotUnavailable("Your change could not be saved. Please try again.") from exc


class SnapshotConnection(sqlite3.Connection):
    def commit(self):
        super().commit()
        content = self._snapshot_path.read_bytes()
        digest = hashlib.sha256(content).digest()
        # total_changes ignores DDL and includes rolled-back rows. The committed
        # file hash correctly covers migrations, new databases, and real writes.
        if digest != self._saved_digest:
            self._etag = self._store.write(content, self._etag)
            self._saved_digest = digest

    def close(self):
        super().close()
        self._snapshot_path.unlink(missing_ok=True)

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False


def connect_snapshot(store=None):
    store = store or BlobStore()
    content, etag = store.read()
    path = Path(tempfile.gettempdir()) / f"airbnb-{uuid4().hex}.sqlite"
    if content is not None:
        path.write_bytes(content)
    db = sqlite3.connect(path, check_same_thread=False, factory=SnapshotConnection)
    db._snapshot_path = path
    db._store = store
    db._etag = etag
    db._saved_digest = hashlib.sha256(content or b"").digest()
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = DELETE")
    if content is None:
        db._saved_digest = hashlib.sha256(path.read_bytes()).digest()
    return db
