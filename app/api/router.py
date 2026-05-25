from fastapi import APIRouter
from app.api.v1 import health, resume

# Master router for all API endpoints
api_router = APIRouter()

# Register sub-routers under standard prefix
api_router.include_router(health.router, prefix="/v1")
api_router.include_router(resume.router, prefix="/v1/resume")
