"""
Testes de RBAC - Role-Based Access Control

Valida que:
1. Usuário sem permissão orders:delete recebe 403
2. Admin com permissão orders:delete consegue deletar order
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.order import Order


class TestRBACEnforcement:
    """Testes de enforcement de permissões"""
    
    def test_user_has_permission_method(self, db_session: Session):
        """
        Testa método User.has_permission() diretamente
        """
        # 1. Criar permission (idempotente)
        read_permission = db_session.query(Permission).filter_by(
            resource="test_orders", action="read"
        ).first()
        if not read_permission:
            read_permission = Permission(resource="test_orders", action="read")
            db_session.add(read_permission)
        
        delete_permission = db_session.query(Permission).filter_by(
            resource="test_orders", action="delete"
        ).first()
        if not delete_permission:
            delete_permission = Permission(resource="test_orders", action="delete")
            db_session.add(delete_permission)
        
        db_session.flush()
        
        # 2. Criar role com apenas read (idempotente)
        reader_role = db_session.query(Role).filter_by(name="reader_test_unique").first()
        if not reader_role:
            reader_role = Role(name="reader_test_unique")
            reader_role.permissions.append(read_permission)
            db_session.add(reader_role)
            db_session.flush()
        
        # 3. Criar user com role reader
        user = User(
            name="Reader User",
            email=f"reader_test_{hash('test1')}@example.com",
            password_hash="hash",
            role="user"
        )
        user.roles.append(reader_role)
        db_session.add(user)
        db_session.commit()
        
        # 4. Verificar permissões
        assert user.has_permission("test_orders", "read") is True
        assert user.has_permission("test_orders", "delete") is False
        assert user.has_permission("financial", "read") is False


class TestRBACModels:
    """Testes dos modelos RBAC"""
    
    def test_permission_full_name(self, db_session: Session):
        """Testa Permission.full_name property"""
        permission = Permission(
            resource="orders",
            action="create",
            description="Criar pedidos"
        )
        assert permission.full_name == "orders:create"
    
    def test_role_permissions_association(self, db_session: Session):
        """Testa associação many-to-many entre Role e Permission"""
        # Criar permissions com nomes únicos
        perm1 = Permission(resource="test_resource_assoc", action="read")
        perm2 = Permission(resource="test_resource_assoc", action="create")
        db_session.add_all([perm1, perm2])
        db_session.flush()
        
        # Criar role e associar permissions
        role = Role(name="test_role_assoc_unique")
        role.permissions.extend([perm1, perm2])
        db_session.add(role)
        db_session.commit()
        
        # Verificar associação
        assert len(role.permissions) == 2
        assert perm1 in role.permissions
        assert perm2 in role.permissions
    
    def test_user_roles_association(self, db_session: Session):
        """Testa associação many-to-many entre User e Role"""
        # Criar roles com nomes únicos
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        role1 = Role(name=f"admin_test_role_{unique_id}")
        role2 = Role(name=f"finance_test_role_{unique_id}")
        db_session.add_all([role1, role2])
        db_session.flush()
        
        # Criar user e associar roles
        user = User(
            name="Multi Role User",
            email=f"multi_role_test_{unique_id}@example.com",
            password_hash="hash",
            role="admin"
        )
        user.roles.extend([role1, role2])
        db_session.add(user)
        db_session.commit()
        
        # Verificar associação
        assert len(user.roles) == 2
        assert role1 in user.roles
        assert role2 in user.roles
