"""
Utilitários JWT (preparação para implementação futura)
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Cria JWT access token
    
    Args:
        data: payload do token (ex: {"sub": "user_id"})
        expires_delta: tempo de expiração customizado
    
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodifica e valida JWT token
    
    Args:
        token: JWT string
    
    Returns:
        dict: payload decodificado
    
    Raises:
        JWTError: se token inválido/expirado
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
