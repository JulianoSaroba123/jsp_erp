"""Criar todas as tabelas RBAC manualmente (workaround para problema do Alembic)"""
from app.database import engine
from sqlalchemy import text

print("\n" + "=" * 60)
print("  CRIAÇÃO MANUAL DE TABELAS RBAC")
print("=" * 60 + "\n")

sql_commands = [
    # 1. Drop tabela roles se existe (da criação anterior)
    """
    DROP TABLE IF EXISTS core.roles CASCADE
    """,
    
    # 2. Criar tabela roles
    """
    CREATE TABLE core.roles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(50) NOT NULL UNIQUE,
        description VARCHAR(255),
        created_at TIMESTAMP NOT NULL DEFAULT now()
    )
    """,
    
    # 3. Criar tabela permissions
    """
    CREATE TABLE core.permissions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        resource VARCHAR(100) NOT NULL,
        action VARCHAR(50) NOT NULL,
        description VARCHAR(255),
        created_at TIMESTAMP NOT NULL DEFAULT now(),
        CONSTRAINT permissions_resource_action_key UNIQUE (resource, action)
    )
    """,
    
    # 4. Criar tabela user_roles (associação N:N)
    """
    CREATE TABLE core.user_roles (
        user_id UUID NOT NULL,
        role_id UUID NOT NULL,
        assigned_at TIMESTAMP NOT NULL DEFAULT now(),
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE
    )
    """,
    
    # 5. Criar tabela role_permissions (associação N:N)
    """
    CREATE TABLE core.role_permissions (
        role_id UUID NOT NULL,
        permission_id UUID NOT NULL,
        assigned_at TIMESTAMP NOT NULL DEFAULT now(),
        PRIMARY KEY (role_id, permission_id),
        FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE,
        FOREIGN KEY (permission_id) REFERENCES core.permissions(id) ON DELETE CASCADE
    )
    """,
    
    # 6-10. Criar índices
    """
    CREATE INDEX idx_user_roles_user_id ON core.user_roles(user_id)
    """,
    """
    CREATE INDEX idx_user_roles_role_id ON core.user_roles(role_id)
    """,
    """
    CREATE INDEX idx_role_permissions_role_id ON core.role_permissions(role_id)
    """,
    """
    CREATE INDEX idx_role_permissions_permission_id ON core.role_permissions(permission_id)
    """,
    """
    CREATE UNIQUE INDEX idx_permissions_resource_action ON core.permissions(resource, action)
    """,
]

try:
    with engine.begin() as conn:  # begin() para auto-commit
        for i, sql in enumerate(sql_commands, 1):
            try:
                conn.execute(text(sql))
                step_name = sql.strip().split('\n')[0].strip()
                print(f"[{i}/{len(sql_commands)}] ✓ {step_name[:50]}...")
            except Exception as e:
                print(f"[{i}/{len(sql_commands)}] ✗ ERRO: {e}")
                raise
    
    print("\n" + "=" * 60)
    print("  ✓ TODAS AS TABELAS RBAC CRIADAS COM SUCESSO")
    print("=" * 60 + "\n")
    
    # Verificar tabelas criadas
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'core' "
            "ORDER BY table_name"
        ))
        
        print("Tabelas no schema 'core':")
        for row in result:
            marker = "  [RBAC]" if row[0] in ['roles', 'permissions', 'user_roles', 'role_permissions'] else ""
            print(f"  - {row[0]}{marker}")
    
except Exception as e:
    print(f"\n✗ ERRO FATAL: {e}")
    raise
