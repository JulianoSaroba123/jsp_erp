"""Test simple database query first"""
from app.database import SessionLocal
from app.models.settings import Settings
from sqlalchemy import inspect

db = SessionLocal()
try:
    print("Checking table structure...")
    inspector = inspect(db.get_bind())
    columns = [c['name'] for c in inspector.get_columns('settings', schema='public')]
    print(f"Columns in public.settings: {columns}")
    
    print("\nQuerying Settings...")
    settings = db.query(Settings).first()
    if settings:
        print(f"Found settings!")
        print(f"ID: {settings.id}")
        print(f"company_name: {settings.company_name}")
        print(f"city: {settings.city}")
        print(f"phones: {settings.phones}")
        print(f"values: {settings.values}")
    else:
        print("No settings found")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
