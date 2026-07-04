"""Teste simplificado de share link - direto no banco"""
from app.database import engine
from sqlalchemy import text
import secrets
from datetime import datetime, timedelta

proposal_id = '27c95982-9b1f-4da0-8592-8dc8bb5511b0'

# Gerar token
share_token = secrets.token_urlsafe(48)[:64]
share_expires_at = datetime.utcnow() + timedelta(days=30)

print(f"\n🔑 Gerando token para proposta {proposal_id}...")
print(f"   Token: {share_token}")

with engine.begin() as conn:
    # Atualizar proposta com share token
    conn.execute(text("""
        UPDATE core.proposals
        SET share_token = :token,
            share_enabled = true,
            share_expires_at = :expires,
            share_created_at = now()
        WHERE id = :id
    """), {"token": share_token, "expires": share_expires_at, "id": proposal_id})
    
    print("✅ Token salvo no banco com sucesso!")
    
    # Verificar
    result = conn.execute(text("""
        SELECT number, share_token, share_enabled, share_expires_at
        FROM core.proposals
        WHERE id = :id
    """), {"id": proposal_id})
    
    proposal = result.fetchone()
    
    print(f"\n📋 Proposta: {proposal[0]}")
    print(f"🔑 Token: {proposal[1]}")
    print(f"💚 Ativo: {proposal[2]}")
    print(f"⏰ Expira em: {proposal[3]}")
    
    # Construir URL
    base_url = "http://localhost:8000"
    share_url = f"{base_url}/proposals/{proposal_id}/share/pdf?token={share_token}"
    
    print(f"\n📱 URL de compartilhamento:")
    print(f"   {share_url}")
    print(f"\n🧪 Para testar, acesse no navegador ou use curl:")
    print(f"   curl '{share_url}' --output proposta.pdf")
