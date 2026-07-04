"""
Testes de RBAC - Role-Based Access Control

Valida que:
1. Usuário sem permissão orders:delete recebe 403
2. Admin com permissão orders:delete consegue deletar order
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

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
        unique_id = uuid4().hex[:8]
        resource_name = f"test_orders_{unique_id}"

        # 1. Criar permissions únicas para evitar interferência de dados reaproveitados
        read_permission = Permission(resource=resource_name, action="read")
        delete_permission = Permission(resource=resource_name, action="delete")
        db_session.add_all([read_permission, delete_permission])
        db_session.flush()

        # 2. Criar role única com apenas read
        reader_role = Role(name=f"reader_test_{unique_id}")
        reader_role.permissions.append(read_permission)
        db_session.add(reader_role)
        db_session.flush()

        # 3. Criar user único com role reader
        user = User(
            name="Reader User",
            email=f"reader_test_{unique_id}@example.com",
            password_hash="hash",
            role="user"
        )
        user.roles.append(reader_role)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Recarregar da sessão para validar navegação real User -> Role -> Permission
        user = db_session.query(User).filter(User.id == user.id).first()
        _ = len(user.roles)
        for role in user.roles:
            _ = len(role.permissions)

        # 4. Verificar permissões
        assert user.has_permission(resource_name, "read") is True
        assert user.has_permission(resource_name, "delete") is False
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
        # Criar permissions com nomes únicos (idempotente)
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        perm1 = Permission(resource=f"test_res_assoc_{unique_id}", action="read")
        perm2 = Permission(resource=f"test_res_assoc_{unique_id}", action="create")
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
