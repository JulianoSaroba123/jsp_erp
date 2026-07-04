"""Test se o backend carrega corretamente"""
import sys

try:
    print("Importando app...")
    from app.main import app
    print("✅ Backend importado com sucesso!")
    
    print("\nVerificando routers registrados...")
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    proposal_routes = [r for r in routes if 'proposal' in r.lower()]
    
    if proposal_routes:
        print(f"✅ {len(proposal_routes)} rotas de proposals encontradas:")
        for route in proposal_routes[:5]:  # Mostrar primeiras 5
            print(f"   {route}")
    else:
        print("⚠️  Nenhuma rota de proposals encontrada")
    
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Erro ao carregar backend: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
