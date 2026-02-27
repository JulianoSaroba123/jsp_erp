"""
Arquivo de configuração centralizado do projeto.
Carrega variáveis do .env e define configurações globais.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# ENVIRONMENT
# ============================================================================
# Suporta ENV ou ENVIRONMENT (ENV tem prioridade para compatibilidade com staging)
ENVIRONMENT = os.getenv("ENV", os.getenv("ENVIRONMENT", "local")).lower()

# Normaliza 'local' para 'development'
if ENVIRONMENT == "local":
    ENVIRONMENT = "development"

if ENVIRONMENT not in ["development", "production", "test"]:
    raise ValueError(f"ENVIRONMENT inválido: '{ENVIRONMENT}'. Use 'local', 'development', 'test' ou 'production'.")

# ============================================================================
# DATABASE
# ============================================================================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL não encontrado no .env")

# ============================================================================
# SECURITY / JWT
# ============================================================================
# SECRET_KEY é OBRIGATÓRIO e não pode usar valor padrão inseguro
# EXCEÇÃO: Em ambiente de teste, permite SECRET_KEY determinística para testes
SECRET_KEY = os.getenv("SECRET_KEY")

if ENVIRONMENT == "test":
    # Em ambiente de teste, usa SECRET_KEY segura e determinística
    # Permite rodar pytest sem configurar SECRET_KEY manualmente
    if not SECRET_KEY:
        SECRET_KEY = "test_secret_key_for_pytest_deterministic_0123456789abcdef"
elif not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production":
    # Em development/production, SECRET_KEY forte é OBRIGATÓRIA
    raise ValueError(
        "SECRET_KEY não configurado ou usando valor padrão inseguro. "
        "Configure uma chave forte no .env. "
        "Gere com: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

ALGORITHM = "HS256"

# Expiração do token de acesso (em minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ============================================================================
# CORS
# ============================================================================
# Lista de origins permitidas (separadas por vírgula)
# Exemplo: "https://app.exemplo.com,https://admin.exemplo.com"
CORS_ALLOW_ORIGINS_STR = os.getenv("CORS_ALLOW_ORIGINS", "")

if ENVIRONMENT == "production":
    if not CORS_ALLOW_ORIGINS_STR or CORS_ALLOW_ORIGINS_STR.strip() == "":
        raise ValueError(
            "CORS_ALLOW_ORIGINS é obrigatório em produção. "
            "Configure no .env como: CORS_ALLOW_ORIGINS=https://dominio1.com,https://dominio2.com"
        )
    CORS_ALLOW_ORIGINS = [origin.strip() for origin in CORS_ALLOW_ORIGINS_STR.split(",") if origin.strip()]
else:
    # Em development e test, permitir localhost/127.0.0.1
    if CORS_ALLOW_ORIGINS_STR:
        CORS_ALLOW_ORIGINS = [origin.strip() for origin in CORS_ALLOW_ORIGINS_STR.split(",") if origin.strip()]
    else:
        CORS_ALLOW_ORIGINS = ["*"]  # Apenas em dev/test

# ============================================================================
# PAGINAÇÃO
# ============================================================================
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ============================================================================
# APP
# ============================================================================
APP_NAME = "ERP JSP"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
