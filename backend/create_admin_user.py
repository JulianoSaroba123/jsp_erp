"""Cria usuário admin direto"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from app.security.password import hash_password

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Verifica se já existe
    result = conn.execute(text("SELECT id FROM core.users WHERE email = 'admin@jsp.com'"))
    if result.fetchone():
        print("✅ Usuário admin@jsp.com já existe!")
    else:
        # Cria usuário
        password_hash = hash_password("123456")
        conn.execute(text("""
            INSERT INTO core.users (name, email, password_hash, role, is_active)
            VALUES ('Admin System', 'admin@jsp.com', :password_hash, 'admin', true)
        """), {"password_hash": password_hash})
        conn.commit()
        print("✅ Usuário admin@jsp.com criado com sucesso!")
        print("   Senha: 123456")
