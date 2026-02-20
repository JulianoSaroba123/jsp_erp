"""
Funções de segurança: hash de senhas e geração/validação de tokens JWT.

Este módulo centraliza toda a lógica de criptografia e autenticação,
usando bcrypt para senhas e JWT (HS256) para tokens de acesso.
"""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


# Contexto de hash de senha (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Gera hash bcrypt de uma senha em texto plano.
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Hash bcrypt da senha
        
    Example:
        >>> hash_password("minhasenha123")
        '$2b$12$...'
    
    Note:
        Bcrypt tem limite de 72 bytes. Senhas maiores são truncadas.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde ao hash armazenado.
    
    Args:
        plain_password: Senha em texto plano fornecida pelo usuário
        hashed_password: Hash bcrypt armazenado no banco de dados
        
    Returns:
        True se a senha estiver correta, False caso contrário
        
    Example:
        >>> verify_password("minhasenha123", "$2b$12$...")
        True
    
    Note:
        Bcrypt tem limite de 72 bytes. Trunca a senha antes de verificar.
    """
    # Bcrypt tem limite de 72 bytes, truncar antes de verificar
    password_bytes = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(password_bytes, hashed_password)


def create_access_token(
    *, 
    subject: str, 
    expires_minutes: int | None = None
) -> str:
    """
    Cria um token JWT de acesso.
    
    Args:
        subject: Identificador do usuário (normalmente o user_id)
        expires_minutes: Minutos até expiração (usa ACCESS_TOKEN_EXPIRE_MINUTES se None)
        
    Returns:
        Token JWT codificado
        
    Example:
        >>> token = create_access_token(subject="123", expires_minutes=60)
        >>> print(token)  # 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    if expires_minutes is None:
        expires_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)
    
    payload = {
        "sub": subject,          # Subject: identificador do usuário
        "iat": int(now.timestamp()),      # Issued at: quando foi criado
        "exp": int(expire.timestamp()),   # Expiration: quando expira
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: Token JWT codificado
        
    Returns:
        Payload do token (dict com 'sub', 'iat', 'exp')
        
    Raises:
        ValueError: Se o token for inválido ou expirado
        
    Example:
        >>> payload = decode_token(token)
        >>> user_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Token inválido ou expirado: {str(e)}") from e
