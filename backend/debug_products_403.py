"""
Script manual para debugar o erro 403 em /products
"""
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.auth.security import hash_password, create_access_token

# Setup
db = SessionLocal()
client = TestClient(app)

# Create user with role
user = User(
    name='Debug User',
    email='debug@test.com',
    password_hash=hash_password('test123'),
    role='user',
    is_active=True
)
db.add(user)
db.flush()

# Assign RBAC role
user_role = db.query(Role).filter_by(name='user').first()
if user_role:
    user.roles.append(user_role)
    print(f"✓ Assigned role 'user' with {len(user_role.permissions)} permissions")

db.commit()
db.refresh(user)

print(f"\n=== USER INFO ===")
print(f"User ID: {user.id}")
print(f"User Email: {user.email}")
print(f"User RBAC Roles: {[r.name for r in user.roles]}")
print(f"has_permission('products', 'read'): {user.has_permission('products', 'read')}")

# Make request
token = create_access_token(subject=str(user.id))
headers = {'Authorization': f'Bearer {token}'}

print(f"\n=== REQUEST ===")
print(f"GET /products")
print(f"Headers: Authorization: Bearer {token[:30]}...")

response = client.get('/products', headers=headers)

print(f"\n=== RESPONSE ===")
print(f"Status: {response.status_code}")
print(f"Body: {response.json()}")

# Cleanup
db.delete(user)
db.commit()
db.close()
