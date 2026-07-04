"""
Limpa o banco de dados de teste
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://jsp_user:jsp123456@localhost:5432/jsp_erp_test"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE core.users CASCADE"))
    conn.execute(text("TRUNCATE TABLE core.roles CASCADE"))
    conn.execute(text("TRUNCATE TABLE core.permissions CASCADE"))
    conn.commit()
    print("✅ Database limpo!")
