"""
Steps AI Sliding Window Rate Limiter Module.

This module implements a thread-safe, in-memory sliding window rate limiter
to guard backend endpoints (e.g., resume uploads, interview turns) from excessive requests.
"""

import time
from fastapi import HTTPException, Request, status
from threading import Lock
from typing import Dict, List

class RateLimiter:
    """
    A lightweight, thread-safe in-memory rate limiter using a sliding window.
    """
    def __init__(self, requests_limit: int = 60, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history: Dict[str, List[float]] = {}
        self.lock = Lock()

    def __call__(self, request: Request):
        # Retrieve client IP, fallback to localhost if missing
        client_ip = "127.0.0.1"
        if request.client and request.client.host:
            client_ip = request.client.host
            
        now = time.time()
        
        with self.lock:
            # Fetch request history list for this client
            timestamps = self.history.get(client_ip, [])
            
            # Filter out older timestamps outside the current window
            timestamps = [t for t in timestamps if now - t < self.window_seconds]
            
            if len(timestamps) >= self.requests_limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests on this endpoint. Please slow down your requests rate."
                )
                
            # Record current request timestamp
            timestamps.append(now)
            self.history[client_ip] = timestamps

# Standard rate limiter definitions:
# Limit resume uploads to max 10 per minute per IP
upload_limiter = RateLimiter(requests_limit=10, window_seconds=60)
# Limit interview answers and starts to max 60 per minute per IP
interview_limiter = RateLimiter(requests_limit=60, window_seconds=60)
