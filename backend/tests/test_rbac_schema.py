"""
Testes de schema RBAC - Validar que tabelas existem após migrations

Garante que migrations RBAC criem corretamente as tabelas:
- core.roles
- core.permissions
- core.user_roles
- core.role_permissions

E que índices/constraints esperados existam.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True, scope="function")
def clean_rbac_test_data(db_session: Session):
    """
    Limpa dados de teste RBAC antes de cada teste neste módulo.
    
    Remove apenas registros criados por testes (resource começando com 'test_'),
    preservando dados de seed necessários para outros testes.
    """
    yield  # Executa o teste primeiro
    
    # Cleanup após o teste
    db_session.execute(text("""
        DELETE FROM core.role_permissions 
        WHERE role_id IN (SELECT id FROM core.roles WHERE name LIKE 'test_%')
    """))
    db_session.execute(text("""
        DELETE FROM core.user_roles 
        WHERE role_id IN (SELECT id FROM core.roles WHERE name LIKE 'test_%')
    """))
    db_session.execute(text("DELETE FROM core.roles WHERE name LIKE 'test_%'"))
    db_session.execute(text("DELETE FROM core.permissions WHERE resource LIKE 'test_%'"))
    db_session.commit()


class TestRBACSchema:
    """Testes de estrutura do schema RBAC"""
    
    def test_rbac_tables_exist(self, db_session: Session):
        """
        Valida que as 4 tabelas RBAC existem no schema core
        
        Este teste garante que as migrations criaram corretamente:
        - core.roles
        - core.permissions
        - core.user_roles
        - core.role_permissions
        """
        result = db_session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'core' 
            AND table_name IN ('roles', 'permissions', 'user_roles', 'role_permissions')
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        
        expected_tables = ['permissions', 'role_permissions', 'roles', 'user_roles']
        assert tables == expected_tables, (
            f"Esperadas tabelas RBAC {expected_tables}, mas encontradas {tables}. "
            f"Execute: alembic upgrade head"
        )
    
    def test_roles_table_structure(self, db_session: Session):
        """Valida estrutura da tabela core.roles"""
        result = db_session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'core' AND table_name = 'roles'
            ORDER BY ordinal_position
        """))
        
        columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in result}
        
        # Validações essenciais
        assert 'id' in columns, "Coluna 'id' deve existir em core.roles"
        assert 'name' in columns, "Coluna 'name' deve existir em core.roles"
        assert 'description' in columns
        assert 'created_at' in columns
        
        assert columns['id']['type'] == 'uuid'
        assert columns['name']['type'] == 'character varying'
        assert columns['name']['nullable'] == 'NO', "name deve ser NOT NULL"
    
    def test_permissions_table_structure(self, db_session: Session):
        """Valida estrutura da tabela core.permissions"""
        result = db_session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'core' AND table_name = 'permissions'
            ORDER BY ordinal_position
        """))
        
        columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in result}
        
        # Validações essenciais
        assert 'id' in columns
        assert 'resource' in columns
        assert 'action' in columns
        assert 'description' in columns
        assert 'created_at' in columns
        
        assert columns['resource']['nullable'] == 'NO', "resource deve ser NOT NULL"
        assert columns['action']['nullable'] == 'NO', "action deve ser NOT NULL"
    
    def test_permissions_unique_constraint(self, db_session: Session):
        """Valida que existe UNIQUE(resource, action) em permissions"""
        result = db_session.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'core' 
            AND table_name = 'permissions'
            AND constraint_type = 'UNIQUE'
        """))
        
        constraints = [row[0] for row in result]
        
        # Deve existir constraint UNIQUE em (resource, action)
        assert any('resource_action' in c for c in constraints), (
            f"Constraint UNIQUE(resource, action) deve existir em permissions. "
            f"Constraints encontradas: {constraints}"
        )
    
    def test_user_roles_foreign_keys(self, db_session: Session):
        """Valida foreign keys da tabela user_roles"""
        result = db_session.execute(text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'core'
            AND tc.table_name = 'user_roles'
        """))
        
        fks = {row[1]: row[2] for row in result}  # {column: foreign_table}
        
        assert 'user_id' in fks, "user_id deve ter FK para users"
        assert 'role_id' in fks, "role_id deve ter FK para roles"
        assert fks['user_id'] == 'users'
        assert fks['role_id'] == 'roles'
    
    def test_role_permissions_foreign_keys(self, db_session: Session):
        """Valida foreign keys da tabela role_permissions"""
        result = db_session.execute(text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'core'
            AND tc.table_name = 'role_permissions'
        """))
        
        fks = {row[1]: row[2] for row in result}  # {column: foreign_table}
        
        assert 'role_id' in fks, "role_id deve ter FK para roles"
        assert 'permission_id' in fks, "permission_id deve ter FK para permissions"
        assert fks['role_id'] == 'roles'
        assert fks['permission_id'] == 'permissions'
    
    def test_rbac_indexes_exist(self, db_session: Session):
        """Valida que índices de performance existem"""
        result = db_session.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'core'
            AND indexname LIKE 'idx_%'
            AND tablename IN ('user_roles', 'role_permissions', 'permissions')
            ORDER BY indexname
        """))
        
        indexes = [row[0] for row in result]
        
        # Índices esperados (alguns podem ter nomes diferentes)
        expected_patterns = [
            'user_roles',  # idx_user_roles_user_id, idx_user_roles_role_id
            'role_permissions',  # idx_role_permissions_role_id, idx_role_permissions_permission_id
            'permissions'  # idx_permissions_resource_action
        ]
        
        for pattern in expected_patterns:
            matching = [idx for idx in indexes if pattern in idx]
            assert len(matching) > 0, (
                f"Deve existir pelo menos 1 índice para {pattern}. "
                f"Índices encontrados: {indexes}"
            )


class TestRBACIntegrity:
    """Testes de integridade referencial do RBAC"""
    
    def test_cannot_create_duplicate_permissions(self, db_session: Session):
        """Valida que não é possível criar permissions duplicadas (resource, action)"""
        from app.models.permission import Permission
        
        # Criar primeira permission
        perm1 = Permission(resource="test_dup", action="read")
        db_session.add(perm1)
        db_session.commit()
        
        # Tentar criar duplicada (deve falhar)
        perm2 = Permission(resource="test_dup", action="read")
        db_session.add(perm2)
        
        with pytest.raises(Exception) as exc_info:
            db_session.commit()
        
        # Deve ser erro de IntegrityError/UniqueViolation
        assert "unique" in str(exc_info.value).lower() or "duplicate" in str(exc_info.value).lower()
        
        db_session.rollback()
    
    def test_cascade_delete_role_removes_associations(self, db_session: Session):
        """Valida que deletar role remove associações (CASCADE)"""
        from app.models.role import Role
        from app.models.permission import Permission
        from sqlalchemy import select
        
        # Criar role e permission
        role = Role(name="test_cascade_role")
        perm = Permission(resource="test_cascade", action="read")
        role.permissions.append(perm)
        db_session.add(role)
        db_session.commit()
        
        role_id = role.id
        perm_id = perm.id
        
        # Verificar que associação existe
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM core.role_permissions
            WHERE role_id = :role_id AND permission_id = :perm_id
        """), {"role_id": role_id, "perm_id": perm_id})
        
        assert result.scalar() == 1, "Associação deve existir"
        
        # Deletar role
        db_session.delete(role)
        db_session.commit()
        
        # Verificar que associação foi removida (CASCADE)
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM core.role_permissions
            WHERE role_id = :role_id
        """), {"role_id": role_id})
        
        assert result.scalar() == 0, "Associação deve ter sido removida por CASCADE"
