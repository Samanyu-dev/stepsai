"""
Steps AI Mock Interview Platform API Main Entrypoint.

This is the main module initializing the FastAPI application, CORS configuration,
registering lifecycle handlers, logging, and endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
from app.core.logging import setup_logging
from app.core.db import init_db

# Initialize structured logging
setup_logging()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# Initialize the FastAPI App with rich OpenAPI metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "An intelligent, end-to-end backend platform designed for the Steps AI National-Level Hackathon 2026. "
        "It automates resume parsing, interactive conversational mock interviews, and multi-dimensional "
        "performance grading with detailed suggestions and reports."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS (Cross-Origin Resource Sharing) Middlewares
# Enables frontend clients or browser tools to communicate with the backend
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the master router containing API paths under "/api" prefix
app.include_router(api_router, prefix="/api")

@app.get("/", include_in_schema=False)
def root_redirect():
    """
    Root endpoint offering greetings and guiding developers to interactive Swagger UI.
    """
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API. Please navigate to /docs to explore the interactive API schema.",
        "docs": "/docs"
    }

@app.get("/health", tags=["System"])
def health_check():
    """
    Perform a system health check verifying database SELECT connectivity.
    """
    from app.core.db import get_db_connection
    db_status = "unhealthy"
    db_error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        db_status = "healthy"
    except Exception as e:
        db_error = str(e)

    if db_status != "healthy":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail={"status": "unhealthy", "database": {"status": db_status, "error": db_error}}
        )

    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "database": {
            "status": db_status,
            "error": None
        }
    }

