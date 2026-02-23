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
    Validates staging-ready format: ok, service, env + legacy fields.
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Staging-ready fields
    assert "ok" in data
    assert data["ok"] is True  # DB should be healthy in tests
    assert "service" in data
    assert data["service"] == "jsp_erp"
    assert "env" in data
    assert data["env"] in ["development", "test", "production"]
    
    # Legacy fields (backward compatibility)
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
    data = response.json()
    assert data["ok"] is True
    assert data["database"] == "healthy"
