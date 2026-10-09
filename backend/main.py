"""Application composition: lifecycle, middleware, errors and router registration."""
from contextlib import asynccontextmanager
from pathlib import Path
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from . import database
from .blob_database import SnapshotConflict, SnapshotUnavailable
from .routers import listings, bookings, host, wishlists, photos
from .routers.activities import router as activities_router


@asynccontextmanager
async def lifespan(app):
    database.initialize()
    yield


app = FastAPI(title="Airbnb Marketplace API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:3001,http://127.0.0.1:3001"
    ).split(","),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-Demo-User", "Idempotency-Key"],
)


@app.exception_handler(SnapshotConflict)
async def snapshot_conflict_handler(request, exc):
    return JSONResponse(status_code=409, content={"detail": "Another reservation or edit was saved just now. Please try again."})


@app.exception_handler(SnapshotUnavailable)
async def snapshot_unavailable_handler(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})



for router in (listings.router, bookings.router, host.router, wishlists.router, photos.router, activities_router):
    app.include_router(router)


# Production serves the Next.js static export and API from the same origin.
static_dir = Path(__file__).parent.parent / "frontend" / "out"
@app.get("/experiences", include_in_schema=False)
@app.get("/experiences/{aid}", include_in_schema=False)
@app.get("/services", include_in_schema=False)
@app.get("/services/{aid}", include_in_schema=False)
def activity_shell(aid: str = ""):
    return FileResponse(static_dir / "index.html")

if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
