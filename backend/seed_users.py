"""
Script para criar usuários iniciais com hash bcrypt compatível.

Executar:
    cd backend
    python seed_users.py

Requisitos:
- .env configurado com DATABASE_URL e SECRET_KEY
- Banco de dados já criado (via bootstrap_database ou docker-compose)

Comportamento:
- Idempotente: não duplica usuários existentes
- Hashes bcrypt compatíveis com passlib (mesmo algoritmo do auth/security.py)
- Cria 4 usuários padrão: admin, technician, finance, user

Variáveis de ambiente:
- DATABASE_URL: obrigatório (lido de .env via app.config)
- SEED_PASSWORD: opcional (default: "123456")
"""
import sys
import os

# Adicionar diretório backend ao path para importar módulos
sys.path.insert(0, os.path.dirname(__file__))

# Importar config para carregar .env e DATABASE_URL
from app.config import DATABASE_URL

# Importar hash bcrypt diretamente (sem SQLAlchemy models para evitar circular import)
from passlib.context import CryptContext
import psycopg

# Contexto de hash bcrypt (igual ao auth/security.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password_simple(password: str) -> str:
    """Hash bcrypt de senha (trunca para 72 bytes)."""
    password_bytes = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password_bytes)


def seed_users():
    """
    Cria usuários padrão se não existirem.
    
    Idempotente: pode ser executado múltiplas vezes sem duplicar.
    """
    
    # Ler senha padrão do ambiente (ou usar default)
    default_password = os.getenv("SEED_PASSWORD", "123456")
    
    # Conectar diretamente ao Postgres (sem SQLAlchemy para evitar circular import)
    # DATABASE_URL formato: postgresql+psycopg://user:pass@host:port/db
    # psycopg precisa: postgresql://user:pass@host:port/db
    conn_string = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Lista de usuários padrão (roles compatíveis com CHECK constraint)
                default_users = [
                    {
                        "name": "Admin JSP",
                        "email": "admin@jsp.com",
                        "password": default_password,
                        "role": "admin"
                    },
                    {
                        "name": "Técnico 1",
                        "email": "tec1@jsp.com",
                        "password": default_password,
                        "role": "technician"
                    },
                    {
                        "name": "Financ ieiro 1",
                        "email": "fin@jsp.com",
                        "password": default_password,
                        "role": "finance"
                    },
                    {
                        "name": "Usuário Padrão",
                        "email": "user@jsp.com",
                        "password": default_password,
                        "role": "user"
                    }
                ]
                
                print("🌱 Iniciando seed de usuários...")
                print()
                
                created = 0
                skipped = 0
                
                for user_data in default_users:
                    # Verificar se usuário já existe
                    cur.execute(
                        "SELECT id FROM core.users WHERE email = %s",
                        (user_data["email"],)
                    )
                    existing = cur.fetchone()
                    
                    if existing:
                        print(f"⏭️  {user_data['email']} - já existe, pulando")
                        skipped += 1
                        continue
                    
                    # Gerar hash bcrypt
                    password_hash = hash_password_simple(user_data["password"])
                    
                    # Inserir usuário
                    cur.execute(
                        """
                        INSERT INTO core.users (name, email, password_hash, role, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            user_data["name"],
                            user_data["email"],
                            password_hash,
                            user_data["role"],
                            True
                        )
                    )
                    
                    print(f"✅ {user_data['email']} - criado (role: {user_data['role']})")
                    created += 1
                
                # Commit transação
                conn.commit()
                
                print()
                print(f"📊 Resumo: {created} criados, {skipped} já existiam")
                print()
                
                # Listar todos os usuários
                print("📋 Usuários cadastrados:")
                cur.execute(
                    "SELECT name, email, role, is_active FROM core.users ORDER BY role, email"
                )
                users = cur.fetchall()
                
                for u in users:
                    name, email, role, is_active = u
                    status = "🟢" if is_active else "🔴"
                    print(f"  {status} {email:20s} | {name:20s} | {role}")
                
                print()
                print("✅ Seed concluído!")
                print()
                print("🔑 Credenciais padrão (desenvolvimento):")
                print("   Email: admin@jsp.com | Senha: 123456")
                print("   Email: tec1@jsp.com  | Senha: 123456")
                print("   Email: fin@jsp.com   | Senha: 123456")
                print("   Email: user@jsp.com  | Senha: 123456")
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    seed_users()
