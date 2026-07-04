"""Verifica e reseta senha do admin"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from app.security.password import hash_password, verify_password

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Busca usuário
    result = conn.execute(text("SELECT id, email, password_hash FROM core.users WHERE email = 'admin@jsp.com'"))
    user = result.fetchone()
    
    if not user:
        print("❌ Usuário admin@jsp.com NÃO EXISTE!")
        exit(1)
    
    print(f"✅ Usuário encontrado: {user.email}")
    
    # Testa senha atual
    if verify_password("123456", user.password_hash):
        print("✅ Senha '123456' está correta!")
    else:
        print("❌ Senha '123456' está INCORRETA - resetando...")
        new_hash = hash_password("123456")
        conn.execute(text("""
            UPDATE core.users 
            SET password_hash = :password_hash 
            WHERE email = 'admin@jsp.com'
        """), {"password_hash": new_hash})
        conn.commit()
        print("✅ Senha resetada para '123456'")
