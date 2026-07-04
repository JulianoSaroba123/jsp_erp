"""Check if admin user exists"""
from sqlalchemy import create_engine, text
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(
        text('SELECT email, name, role, is_active FROM core.users WHERE email = :email'),
        {'email': 'admin@jsp.com'}
    )
    row = result.first()
    if row:
        print(f"✅ User found:")
        print(f"   Email: {row[0]}")
        print(f"   Name: {row[1]}")
        print(f"   Role: {row[2]}")
        print(f"   Active: {row[3]}")
    else:
        print("❌ User NOT found")
