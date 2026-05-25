"""
Steps AI API Security & Authentication Module.

This module provides standard security headers checking using API Key Headers.
It enables simple yet robust authentication gates on backend endpoints.
"""

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependency check verifying X-API-Key header credentials.
    Bypassed if settings.REQUIRE_AUTH is configured to False.
    """
    if not settings.REQUIRE_AUTH:
        return ""
        
    if api_key == settings.API_KEY:
        return api_key if api_key else ""
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid, missing, or unauthorized X-API-Key header credential."
    )
