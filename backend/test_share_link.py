"""
Script de teste para gerar share link de proposta
"""
from app.database import SessionLocal
from app.services.proposal_service import ProposalService
from sqlalchemy import text

db = SessionLocal()

try:
    # Buscar primeira proposta disponível
    result = db.execute(text("SELECT id, number FROM core.proposals LIMIT 1"))
    row = result.fetchone()
    
    if not row:
        print("❌ Nenhuma proposta encontrada no banco")
        print("   Crie uma proposta primeiro")
        exit(1)
    
    proposal_id = row[0]
    proposal_number = row[1]
    
    print(f"\n📋 Proposta encontrada: {proposal_number} (ID: {proposal_id})")
    print("\n🔗 Gerando link de compartilhamento...")
    
    # Gerar share link com expiração de 30 dias
    proposal = ProposalService.generate_share_link(
        db=db,
        proposal_id=proposal_id,
        expires_in_days=30
    )
    
    # Construir URL
    base_url = "http://localhost:8000"
    share_url = f"{base_url}/proposals/{proposal_id}/share/pdf?token={proposal.share_token}"
    
    print("\n✅ Link gerado com sucesso!")
    print(f"\n📱 URL de compartilhamento:")
    print(f"   {share_url}")
    print(f"\n🔑 Token: {proposal.share_token}")
    print(f"⏰ Expira em: {proposal.share_expires_at}")
    print(f"💚 Status: {'Ativo' if proposal.share_enabled else 'Inativo'}")
    
    print(f"\n🧪 Para testar, acesse:")
    print(f"   {share_url}")
    print(f"\nOu use curl:")
    print(f"   curl '{share_url}' --output proposta.pdf")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    db.close()
