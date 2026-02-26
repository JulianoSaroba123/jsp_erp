"""Add RBAC tables

Revision ID: 004_add_rbac
Revises: 003
Create Date: 2026-02-25 10:00:00.000000

ETAPA 6 - RBAC (Role-Based Access Control)
===========================================

Esta migration adiciona suporte a RBAC:
- Tabela core.roles (funções/perfis)
- Tabela core.permissions (permissões por recurso/ação)
- Tabela core.user_roles (associação N:N entre users e roles)
- Tabela core.role_permissions (associação N:N entre roles e permissions)
- Índices otimizados para performance

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_rbac'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cria tabelas RBAC e índices.
    """
    
    # =====================================
    # 1. Tabela core.roles
    # =====================================
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='roles_pkey'),
        sa.UniqueConstraint('name', name='roles_name_key'),
        schema='core'
    )
    
    # =====================================
    # 2. Tabela core.permissions
    # =====================================
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='permissions_pkey'),
        sa.UniqueConstraint('resource', 'action', name='permissions_resource_action_key'),
        schema='core'
    )
    
    # =====================================
    # 3. Tabela core.user_roles (associação N:N)
    # =====================================
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], name='user_roles_user_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['core.roles.id'], name='user_roles_role_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id', name='user_roles_pkey'),
        schema='core'
    )
    
    # =====================================
    # 4. Tabela core.role_permissions (associação N:N)
    # =====================================
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['core.roles.id'], name='role_permissions_role_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['core.permissions.id'], name='role_permissions_permission_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id', name='role_permissions_pkey'),
        schema='core'
    )
    
    # =====================================
    # 5. Criar índices para performance
    # =====================================
    op.create_index(
        'idx_user_roles_user_id', 
        'user_roles', 
        ['user_id'], 
        unique=False, 
        schema='core'
    )
    
    op.create_index(
        'idx_user_roles_role_id', 
        'user_roles', 
        ['role_id'], 
        unique=False, 
        schema='core'
    )
    
    op.create_index(
        'idx_role_permissions_role_id', 
        'role_permissions', 
        ['role_id'], 
        unique=False, 
        schema='core'
    )
    
    op.create_index(
        'idx_role_permissions_permission_id', 
        'role_permissions', 
        ['permission_id'], 
        unique=False, 
        schema='core'
    )
    
    op.create_index(
        'idx_permissions_resource_action', 
        'permissions', 
        ['resource', 'action'], 
        unique=True, 
        schema='core'
    )


def downgrade():
    """
    Remove tabelas RBAC e índices.
    """
    
    # Drop índices
    op.drop_index('idx_permissions_resource_action', table_name='permissions', schema='core')
    op.drop_index('idx_role_permissions_permission_id', table_name='role_permissions', schema='core')
    op.drop_index('idx_role_permissions_role_id', table_name='role_permissions', schema='core')
    op.drop_index('idx_user_roles_role_id', table_name='user_roles', schema='core')
    op.drop_index('idx_user_roles_user_id', table_name='user_roles', schema='core')
    
    # Drop tabelas (ordem reversa, respeitando FKs)
    op.drop_table('role_permissions', schema='core')
    op.drop_table('user_roles', schema='core')
    op.drop_table('permissions', schema='core')
    op.drop_table('roles', schema='core')
