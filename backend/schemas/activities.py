"""Experience and service request contracts."""
from datetime import date, datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from ..activity_seed import EXPERIENCES, SERVICES
from ..services.activity_clock import now_india

Kind = Literal["experiences", "services"]

class ReservationInput(BaseModel):
    slot_id: int = Field(strict=True, ge=1)
    people: int = Field(strict=True, ge=1, le=30)
    expected_total: int | None = Field(None, strict=True, ge=1)


class SlotInput(BaseModel):
    day: date
    start_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    capacity: int = Field(strict=True, ge=1, le=30)


class ActivityInput(BaseModel):
    kind: Kind
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=30, max_length=5000)
    location: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=80)
    category: str
    price: int = Field(strict=True, ge=100, le=1000000)
    price_type: Literal["person", "group"] = "person"
    duration_minutes: int = Field(strict=True, ge=30, le=480)
    capacity: int = Field(strict=True, ge=1, le=30)
    language: Literal["English", "Hindi", "Italian", "Spanish", "Indonesian"] = (
        "English"
    )
    setting: Literal["Indoor", "Outdoor", "Either"] = "Either"
    service_location: Literal["At your stay", "Provider location", "Either"] = "Either"
    itinerary: str = Field(min_length=10, max_length=3000)
    included: str = Field(min_length=5, max_length=2000)
    requirements: str = Field(min_length=5, max_length=2000)
    photos: list[HttpUrl] = Field(min_length=1, max_length=12)
    slots: list[SlotInput] = Field(min_length=1, max_length=240)

    @field_validator(
        "title",
        "description",
        "location",
        "country",
        "itinerary",
        "included",
        "requirements",
        mode="before",
    )
    @classmethod
    def trim(cls, v):
        return v.strip() if isinstance(v, str) else v

    @model_validator(mode="after")
    def valid(self):
        categories = [
            r[0] for r in (EXPERIENCES if self.kind == "experiences" else SERVICES)
        ]
        if self.category not in categories:
            raise ValueError("Choose a valid category for this offering.")
        if self.kind == "experiences" and self.price_type != "person":
            raise ValueError("Experiences are priced per person.")
        if any(p.scheme != "https" for p in self.photos):
            raise ValueError("Use HTTPS photo URLs.")
        seen = set()
        for s in self.slots:
            start = datetime.fromisoformat(str(s.day) + "T" + s.start_time)
            if start <= now_india() or s.day > now_india().date() + timedelta(days=730):
                raise ValueError(
                    "Availability must be in the future, within two years."
                )
            if (start + timedelta(minutes=self.duration_minutes)).date() != s.day:
                raise ValueError("Sessions must end before midnight.")
            if s.capacity > self.capacity:
                raise ValueError("Slot capacity cannot exceed the offering capacity.")
            key = (s.day, s.start_time)
            if key in seen:
                raise ValueError("Availability contains duplicate time slots.")
            seen.add(key)
        return self


