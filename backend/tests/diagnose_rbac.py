"""
Script de diagnóstico para RBAC nos testes
"""
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.auth.security import hash_password
import os


def get_test_database_url() -> str:
    return os.getenv(
        "DATABASE_URL_TEST",
        "postgresql://jsp_user:jsp123456@localhost:5432/jsp_erp_test"
    )


def diagnose_rbac():
    test_db_url = get_test_database_url()
    engine = create_engine(test_db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("RBAC DIAGNOSTIC")
        print("=" * 60)
        
        # Check roles exist
        roles = db.query(Role).all()
        print(f"\n1. Roles in database: {len(roles)}")
        for role in roles:
            print(f"   - {role.name}: {len(role.permissions)} permissions")
        
        # Check permissions exist
        perms = db.query(Permission).all()
        print(f"\n2. Permissions in database: {len(perms)}")
        products_perms = [p for p in perms if p.resource == "products"]
        print(f"   - Products permissions: {len(products_perms)}")
        for p in products_perms:
            print(f"     * {p.resource}:{p.action}")
        
        # Check test users
        test_users = ["admin@test.com", "user@test.com"]
        print(f"\n3. Test users:")
        for email in test_users:
            user = db.query(User).filter_by(email=email).first()
            if user:
                print(f"   - {email}: {len(user.roles)} roles assigned")
                for role in user.roles:
                    print(f"     * Role: {role.name}")
                print(f"     has_permission('products', 'read'): {user.has_permission('products', 'read')}")
            else:
                print(f"   - {email}: NOT FOUND")
        
        print("\n" + "=" * 60)
        
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    diagnose_rbac()
