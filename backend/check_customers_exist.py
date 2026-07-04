from sqlalchemy import create_engine, text, inspect

engine = create_engine('postgresql://jsp_user:jsp123456@localhost:5432/jsp_erp_test')
inspector = inspect(engine)

tables = inspector.get_table_names(schema='core')
print(f"Total tables in core schema: {len(tables)}")
print("\nTables:")
for table in sorted(tables):
    print(f"  - {table}")

if 'customers' in tables:
    print("\n✅ customers table EXISTS")
    columns = inspector.get_columns('customers', schema='core')
    print(f"   Columns: {len(columns)}")
else:
    print("\n❌ customers table DOES NOT EXIST")
