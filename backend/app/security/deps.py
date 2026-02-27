"""
Dependencies de segurança (preparação para implementação futura)
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.security.jwt import decode_access_token
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.exceptions.errors import UnauthorizedError


# Esquema de segurança Bearer Token
security_scheme = HTTPBearer()


def get_db():
    """Dependência de banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obter usuário autenticado
    
    Uso:
        @app.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    
    Raises:
        UnauthorizedError: se token inválido ou usuário não encontrado
    """
    try:
        # Decodifica token
        payload = decode_access_token(credentials.credentials)
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            raise UnauthorizedError("Token inválido")
        
        user_id = UUID(user_id_str)
        
    except Exception:
        raise UnauthorizedError("Token inválido ou expirado")
    
    # Busca usuário
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    
    if user is None:
        raise UnauthorizedError("Usuário não encontrado")
    
    if not user.is_active:
        raise UnauthorizedError("Usuário inativo")
    
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency para exigir role admin
    
    Uso:
        @app.delete("/users/{id}")
        def delete_user(user: User = Depends(require_admin)):
            # Só admin pode acessar
    
    Raises:
        ForbiddenError: se usuário não é admin
    """
    if current_user.role != "admin":
        from app.exceptions.errors import ForbiddenError
        raise ForbiddenError("Acesso restrito a administradores")
    
    return current_user


def require_permission(resource: str, action: str):
    """
    Factory de dependency para verificar permissão específica via RBAC.
    
    Retorna uma função dependency que verifica se o usuário tem a permissão.
    
    Usage:
        @router.delete("/orders/{id}")
        def delete_order(
            order_id: UUID,
            user: User = Depends(require_permission("orders", "delete"))
        ):
            ...
    
    Args:
        resource: nome do recurso (ex: 'orders', 'users')
        action: ação requerida (ex: 'read', 'create', 'update', 'delete')
    
    Returns:
        Dependency function que retorna o usuário se tiver permissão
        
    Raises:
        HTTPException 403: se usuário não tem a permissão
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        # Verificar se usuário tem a permissão via RBAC
        if not current_user.has_permission(resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado: permissão '{resource}:{action}' requerida"
            )
        return current_user
    
    return permission_checker
