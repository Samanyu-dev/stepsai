from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """
    Assert that the health check endpoint returns 200 and matches the expected schema.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "environment" in data
    assert "uptime_seconds" in data

def test_root_endpoint():
    """
    Assert that the root endpoint directs API clients to the Interactive Documentation page.
    """
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "docs" in data
