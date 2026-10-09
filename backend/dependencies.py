"""Shared database and mock-identity dependencies for API routers."""

import sqlite3
from typing import Annotated
from fastapi import Depends, Header, HTTPException
from . import database


def get_db():
    db = database.connect()
    try:
        yield db
    finally:
        db.close()


DB = Annotated[sqlite3.Connection, Depends(get_db)]


def current_user(db: DB, x_demo_user: Annotated[int, Header()] = 1):
    row = db.execute("SELECT * FROM users WHERE id=?", (x_demo_user,)).fetchone()
    if not row:
        raise HTTPException(401, "Choose a valid demo profile.")
    return dict(row)


User = Annotated[dict, Depends(current_user)]


def require_host(user):
    if user["role"] != "host":
        raise HTTPException(403, "Switch to a host profile to manage listings.")
