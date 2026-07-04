from app.core.database import engine
from sqlalchemy import text, inspect

with engine.connect() as conn:
    # Check alembic version
    result = conn.execute(text("SELECT * FROM core.alembic_version"))
    print("Alembic version:", result.fetchall())
    
    # Check if proposals table exists
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema='core')
    print("\nTables in core schema:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    if 'proposals' in tables:
        print("\n✓ proposals table EXISTS")
        # Get columns
        columns = inspector.get_columns('proposals', schema='core')
        print("\nProposals columns:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
    else:
        print("\n✗ proposals table does NOT exist")
