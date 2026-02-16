"""
Tests for health check endpoint.

Tests:
- GET /health returns 200
- Response contains expected fields
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.smoke
def test_health_check(client: TestClient):
    """
    Test that health check endpoint returns 200 and correct status.
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "database" in data
    assert data["database"] == "healthy"
    assert "app" in data
    assert "version" in data


@pytest.mark.smoke
def test_health_check_no_auth_required(client: TestClient):
    """
    Test that health check doesn't require authentication.
    """
    response = client.get("/health")
    
    # Should succeed without Bearer token
    assert response.status_code == 200
    assert response.json()["database"] == "healthy"
