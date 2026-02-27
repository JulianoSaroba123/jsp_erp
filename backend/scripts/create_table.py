"""Testar criação de tabela RBAC manualmente"""
from app.database import engine
from sqlalchemy import text

print("Tentando criar tabela core.roles manualmente...")

try:
    with engine.connect() as conn:
        # Testar criação da tabela roles
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS core.roles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(50) NOT NULL UNIQUE,
                description VARCHAR(255),
                created_at TIMESTAMP NOT NULL DEFAULT now()
            )
        """))
        conn.commit()
        print("✓ Tabela core.roles criada com sucesso!")
        
        # Verificar se foi criada
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'core' AND table_name = 'roles'"
        ))
        if result.fetchone():
            print("✓ Tabela core.roles existe agora!")
        else:
            print("✗ Tabela core.roles NÃO foi criada")
            
except Exception as e:
    print(f"✗ ERRO: {e}")
