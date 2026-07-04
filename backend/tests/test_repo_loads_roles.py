"""
Teste mínimo para verificar se o problema é com eager loading ou sessão
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repo import UserRepository


def test_user_repo_loads_roles_correctly(
    db_session: Session,
    seed_user_normal: User
):
    """Verifica se UserRepository.get_by_id carrega roles corretamente"""
    # Buscar usuário via repository (simula o que get_current_user faz)
    repo = UserRepository(db_session)
    user_from_repo = repo.get_by_id(seed_user_normal.id)
    
    print(f"\n=== USER FROM REPO ===")
    print(f"User: {user_from_repo.email}")
    print(f"Roles loaded: {len(user_from_repo.roles)}")
    
    for role in user_from_repo.roles:
        print(f"  Role: {role.name}")
        print(f"    Permissions: {len(role.permissions)}")
        for perm in role.permissions[:3]:  # Primeiros 3
            print(f"      - {perm.resource}:{perm.action}")
    
    print(f"has_permission('products', 'read'): {user_from_repo.has_permission('products', 'read')}")
    
    # Assertions
    assert len(user_from_repo.roles) > 0, "User deve ter pelo menos 1 role"
    assert user_from_repo.has_permission('products', 'read'), "User deve ter products:read"
