"""Appointment times use the demo's documented India timezone."""
from datetime import datetime, timedelta, timezone

def now_india():
    return datetime.now(timezone(timedelta(minutes=330))).replace(tzinfo=None)


