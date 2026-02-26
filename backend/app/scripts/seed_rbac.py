"""
Script para criar roles e permissions iniciais (seeds)
Execute: python -m app.scripts.seed_rbac
"""
import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User


def seed_permissions(db: Session):
    """Cria permissões básicas do sistema"""
    
    permissions_data = [
        # Orders
        ("orders", "read", "Visualizar pedidos"),
        ("orders", "create", "Criar pedidos"),
        ("orders", "update", "Atualizar pedidos"),
        ("orders", "delete", "Deletar pedidos"),
        
        # Users
        ("users", "read", "Visualizar usuários"),
        ("users", "create", "Criar usuários"),
        ("users", "update", "Atualizar usuários"),
        ("users", "delete", "Deletar usuários"),
        
        # Financial
        ("financial", "read", "Visualizar lançamentos financeiros"),
        ("financial", "create", "Criar lançamentos financeiros"),
        ("financial", "update", "Atualizar lançamentos financeiros"),
        ("financial", "delete", "Deletar lançamentos financeiros"),
        
        # Reports
        ("reports", "read", "Visualizar relatórios"),
        ("reports", "export", "Exportar relatórios"),
    ]
    
    created_permissions = {}
    
    for resource, action, description in permissions_data:
        # Verificar se já existe
        existing = db.query(Permission).filter_by(
            resource=resource,
            action=action
        ).first()
        
        if existing:
            print(f"   ✓ Permission já existe: {resource}:{action}")
            created_permissions[f"{resource}:{action}"] = existing
        else:
            permission = Permission(
                resource=resource,
                action=action,
                description=description
            )
            db.add(permission)
            db.flush()  # Para obter o ID
            created_permissions[f"{resource}:{action}"] = permission
            print(f"   + Criada permission: {resource}:{action}")
    
    db.commit()
    return created_permissions


def seed_roles(db: Session, permissions: dict):
    """Cria roles e associa permissions"""
    
    # Role: admin (todas as permissões)
    admin_role = db.query(Role).filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(
            name="admin",
            description="Administrador com acesso total"
        )
        db.add(admin_role)
        db.flush()
        print("   + Criada role: admin")
    else:
        print("   ✓ Role já existe: admin")
    
    # Associar todas as permissões ao admin
    admin_role.permissions = list(permissions.values())
    
    # Role: user (permissões básicas - sem delete)
    user_role = db.query(Role).filter_by(name="user").first()
    if not user_role:
        user_role = Role(
            name="user",
            description="Usuário padrão com permissões limitadas"
        )
        db.add(user_role)
        db.flush()
        print("   + Criada role: user")
    else:
        print("   ✓ Role já existe: user")
    
    # Permissões para role user (read/create/update, sem delete)
    user_permissions = [
        permissions["orders:read"],
        permissions["orders:create"],
        permissions["orders:update"],
        permissions["financial:read"],
        permissions["financial:create"],
        permissions["reports:read"],
    ]
    user_role.permissions = user_permissions
    
    # Role: finance (foco em financeiro)
    finance_role = db.query(Role).filter_by(name="finance").first()
    if not finance_role:
        finance_role = Role(
            name="finance",
            description="Financeiro com acesso total a lançamentos"
        )
        db.add(finance_role)
        db.flush()
        print("   + Criada role: finance")
    else:
        print("   ✓ Role já existe: finance")
    
    # Permissões para role finance
    finance_permissions = [
        permissions["financial:read"],
        permissions["financial:create"],
        permissions["financial:update"],
        permissions["financial:delete"],
        permissions["reports:read"],
        permissions["reports:export"],
        permissions["orders:read"],  # Apenas leitura de orders
    ]
    finance_role.permissions = finance_permissions
    
    db.commit()
    
    return {
        "admin": admin_role,
        "user": user_role,
        "finance": finance_role
    }


def assign_roles_to_existing_users(db: Session, roles: dict):
    """Atribui roles aos usuários existentes baseado no campo 'role'"""
    
    users = db.query(User).all()
    
    for user in users:
        # Mapear role antigo (string) para nova role (objeto)
        role_name_map = {
            "admin": "admin",
            "user": "user",
            "finance": "finance",
            "technician": "user",  # technician vira user por padrão
        }
        
        target_role_name = role_name_map.get(user.role, "user")
        target_role = roles.get(target_role_name)
        
        if target_role and target_role not in user.roles:
            user.roles.append(target_role)
            print(f"   + Atribuída role '{target_role_name}' ao usuário {user.email}")
    
    db.commit()


def main():
    """Executa seeds de RBAC"""
    
    print("\n" + "="*60)
    print("  SEED RBAC - Roles e Permissions")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        print("[1/3] Criando permissions...")
        permissions = seed_permissions(db)
        print(f"   ✓ Total: {len(permissions)} permissions\n")
        
        print("[2/3] Criando roles...")
        roles = seed_roles(db, permissions)
        print(f"   ✓ Total: {len(roles)} roles\n")
        
        print("[3/3] Atribuindo roles aos usuários existentes...")
        assign_roles_to_existing_users(db, roles)
        print("   ✓ Usuários atualizados\n")
        
        print("="*60)
        print("  ✓ SEED COMPLETO")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
