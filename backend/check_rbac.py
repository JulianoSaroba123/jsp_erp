"""Script para verificar permissões RBAC"""
from app.database import SessionLocal
from app.models.role import Role
from app.models.user import User

db = SessionLocal()

print("\n=== ROLES E PERMISSIONS ===")
admin_role = db.query(Role).filter_by(name='admin').first()
user_role = db.query(Role).filter_by(name='user').first()

print(f"\nAdmin role has {len(admin_role.permissions)} permissions:")
products_perms_admin = [p for p in admin_role.permissions if p.resource == 'products']
for p in products_perms_admin:
    print(f"  products:{p.action}")

print(f"\nUser role has {len(user_role.permissions)} permissions:")
products_perms_user = [p for p in user_role.permissions if p.resource == 'products']
for p in products_perms_user:
    print(f"  products:{p.action}")

print("\n=== USUÁRIOS DE TESTE ===")
admin_user = db.query(User).filter_by(email='admin@test.com').first()
normal_user = db.query(User).filter_by(email='user@test.com').first()

if admin_user:
    print(f"\nadmin@test.com has {len(admin_user.roles)} roles:")
    for r in admin_user.roles:
        print(f"  - {r.name}")
    print(f"  has_permission('products', 'read'): {admin_user.has_permission('products', 'read')}")
else:
    print("\nadmin@test.com NOT FOUND")

if normal_user:
    print(f"\nuser@test.com has {len(normal_user.roles)} roles:")
    for r in normal_user.roles:
        print(f"  - {r.name}")
    print(f"  has_permission('products', 'read'): {normal_user.has_permission('products', 'read')}")
else:
    print("\nuser@test.com NOT FOUND")

db.close()
