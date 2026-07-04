import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema='core' 
          AND table_name='service_orders' 
        ORDER BY ordinal_position
    """)).fetchall()
    
    print("TODOS OS CAMPOS DA TABELA:\n")
    for r in result:
        print(f"  {r[0]}")
