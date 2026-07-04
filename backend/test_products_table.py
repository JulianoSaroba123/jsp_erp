"""Test products table"""
from app.database import SessionLocal
from app.models.product import Product

db = SessionLocal()

try:
    products = db.query(Product).first()
    print('✅ Products table exists')
    print(f'Product: {products}')
except Exception as e:
    print(f'❌ Error: {type(e).__name__}: {e}')
finally:
    db.close()
