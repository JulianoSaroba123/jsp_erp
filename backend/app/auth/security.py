"""
Funções de segurança: hash de senhas e geração/validação de tokens JWT.

Este módulo centraliza toda a lógica de criptografia e autenticação,
usando bcrypt para senhas e JWT (HS256) para tokens de acesso.
"""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """
    Gera hash bcrypt de uma senha em texto plano.
    Usa bcrypt diretamente para compatibilidade com Python 3.11+.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde ao hash armazenado.
    Usa bcrypt diretamente para compatibilidade com Python 3.11+.
        
    Example:
        >>> verify_password("minhasenha123", "$2b$12$...")
        True
    
    Note:
        Bcrypt tem limite de 72 bytes. Trunca a senha antes de verificar.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


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
