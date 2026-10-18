"""RoadGuard AI Backend Application Entry Point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from backend.api.router import api_router
from backend.app.config import settings
from backend.app.database import init_db

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("roadguard.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing RoadGuard database tables...")
    init_db()
    logger.info("Ensuring evidence storage path exists: %s", settings.evidence_storage_path)
    settings.evidence_storage_path.mkdir(parents=True, exist_ok=True)
    yield
    logger.info("RoadGuard backend shutdown.")


app = FastAPI(
    title="RoadGuard AI — Pothole Detection & Reporting API",
    description="Backend API providing event ingestion, persistence, reporting, and model integration boundaries.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS Middleware Configuration
# ---------------------------------------------------------------------------
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle malformed request validation errors with clear JSON response."""
    http_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
    return JSONResponse(
        status_code=http_422,
        content={
            "error": "ValidationError",
            "message": "The request body or parameters failed validation.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity constraint violations."""
    logger.warning("Database integrity error: %s", str(exc.orig))
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "ConflictError",
            "message": "Database constraint violation or duplicate record conflict.",
            "details": str(exc.orig),
        },
    )


# ---------------------------------------------------------------------------
# Top-level Routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    """Service metadata and navigation."""
    return {
        "service": "RoadGuard AI API",
        "version": "0.1.0",
        "status": "online",
        "documentation": "/docs",
        "health_check": "/api/health",
    }


@app.get("/health", tags=["Root"])
def root_health(request: Request):
    """Convenience alias to /api/health."""
    from backend.api.health import check_health
    from backend.app.database import SessionLocal

    db = SessionLocal()
    try:
        return check_health(db=db)
    finally:
        db.close()


# Mount main API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
