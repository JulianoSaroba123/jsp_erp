"""
Teste direto de hash_password e verify_password.
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password_bytes)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password_bytes = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password_bytes, hashed_password)

# Testar
print("Gerando hash para '123456'...")
hash1 = hash_password("123456")
print(f"Hash: {hash1}")
print(f"Length: {len(hash1)}")

print("\nVerificando '123456' contra o hash...")
result = verify_password("123456", hash1)
print(f"Resultado: {result}")

print("\nVerificando senha errada '123457' contra o hash...")
result2 = verify_password("123457", hash1)
print(f"Resultado: {result2}")
