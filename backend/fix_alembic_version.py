"""Insert version 008 into core.alembic_version"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # First, clear any existing versions in core.alembic_version
    conn.execute(text("DELETE FROM core.alembic_version"))
    
    # Insert version 008
    conn.execute(text("INSERT INTO core.alembic_version (version_num) VALUES ('008_add_products')"))
    
    conn.commit()
    
    # Verify
    result = conn.execute(text("SELECT version_num FROM core.alembic_version")).fetchone()
    if result:
        print(f'✅ Versão registrada em core.alembic_version: {result[0]}')
    else:
        print('❌ Erro: versão não foi inserida!')
