"""Script temporário para adicionar colunas de compartilhamento"""
from app.database import engine
from sqlalchemy import text

print("\n🔧 Adicionando colunas de compartilhamento à tabela proposals...")

try:
    with engine.begin() as conn:
        # Adicionar colunas
        conn.execute(text(
            "ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS share_token VARCHAR(64)"
        ))
        print("✅ Coluna share_token adicionada")
        
        conn.execute(text(
            "ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS share_enabled BOOLEAN DEFAULT false"
        ))
        print("✅ Coluna share_enabled adicionada")
        
        conn.execute(text(
            "ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS share_expires_at TIMESTAMP"
        ))
        print("✅ Coluna share_expires_at adicionada")
        
        conn.execute(text(
            "ALTER TABLE core.proposals ADD COLUMN IF NOT EXISTS share_created_at TIMESTAMP"
        ))
        print("✅ Coluna share_created_at adicionada")
        
        # Criar índice único
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_proposals_share_token ON core.proposals(share_token)"
        ))
        print("✅ Índice único criado para share_token")
        
    print("\n✨ Colunas de compartilhamento adicionadas com sucesso!\n")
    
except Exception as e:
    print(f"\n❌ Erro: {e}\n")
    raise
