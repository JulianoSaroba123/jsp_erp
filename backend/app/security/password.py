"""
Utilitários para hash e verificação de senhas
Usa bcrypt via passlib
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    Gera hash bcrypt de uma senha.
    Usa bcrypt diretamente para compatibilidade com Python 3.11+.
    
    Note: bcrypt has a maximum password length of 72 bytes.
    Longer passwords are automatically truncated to prevent runtime errors.
    """
    salt = bcrypt.gensalt()
    # Truncate to 72 bytes (bcrypt limitation)
    password_bytes = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se senha corresponde ao hash.
    Usa bcrypt diretamente para compatibilidade com Python 3.11+.
    
    Note: Truncates password to 72 bytes to match hash_password behavior.
    """
    # Truncate to 72 bytes (bcrypt limitation, must match hash_password)
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
