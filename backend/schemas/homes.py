"""Validated inputs for home listings, reservations and reviews."""
from datetime import date
from pydantic import BaseModel, Field, HttpUrl, field_validator

class BookingInput(BaseModel):
    listing_id: int = Field(strict=True, ge=1)
    check_in: date
    check_out: date
    guests: int = Field(strict=True, ge=1, le=16)
    expected_total: int | None = Field(default=None, strict=True, ge=1)


class ReviewInput(BaseModel):
    rating: int = Field(strict=True, ge=1, le=5)
    comment: str = Field(min_length=10, max_length=1000)

    @field_validator("comment", mode="before")
    @classmethod
    def trim_comment(cls, value):
        return value.strip() if isinstance(value, str) else value


class ListingInput(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=30, max_length=5000)
    location: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=80)
    category: str
    property_type: str
    price: int = Field(strict=True, ge=500, le=1000000)
    cleaning_fee: int = Field(default=900, strict=True, ge=0, le=100000)
    max_guests: int = Field(strict=True, ge=1, le=16)
    bedrooms: int = Field(strict=True, ge=1, le=20)
    beds: int = Field(strict=True, ge=1, le=30)
    bathrooms: int = Field(strict=True, ge=1, le=20)
    photos: list[HttpUrl] = Field(min_length=1, max_length=12)
    amenities: list[str] = Field(max_length=12)

    @field_validator("title", "description", "location", "country", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("category")
    @classmethod
    def valid_category(cls, value):
        if value not in [
            "Tropical",
            "Cabins",
            "Beachfront",
            "Amazing views",
            "Countryside",
            "Design",
            "Amazing pools",
            "Lakefront",
            "Tiny homes",
        ]:
            raise ValueError("Choose a valid category")
        return value

    @field_validator("property_type")
    @classmethod
    def valid_type(cls, value):
        if value not in ["Villa", "Cabin", "Cottage", "Apartment", "Tiny home"]:
            raise ValueError("Choose a valid property type")
        return value


class PhotoUploadInput(BaseModel):
    content_type: str = Field(pattern=r"^image/(jpeg|png|webp)$")
    content_base64: str = Field(min_length=1, max_length=4_194_304)


