"""
Script para testar acesso direto ao banco e identificar o erro 500
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Conexão com o banco
DATABASE_URL = "postgresql+psycopg://jsp_user:jsp123456@localhost:5433/jsp_erp"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

try:
    with Session() as db:
        # Testar query SQL direta
        print("Testando query SQL direta...")
        result = db.execute(text("SELECT * FROM public.settings LIMIT 1"))
        row = result.fetchone()
        
        if row:
            print(f"✓ Row encontrado: {type(row)}")
            print(f"✓ Colunas disponíveis: {row._fields if hasattr(row, '_fields') else 'N/A'}")
            
            # Testar acesso aos campos novos
            print("\nTestando acesso aos campos PDF:")
            try:
                header = row.pdf_header_text
                print(f"✓ pdf_header_text: {header[:50] if header else 'NULL'}...")
            except Exception as e:
                print(f"✗ pdf_header_text: ERRO ao acessar - {e}")
            
            try:
                footer = row.pdf_footer_text
                print(f"✓ pdf_footer_text: {footer[:50] if footer else 'NULL'}...")
            except Exception as e:
                print(f"✗ pdf_footer_text: ERRO ao acessar - {e}")
            
            try:
                message = row.default_proposal_message
                print(f"✓ default_proposal_message: {message[:50] if message else 'NULL'}...")
            except Exception as e:
                print(f"✗ default_proposal_message: ERRO ao acessar - {e}")
        else:
            print("✗ Nenhum dado encontrado na tabela settings")
            
except Exception as e:
    print(f"✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
