"""
Teste simplificado para capturar detalhes do erro 500
"""
import pytest
from fastapi.testclient import TestClient
from app.models.user import User


def test_debug_500_error(
    client: TestClient,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """Debugar o erro 500 em detalhes"""
    client.headers.update(auth_headers_user)
    response = client.get("/products")
    
    print(f"\n=== RESPONSE DEBUG ===")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Text: {response.text[:500]}")  # Primeiros 500 caracteres
    
    try:
        json_data = response.json()
        print(f"JSON: {json_data}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
    
    # Assertion que vai falhar para mostrar output
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}. Response: {response.text}"
