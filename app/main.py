import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import init_db
from app.api.routes_patients import router as patients_router
from app.api.routes_voice import router as voice_router
from app.api.routes_appointments import router as appointments_router
from app.api.routes_dashboard import router as dashboard_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("carecloud.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB on startup
    logger.info("Initializing persistent database...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down CareCloud Voice AI service.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Voice AI Patient Registration & Intake API with telephony integration, persistent DB, and dashboard.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for Pydantic validation errors (HTTP 422) returning standardized envelope
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{field}: {msg}")
    
    formatted_error = "; ".join(error_messages)
    logger.warning(f"Validation error on {request.url.path}: {formatted_error}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "data": None,
            "error": {
                "message": "Validation failed",
                "details": error_messages
            }
        }
    )

# Exception handler for Starlette / FastAPI HTTPExceptions returning standardized envelope
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "error": exc.detail
        }
    )

# Generic exception handler (500)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "data": None,
            "error": "An internal server error occurred."
        }
    )

# Mount Static Files
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include Routers
app.include_router(dashboard_router)
app.include_router(patients_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(appointments_router, prefix="/api")

# Also alias root /patients for direct PDF requirements (e.g. GET /patients, POST /patients)
app.include_router(patients_router)
app.include_router(appointments_router)

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"data": {"status": "healthy", "service": settings.PROJECT_NAME}, "error": None}
