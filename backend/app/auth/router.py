"""
Router de autenticação.
Endpoints: /auth/register, /auth/login, /auth/me
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.security.deps import get_db
from .service import AuthService
from .repository import UserRepository
from .security import create_access_token, decode_token
from app.models.user import User
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.exceptions.errors import ConflictError
from slowapi import Limiter
from slowapi.util import get_remote_address


router = APIRouter(prefix="/auth", tags=["autenticação"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# OAuth2 scheme para Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ============================================================================
# SCHEMAS (Pydantic)
# ============================================================================

class RegisterRequest(BaseModel):
    """Schema para registro de novo usuário"""
    email: EmailStr
    password: str = Field(min_length=6, max_length=128, description="Senha (mínimo 6 caracteres)")
    name: str = Field(min_length=3, max_length=150, description="Nome completo")
    role: str = Field(default="user", description="Papel do usuário (admin, user, technician, finance)")
    
    model_config = {"json_schema_extra": {
        "example": {
            "email": "novo@jsp.com",
            "password": "senha123",
            "name": "Novo Usuário",
            "role": "user"
        }
    }}


class UserResponse(BaseModel):
    """Schema de resposta com dados do usuário"""
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
    
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema de resposta do login"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============================================================================
# DEPENDENCY: Get Current User
# ============================================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obter usuário autenticado a partir do token JWT.
    
    Uso:
        @router.get("/rota-protegida")
        def rota(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    
    Raises:
        HTTPException 401: Se token inválido ou usuário não encontrado
    """
    try:
        # Decodificar token
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: subject (sub) não encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Converter para UUID
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: ID de usuário mal formatado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Buscar usuário no banco
        user = UserRepository.get_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inativo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except ValueError as e:
        # Erro de decode_token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
def register(
    request: Request,  # Necessário para rate limiting
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário no sistema.
    
    - **email**: Email único do usuário
    - **password**: Senha (mínimo 6 caracteres)
    - **name**: Nome completo
    - **role**: Papel (admin, user, technician, finance) - default: user
    
    Retorna os dados do usuário criado (sem senha).
    
    **Rate limit:** 3 tentativas por minuto por IP.
    """
    try:
        user = AuthService.register(
            db=db,
            email=data.email,
            password=data.password,
            name=data.name,
            role=data.role
        )
        return UserResponse.model_validate(user)
    
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        # Email duplicado = 409 Conflict (não 400)
        if "já cadastrado" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,  # Necessário para rate limiting
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autentica usuário e retorna token JWT.
    
    - **username**: Email do usuário
    - **password**: Senha
    
    Retorna token de acesso (JWT) e dados do usuário.
    
    **Nota:** OAuth2PasswordRequestForm usa "username" como campo,
    mas aqui interpretamos como email.
    
    **Rate limit:** 5 tentativas por minuto por IP.
    """
    try:
        # Autenticar (form_data.username contém o email)
        user = AuthService.authenticate(
            db=db,
            email=form_data.username,
            password=form_data.password
        )
        
        # Criar token JWT (subject = user.id) usando expiração do config
        access_token = create_access_token(
            subject=str(user.id),
            expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retorna dados do usuário autenticado.
    
    Requer autenticação (Bearer token).
    Útil para verificar se token ainda é válido.
    """
    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos os usuários ativos.
    
    Requer autenticação e permissão de administrador.
    
    **Restrito a:** admin
    """
    # Validar permissão: apenas admins
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores podem listar usuários."
        )
    
    users = UserRepository.get_all_active(db)
    return [UserResponse.model_validate(u) for u in users]
