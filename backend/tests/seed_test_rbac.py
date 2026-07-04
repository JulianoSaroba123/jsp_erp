"""
Script auxiliar para popular RBAC no banco de testes.
Execute antes de rodar pytest se testes de RBAC falharem.
"""
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
import os


def get_test_database_url() -> str:
    """Get test database URL"""
    return os.getenv(
        "DATABASE_URL_TEST",
        "postgresql://jsp_user:jsp123456@localhost:5432/jsp_erp_test"
    )


def seed_test_permissions_and_roles():
    """Popula permissions e roles no banco de testes"""
    test_db_url = get_test_database_url()
    engine = create_engine(test_db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("Seeding RBAC for test database...")
        
        # Criar permissions básicas
        permissions_data = [
            # Orders
            ("orders", "read"), ("orders", "create"), ("orders", "update"), ("orders", "delete"),
            # Users  
            ("users", "read"), ("users", "create"), ("users", "update"), ("users", "delete"),
            # Financial
            ("financial", "read"), ("financial", "create"), ("financial", "update"), ("financial", "delete"),
            # Reports
            ("reports", "read"), ("reports", "export"),
            # Customers
            ("customers", "read"), ("customers", "create"), ("customers", "update"), ("customers", "delete"),
            # Suppliers
            ("suppliers", "read"), ("suppliers", "create"), ("suppliers", "update"), ("suppliers", "delete"),
            # Products
            ("products", "read"), ("products", "create"), ("products", "update"), ("products", "delete"),
        ]
        
        created_permissions = {}
        for resource, action in permissions_data:
            existing = db.query(Permission).filter_by(resource=resource, action=action).first()
            if not existing:
                perm = Permission(resource=resource, action=action, description=f"{action} {resource}")
                db.add(perm)
                db.flush()
                created_permissions[f"{resource}:{action}"] = perm
                print(f"  + Created permission: {resource}:{action}")
            else:
                created_permissions[f"{resource}:{action}"] = existing
                print(f"  = Permission exists: {resource}:{action}")
        
        db.commit()
        
        # Criar roles
        admin_role = db.query(Role).filter_by(name="admin").first()
        if not admin_role:
            admin_role = Role(name="admin", description="Admin with all permissions")
            db.add(admin_role)
            db.flush()
            print("  + Created role: admin")
        else:
            print("  = Role exists: admin")
        
        # Admin tem todas as permissões
        admin_role.permissions = list(created_permissions.values())
        
        user_role = db.query(Role).filter_by(name="user").first()
        if not user_role:
            user_role = Role(name="user", description="Standard user")
            db.add(user_role)
            db.flush()
            print("  + Created role: user")
        else:
            print("  = Role exists: user")
        
        # User tem acesso básico (read/create/update, sem delete)
        user_permissions = [
            created_permissions["orders:read"], created_permissions["orders:create"], created_permissions["orders:update"],
            created_permissions["financial:read"], created_permissions["financial:create"],
            created_permissions["reports:read"],
            created_permissions["customers:read"], created_permissions["customers:create"], created_permissions["customers:update"],
            created_permissions["products:read"], created_permissions["products:create"], created_permissions["products:update"],
        ]
        user_role.permissions = user_permissions
        
        db.commit()
        print("\nSeed completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\nError seeding RBAC: {e}")
        raise
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    seed_test_permissions_and_roles()
