"""
Steps AI Master Health Probe Tests.

This module asserts the correct operations of the main database connectivity SELECT probe.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_database_health_probe():
    """
    Assert that GET /health successfully probes the database and returns a healthy status.
    """
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "database" in data
    assert data["database"]["status"] == "healthy"
    assert data["database"]["error"] is None
