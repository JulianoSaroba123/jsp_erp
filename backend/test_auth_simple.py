"""
Teste de autenticação simples.
"""
from app.database import SessionLocal
from app.auth.service import AuthService

def test_auth():
    db = SessionLocal()
    
    try:
        print("Testando autenticação...")
        user = AuthService.authenticate(db, "admin@jsp.com", "123456")
        print(f"✅ LOGIN FUNCIONOU!")
        print(f"   Email: {user.email}")
        print(f"   Nome: {user.name}")
        print(f"   Role: {user.role}")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_auth()
