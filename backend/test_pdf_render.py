from app.security.deps import get_db
from app.services.proposal_service import ProposalService
from uuid import UUID
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# ID da proposta da imagem
proposal_id = "710a89c9-84f9-4ad5-a47a-96ae85460c1d"

try:
    db = next(get_db())
    
    print(f"\n=== TESTANDO PDF PROPOSTA {proposal_id} ===\n")
    
    # Busca proposta com relações
    print("1. Buscando proposta...")
    proposal = ProposalService.get_proposal(db, UUID(proposal_id), with_relations=True)
    print(f"   ✓ Proposta encontrada: {proposal.number} - {proposal.title}")
    
    # Verifica customer
    if proposal.customer:
        print(f"   ✓ Cliente: {proposal.customer.name}")
    else:
        print("   ⚠ Cliente não encontrado")
    
    # Verifica items
    if proposal.items:
        print(f"   ✓ Items: {len(proposal.items)}")
    else:
        print("   ⚠ Nenhum item")
    
    # Verifica products
    if proposal.products:
        print(f"   ✓ Products: {len(proposal.products)}")
    else:
        print("   ⚠ Nenhum product")
    
    # Configura Jinja2
    print("\n2. Configurando template...")
    template_dir = Path(__file__).parent / "app" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("proposal_pdf.html")
    print(f"   ✓ Template carregado de: {template_dir}")
    
    # Renderiza HTML
    print("\n3. Renderizando HTML...")
    html_content = template.render(
        proposal=proposal,
        now=datetime.now()
    )
    print(f"   ✓ HTML renderizado ({len(html_content)} bytes)")
    
    print("\n✅ TESTE CONCLUÍDO COM SUCESSO!\n")
    
except Exception as e:
    print(f"\n❌ ERRO: {type(e).__name__}")
    print(f"   Mensagem: {str(e)}")
    import traceback
    traceback.print_exc()
    print()
