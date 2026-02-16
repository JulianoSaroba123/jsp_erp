"""
Main application - FastAPI setup
Responsabilidades:
- Criar app FastAPI
- Incluir routers
- Configurar middleware
- Configurar exception handlers
- NÃO contém lógica de negócio
- NÃO contém queries SQL
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import APP_NAME, APP_VERSION, DEBUG, ENVIRONMENT, CORS_ALLOW_ORIGINS
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import LoggingMiddleware
from app.exceptions.handlers import register_exception_handlers

# Routers
from app.routers import health_routes, user_routes, order_routes, financial_routes, report_routes
from app.auth import router as auth_router


# Configuração de logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITING (Slowapi)
# ============================================================================
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Cria aplicação FastAPI
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="ERP JSP - Sistema profissional com arquitetura em camadas",
    debug=DEBUG
)

# Registrar limiter no app state
app.state.limiter = limiter

# Handler customizado para rate limit exceeded
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handler para quando rate limit é excedido."""
    logger.warning(f"Rate limit excedido para IP: {get_remote_address(request)}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Muitas requisições. Tente novamente em alguns instantes.",
            "error": "rate_limit_exceeded"
        },
        headers={"Retry-After": "60"}
    )


# ========================================
# MIDDLEWARE (ordem importa!)
# ========================================

# 1. CORS (configuração segura baseada em ENVIRONMENT)
logger.info(f"Iniciando em modo: {ENVIRONMENT}")
logger.info(f"CORS allow_origins: {CORS_ALLOW_ORIGINS}")

# Em produção, NUNCA permitir "*" com credentials
allow_credentials = True
if CORS_ALLOW_ORIGINS == ["*"]:
    allow_credentials = False  # Obrigatório por spec CORS
    if ENVIRONMENT == "production":
        raise RuntimeError(
            "CORS mal configurado: allow_origins=['*'] não é permitido em produção com credentials. "
            "Configure CORS_ALLOW_ORIGINS no .env."
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# 2. Request ID (deve vir antes do logging)
app.add_middleware(RequestIDMiddleware)

# 3. Logging (usa request_id do middleware anterior)
app.add_middleware(LoggingMiddleware)


# ========================================
# EXCEPTION HANDLERS
# ========================================
register_exception_handlers(app)


# ========================================
# ROUTERS
# ========================================
app.include_router(health_routes.router)
app.include_router(auth_router)  # Autenticação (register, login, me)
app.include_router(user_routes.router)
app.include_router(order_routes.router)
app.include_router(financial_routes.router)  # ETAPA 3A: Financeiro
app.include_router(report_routes.router)  # ETAPA 4: Relatórios Financeiros


# ========================================
# STARTUP/SHUTDOWN EVENTS (opcional)
# ========================================

@app.on_event("startup")
async def startup_event():
    """Executa ao iniciar aplicação"""
    logging.info(f"🚀 {APP_NAME} v{APP_VERSION} iniciado")


@app.on_event("shutdown")
async def shutdown_event():
    """Executa ao desligar aplicação"""
    logging.info(f"🛑 {APP_NAME} desligado")
