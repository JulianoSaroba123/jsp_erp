"""Check all users in database"""
from sqlalchemy import create_engine, text
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM core.users'))
    count = result.scalar()
    print(f"Total users in database: {count}")
    
    if count > 0:
        result = conn.execute(text('SELECT email, name, role FROM core.users LIMIT 10'))
        print("\nExisting users:")
        for row in result:
            print(f"  - {row[0]} ({row[1]}) - Role: {row[2]}")
