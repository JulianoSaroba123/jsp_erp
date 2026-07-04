"""
Script para adicionar permissões CREATE/UPDATE/DELETE de proposals ao role financeiro
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal, Base
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.proposal import Proposal, ProposalItem, ProposalProduct
from app.models.product import Product
from app.models.customer import Customer

def grant_permissions():
    db = SessionLocal()
    try:
        # Buscar usuário financeiro
        user = db.query(User).filter(User.email == 'fin@jsp.com').first()
        if not user:
            print('[ERRO] Usuario fin@jsp.com nao encontrado')
            return
        
        print(f'[OK] Usuario: {user.email} (Roles: {[r.name for r in user.roles]})')
        
        # Pegar o primeiro role do usuário
        if not user.roles:
            print('[ERRO] Usuario nao tem roles associados')
            return
        
        role = user.roles[0]
        print(f'[OK] Role: {role.name}')
        
        # Permissões a adicionar
        permissions_to_add = [
            ('proposals', 'create', 'Criar propostas'),
            ('proposals', 'read', 'Ler propostas'),
            ('proposals', 'update', 'Atualizar propostas'),
            ('proposals', 'delete', 'Deletar propostas'),
        ]
        
        count = 0
        for resource, action, description in permissions_to_add:
            # Buscar ou criar permissão
            perm = db.query(Permission).filter(
                Permission.resource == resource,
                Permission.action == action
            ).first()
            
            if not perm:
                perm = Permission(resource=resource, action=action, description=description)
                db.add(perm)
                db.flush()
                print(f'[OK] Permissao {action} {resource} criada (ID: {perm.id})')
            else:
                print(f'[INFO] Permissao {action} {resource} ja existe (ID: {perm.id})')
            
            # Verificar se role já tem a permissão
            if perm not in role.permissions:
                role.permissions.append(perm)
                print(f'  [SUCESSO] Permissao {action} {resource} adicionada ao role {role.name}!')
                count += 1
            else:
                print(f'  [INFO] Role ja tinha a permissao {action} {resource}')
        
        db.commit()
        print(f'\n[CONCLUIDO] {count} permissoes adicionadas!')
        print('[ACAO] Recarregue a pagina (F5) para ver o botao + Nova Proposta')
        print('[OU] Faca logout e login novamente para atualizar permissoes')
    except Exception as e:
        print(f'[ERRO] {e}')
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    grant_permissions()
