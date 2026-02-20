"""
Utilitários para hash e verificação de senhas
Usa bcrypt via passlib
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    Gera hash bcrypt de uma senha.
    Usa bcrypt diretamente para compatibilidade com Python 3.11+.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se senha corresponde ao hash.
    Usa bcrypt diretamente para compatibilidade com Python 3.11+.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
