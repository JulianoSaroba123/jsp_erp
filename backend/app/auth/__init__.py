"""
Módulo de autenticação.

Fornece registro, login, JWT e controle de acesso.

Principais componentes:
- User: Modelo ORM de usuário (importado de app.models.user)
- router: Endpoints /auth/register, /auth/login, /auth/me
- get_current_user: Dependency para rotas protegidas
"""
from app.models.user import User  # Usa o modelo existente
from .router import router, get_current_user
from .service import AuthService
from .repository import UserRepository
from .security import hash_password, verify_password, create_access_token, decode_token

__all__ = [
    "User",
    "router",
    "get_current_user",
    "AuthService",
    "UserRepository",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_token",
]
