"""
Teste para verificar o fluxo completo de autenticação + RBAC em /products
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User


def test_get_products_with_user_token_full_flow(
    client: TestClient,
    seed_user_normal: User,
    auth_headers_user: dict,
    db_session: Session
):
    """
    Testa o fluxo completo: User autenticado GET /products
    """
    print(f"\n=== FULL FLOW TEST ===")
    print(f"User: {seed_user_normal.email}")
    print(f"User ID: {seed_user_normal.id}")
    print(f"User Roles: {[r.name for r in seed_user_normal.roles]}")
    print(f"has_permission('products', 'read'): {seed_user_normal.has_permission('products', 'read')}")
    print(f"Auth headers: {list(auth_headers_user.keys())}")
    
    # Fazer request
    client.headers.update(auth_headers_user)
    response = client.get("/products")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    # Assertions
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert "items" in data
    assert "total" in data
