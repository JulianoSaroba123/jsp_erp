import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

#Define a base para os modelos do SQLAlchemy
Base = declarative_base()

# 1. Carrega Variáveis do .env (se existir)
load_dotenv()
# 2. Lê a url do banco a partir do .env
#Exemplo Esperado:
# DATABASE_URL=postgresql+psycppg://jsp_user:lsp123456@localhost:5432/jsp_erp
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não encontrado. Crie/ajuste no .env do backend.")

# 3. Cria a engine(conexão base)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
#4 Fábrica de sessões (cada request usa uma sessão)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Função utilitária para obter uma sessão
def test_db_connection()-> None:
    """ Teste simples de conexão.
    Se der erro aqui, a URL, usuario e senha ou portas estão errados.
    """
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

