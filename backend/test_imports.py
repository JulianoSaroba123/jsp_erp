"""Teste de Importação do Backend"""
try:
    print("=== TESTE DE IMPORTAÇÃO DO BACKEND ===\n")
    
    print("1. Importando app...")
    from app.main import app
    print("   ✅ App importado com sucesso\n")
    
    print("2. Verificando rotas de proposals...")
    proposal_routes = [r.path for r in app.routes if hasattr(r, 'path') and 'proposal' in r.path]
    print(f"   ✅ {len(proposal_routes)} rotas de proposals encontradas:")
    for route in proposal_routes[:8]:
        print(f"      • {route}")
    
    print("\n3. Verificando rotas de service-orders...")
    os_routes = [r.path for r in app.routes if hasattr(r, 'path') and 'service-order' in r.path]
    print(f"   ✅ {len(os_routes)} rotas de service-orders encontradas")
    
    print("\n4. Testando imports dos módulos novos...")
    from app.repositories.proposal_repository import ProposalRepository
    print("   ✅ ProposalRepository")
    
    from app.services.proposal_service import ProposalService
    print("   ✅ ProposalService")
    
    from app.routers.proposal_routes import router
    print("   ✅ ProposalRoutes")
    
    from app.schemas.proposal_schema import ProposalCreate
    print("   ✅ ProposalSchemas")
    
    print("\n" + "="*50)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("="*50)
    print("\n🚀 Backend pronto para iniciar!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
