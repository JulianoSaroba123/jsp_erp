"""
Script simples para resetar senhas dos usuários.
Usa bcrypt diretamente sem passlib.
"""
import bcrypt
import psycopg
import os
from app.config import DATABASE_URL

def reset_passwords():
    # Senha padrão
    password = "123456"
    
    # Gerar hash bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(password_bytes, salt)
    password_hash = hash_bytes.decode('utf-8')
    
    print(f"Hash gerado: {password_hash[:30]}...")
    
    # Conectar ao banco
    conn_string = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            # Atualizar todos os usuários
            cur.execute("""
                UPDATE core.users
                SET password_hash = %s
                WHERE email IN ('admin@jsp.com', 'tec1@jsp.com', 'fin@jsp.com')
            """, (password_hash,))
            
            count = cur.rowcount
            conn.commit()
            
            print(f"✅ {count} senhas atualizadas com sucesso!")
            print(f"   Senha para todos: {password}")

if __name__ == "__main__":
    reset_passwords()
