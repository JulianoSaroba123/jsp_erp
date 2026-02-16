"""
Tests for authentication endpoints.

Tests:
- POST /auth/login returns valid token
- GET /auth/me returns current user
- Invalid credentials return 401
- Token validation works correctly
"""

import pytest
from fastapi.testclient import TestClient
from app.models.user import User


@pytest.mark.auth
def test_login_success(client: TestClient, seed_user_normal: User):
    """
    Test successful login returns access token.
    """
    response = client.post(
        "/auth/login",
        data={
            "username": "user@test.com",
            "password": "testpass123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.auth
def test_login_invalid_credentials(client: TestClient, seed_user_normal: User):
    """
    Test login with wrong password returns 401.
    """
    response = client.post(
        "/auth/login",
        data={
            "username": "user@test.com",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 401


@pytest.mark.auth
def test_login_nonexistent_user(client: TestClient):
    """
    Test login with non-existent user returns 401.
    """
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@test.com",
            "password": "anypassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 401


@pytest.mark.auth
def test_auth_me_returns_current_user(
    client: TestClient,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test GET /auth/me returns authenticated user details.
    """
    response = client.get("/auth/me", headers=auth_headers_user)
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "user@test.com"
    assert data["name"] == "User Test"
    assert data["role"] == "user"
    assert "id" in data


@pytest.mark.auth
def test_auth_me_without_token_returns_401(client: TestClient):
    """
    Test GET /auth/me without token returns 401.
    """
    response = client.get("/auth/me")
    
    assert response.status_code == 401


@pytest.mark.auth
def test_auth_me_with_invalid_token_returns_401(client: TestClient):
    """
    Test GET /auth/me with invalid token returns 401.
    """
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_xyz"}
    )
    
    assert response.status_code == 401


@pytest.mark.auth
def test_register_creates_new_user(client: TestClient, db_session):
    """
    Test POST /auth/register creates new user.
    """
    response = client.post(
        "/auth/register",
        json={
            "name": "New User",
            "email": "newuser@test.com",
            "password": "securepass123",
            "role": "user"
        }
    )
    
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["name"] == "New User"
    assert data["role"] == "user"
    assert "id" in data


@pytest.mark.auth
def test_register_duplicate_email_returns_409(
    client: TestClient,
    seed_user_normal: User
):
    """
    Test registering duplicate email returns 409 Conflict.
    """
    response = client.post(
        "/auth/register",
        json={
            "name": "Another User",
            "email": "user@test.com",  # Already exists
            "password": "password123",
            "role": "user"
        }
    )
    
    assert response.status_code == 409
