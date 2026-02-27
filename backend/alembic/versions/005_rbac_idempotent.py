"""RBAC: Create tables if missing (idempotent fix)

Revision ID: 005_rbac_idempotent
Revises: 004_add_rbac
Create Date: 2026-02-26 12:30:00.000000

ETAPA 6 - RBAC Idempotent Migration
====================================

Esta migration garante que as tabelas RBAC existam, mesmo se a migration 004
falhou em criá-las (workaround para issue de transações do Alembic).

Usa CREATE TABLE IF NOT EXISTS e CREATE INDEX IF NOT EXISTS para ser idempotente.

Reproduz exatamente a estrutura de:
- backend/app/models/role.py
- backend/app/models/permission.py
- backend/create_rbac_tables_manual.py (script manual que não será mais necessário)

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '005_rbac_idempotent'
down_revision = '004_add_rbac'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cria tabelas RBAC com IF NOT EXISTS (idempotente).
    
    Se as tabelas já existem (criadas manualmente ou por 004), nada acontece.
    Se não existem, serão criadas com a estrutura correta.
    """
    
    # Usar connection.execute(text()) para DDL raw com IF NOT EXISTS
    connection = op.get_bind()
    
    # =====================================
    # 1. Tabela core.roles
    # =====================================
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS core.roles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """))
    
    # =====================================
    # 2. Tabela core.permissions
    # =====================================
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS core.permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            resource VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT permissions_resource_action_key UNIQUE (resource, action)
        )
    """))
    
    # =====================================
    # 3. Tabela core.user_roles (associação N:N)
    # =====================================
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS core.user_roles (
            user_id UUID NOT NULL,
            role_id UUID NOT NULL,
            assigned_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, role_id),
            CONSTRAINT user_roles_user_id_fkey 
                FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE CASCADE,
            CONSTRAINT user_roles_role_id_fkey 
                FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE
        )
    """))
    
    # =====================================
    # 4. Tabela core.role_permissions (associação N:N)
    # =====================================
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS core.role_permissions (
            role_id UUID NOT NULL,
            permission_id UUID NOT NULL,
            assigned_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (role_id, permission_id),
            CONSTRAINT role_permissions_role_id_fkey 
                FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE,
            CONSTRAINT role_permissions_permission_id_fkey 
                FOREIGN KEY (permission_id) REFERENCES core.permissions(id) ON DELETE CASCADE
        )
    """))
    
    # =====================================
    # 5. Criar índices (IF NOT EXISTS requires PostgreSQL 9.5+)
    # =====================================
    
    # Note: PostgreSQL suporta CREATE INDEX IF NOT EXISTS a partir da versão 9.5
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_user_roles_user_id 
        ON core.user_roles(user_id)
    """))
    
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_user_roles_role_id 
        ON core.user_roles(role_id)
    """))
    
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id 
        ON core.role_permissions(role_id)
    """))
    
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id 
        ON core.role_permissions(permission_id)
    """))
    
    connection.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_permissions_resource_action 
        ON core.permissions(resource, action)
    """))


def downgrade():
    """
    Remove tabelas RBAC com IF EXISTS (seguro).
    
    Na ordem reversa para respeitar foreign keys.
    """
    
    connection = op.get_bind()
    
    # Drop índices (não precisa IF EXISTS pois DROP CASCADE cuida)
    connection.execute(text("DROP INDEX IF EXISTS core.idx_permissions_resource_action"))
    connection.execute(text("DROP INDEX IF EXISTS core.idx_role_permissions_permission_id"))
    connection.execute(text("DROP INDEX IF EXISTS core.idx_role_permissions_role_id"))
    connection.execute(text("DROP INDEX IF EXISTS core.idx_user_roles_role_id"))
    connection.execute(text("DROP INDEX IF EXISTS core.idx_user_roles_user_id"))
    
    # Drop tabelas (ordem reversa, respeitando FKs)
    connection.execute(text("DROP TABLE IF EXISTS core.role_permissions CASCADE"))
    connection.execute(text("DROP TABLE IF EXISTS core.user_roles CASCADE"))
    connection.execute(text("DROP TABLE IF EXISTS core.permissions CASCADE"))
    connection.execute(text("DROP TABLE IF EXISTS core.roles CASCADE"))
