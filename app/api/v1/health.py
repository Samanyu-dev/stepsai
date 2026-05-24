from fastapi import APIRouter
from app.core.config import settings
import time

router = APIRouter()

START_TIME = time.time()

@router.get("/health", tags=["System"])
def health_check():
    """
    Perform a system health check.
    Returns status, active environment configuration, and service uptime.
    """
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "uptime_seconds": round(time.time() - START_TIME, 2)
    }
