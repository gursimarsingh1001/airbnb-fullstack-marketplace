"""Validated image upload and safe generated-key retrieval."""
import base64
import binascii
import re
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from ..dependencies import User, require_host
from ..blob_database import BlobStore, IMAGE_TYPES, MAX_IMAGE_BYTES
from ..schemas.homes import PhotoUploadInput

router = APIRouter()

def image_type(content):
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


@router.post("/api/host/photos", status_code=201)
def upload_host_photo(body: PhotoUploadInput, request: Request, user: User):
    require_host(user)
    try:
        content = base64.b64decode(body.content_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, "The uploaded image data is invalid.")
    if not content or len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Images must be 3 MB or smaller.")
    detected = image_type(content)
    if not detected or detected != body.content_type:
        raise HTTPException(415, "Choose a valid JPEG, PNG, or WebP image.")
    key = BlobStore().put_image(content, detected)
    url = str(request.base_url).rstrip("/") + "/api/photos/" + key
    return {"url": url, "content_type": detected, "size": len(content)}


@router.get("/api/photos/{key}")
def hosted_photo(key: str):
    if not re.fullmatch(r"[a-f0-9]{32}\.(jpg|png|webp)", key):
        raise HTTPException(404, "Image not found.")
    content_type = next(mime for mime, ext in IMAGE_TYPES.items() if key.endswith("." + ext))
    content = BlobStore().get_image(key)
    if content is None:
        raise HTTPException(404, "Image not found.")
    return Response(content, media_type=content_type, headers={
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
    })


