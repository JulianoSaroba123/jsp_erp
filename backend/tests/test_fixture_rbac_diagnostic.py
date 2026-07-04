"""
Teste de diagnóstico para verificar se fixtures estão atribuindo roles corretamente
"""
import pytest
from sqlalchemy.orm import Session
from app.models.user import User


def test_seed_user_admin_has_roles(db_session: Session, seed_user_admin: User):
    """Verifica se o admin criado pelo fixture tem roles RBAC"""
    print(f"\n\nAdmin User ID: {seed_user_admin.id}")
    print(f"Admin User Email: {seed_user_admin.email}")
    print(f"Admin User Role (string): {seed_user_admin.role}")
    print(f"Admin User Roles (RBAC): {len(seed_user_admin.roles)}")
    
    for role in seed_user_admin.roles:
        print(f"  - Role: {role.name} ({len(role.permissions)} permissions)")
    
    print(f"has_permission('products', 'read'): {seed_user_admin.has_permission('products', 'read')}")
    
    assert len(seed_user_admin.roles) > 0, "Admin deve ter pelo menos 1 role RF"
    assert seed_user_admin.has_permission('products', 'read'), " Admin deve ter permissão products:read"


def test_seed_user_normal_has_roles(db_session: Session, seed_user_normal: User):
    """Verifica se o user normal criado pelo fixture tem roles RBAC"""
    print(f"\n\nNormal User ID: {seed_user_normal.id}")
    print(f"Normal User Email: {seed_user_normal.email}")
    print(f"Normal User Role (string): {seed_user_normal.role}")
    print(f"Normal User Roles (RBAC): {len(seed_user_normal.roles)}")
    
    for role in seed_user_normal.roles:
        print(f"  - Role: {role.name} ({len(role.permissions)} permissions)")
    
    print(f"has_permission('products', 'read'): {seed_user_normal.has_permission('products', 'read')}")
    
    assert len(seed_user_normal.roles) > 0, "User deve ter pelo menos 1 role RBAC"
    assert seed_user_normal.has_permission('products', 'read'), "User deve ter permissão products:read"
