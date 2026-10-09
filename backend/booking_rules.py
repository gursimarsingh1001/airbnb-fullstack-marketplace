"""Shared date-only and integer-INR booking rules."""

from datetime import datetime, timezone, timedelta


def booking_today():
    """One documented day boundary for every deployment, independent of host TZ."""
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).date()


def price_quote(row, nights):
    subtotal = row["price"] * nights
    service = (subtotal * 14 + 50) // 100
    return dict(
        nights=nights,
        nightly_price=row["price"],
        subtotal=subtotal,
        cleaning_fee=row["cleaning_fee"],
        service_fee=service,
        total=subtotal + row["cleaning_fee"] + service,
        currency="INR",
    )


def stored_quote(row):
    from datetime import date

    nights = (date.fromisoformat(row["check_out"]) - date.fromisoformat(row["check_in"])).days
    return dict(
        nights=nights,
        nightly_price=row["nightly_price"],
        subtotal=row["nightly_price"] * nights,
        cleaning_fee=row["cleaning_fee"],
        service_fee=row["service_fee"],
        total=row["total"],
        currency="INR",
    )
