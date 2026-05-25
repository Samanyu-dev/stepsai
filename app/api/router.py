"""
Steps AI Router Configuration Module.

This module consolidates all API sub-routers (health, resume parsing, interview
engine, and performance evaluation endpoints) under a unified FastAPI APIRouter structure.
"""

from fastapi import APIRouter
from app.api.v1 import health, resume, interview, evaluation

# Master router for all API endpoints
api_router = APIRouter()

# Register sub-routers under standard prefix
api_router.include_router(health.router, prefix="/v1")
api_router.include_router(resume.router, prefix="/v1/resume")
api_router.include_router(interview.router, prefix="/v1/interview")
api_router.include_router(evaluation.router, prefix="/v1")
