"""Current-profile saved homes."""
from fastapi import APIRouter
from ..dependencies import DB, User
from ..services.listings import listing_row, serialize_listing

router = APIRouter()

@router.get("/api/wishlists")
def wishlist(db: DB, user: User):
    return [
        serialize_listing(db, r)
        for r in db.execute(
            "SELECT l.* FROM listings l JOIN wishlists w ON w.listing_id=l.id WHERE w.user_id=? AND l.deleted=0",
            (user["id"],),
        )
    ]


@router.put("/api/wishlists/{id}")
def save(id: int, db: DB, user: User):
    listing_row(db, id)
    db.execute("INSERT OR IGNORE INTO wishlists VALUES(?,?)", (user["id"], id))
    db.commit()
    return {"saved": True}


@router.delete("/api/wishlists/{id}")
def unsave(id: int, db: DB, user: User):
    db.execute(
        "DELETE FROM wishlists WHERE user_id=? AND listing_id=?", (user["id"], id)
    )
    db.commit()
    return {"saved": False}


