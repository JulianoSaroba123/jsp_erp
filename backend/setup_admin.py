"""
Script seguro para criar/resetar usuário admin inicial.

Credenciais padrão:
- Email: admin@jsp.com
- Senha: admin123
- Perfil: admin
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from app.security.password import hash_password, verify_password

# Carregar variáveis de ambiente
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL não configurada no arquivo .env")
    sys.exit(1)

# Conectar ao banco
engine = create_engine(DATABASE_URL)

print("=" * 70)
print("SCRIPT DE CONFIGURAÇÃO DO USUÁRIO ADMIN")
print("=" * 70)

with engine.connect() as conn:
    # Verificar se usuário admin já existe
    print("\n1️⃣ Verificando usuário admin@jsp.com...")
    
    result = conn.execute(text("""
        SELECT id, email, name, role, is_active, password_hash 
        FROM core.users 
        WHERE email = 'admin@jsp.com'
    """))
    user = result.fetchone()
    
    if user:
        print(f"   ✅ Usuário encontrado: {user.name} ({user.email})")
        print(f"   📋 Role: {user.role}")
        print(f"   🔓 Ativo: {'Sim' if user.is_active else 'Não'}")
        
        # Verificar se a senha é "admin123"
        print("\n2️⃣ Verificando senha...")
        
        if verify_password("admin123", user.password_hash):
            print("   ✅ Senha 'admin123' já está configurada corretamente!")
        else:
            print("   ⚠️ Senha atual NÃO é 'admin123' - atualizando...")
            
            # Atualizar senha para admin123
            new_hash = hash_password("admin123")
            
            conn.execute(text("""
                UPDATE core.users 
                SET password_hash = :password_hash 
                WHERE email = 'admin@jsp.com'
            """), {"password_hash": new_hash})
            
            conn.commit()
            
            print("   ✅ Senha atualizada com sucesso para 'admin123'")
        
        # Garantir que está ativo e é admin
        if user.role != 'admin' or not user.is_active:
            print("\n3️⃣ Ajustando permissões...")
            
            conn.execute(text("""
                UPDATE core.users 
                SET role = 'admin', is_active = true 
                WHERE email = 'admin@jsp.com'
            """))
            
            conn.commit()
            
            print("   ✅ Usuário configurado como admin ativo")
    
    else:
        print("   ❌ Usuário admin@jsp.com NÃO existe - criando...")
        
        # Criar novo usuário admin
        password_hash = hash_password("admin123")
        
        conn.execute(text("""
            INSERT INTO core.users (name, email, password_hash, role, is_active)
            VALUES ('Admin System', 'admin@jsp.com', :password_hash, 'admin', true)
        """), {"password_hash": password_hash})
        
        conn.commit()
        
        print("   ✅ Usuário admin@jsp.com criado com sucesso!")

print("\n" + "=" * 70)
print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 70)
print("")
print("📋 Credenciais de acesso:")
print("   Email: admin@jsp.com")
print("   Senha: admin123")
print("   Perfil: admin")
print("")
print("=" * 70)
