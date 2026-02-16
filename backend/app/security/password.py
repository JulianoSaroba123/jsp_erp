"""
Utilitários para hash e verificação de senhas
Usa bcrypt via passlib
"""
from passlib.context import CryptContext

# Contexto de criptografia (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Gera hash bcrypt de uma senha
    
    Args:
        password: senha em texto plano
    
    Returns:
        str: hash da senha (bcrypt)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se senha corresponde ao hash
    
    Args:
        plain_password: senha em texto plano
        hashed_password: hash armazenado no banco
    
    Returns:
        bool: True se senha correta
    """
    return pwd_context.verify(plain_password, hashed_password)
