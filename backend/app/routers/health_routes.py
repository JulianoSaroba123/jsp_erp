"""
Router de health check
Não depende de services - consulta direta ao banco
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import APP_NAME, APP_VERSION, ENVIRONMENT
from app.security.deps import get_db


router = APIRouter(prefix="", tags=["Health"])


@router.get("/")
def root():
    """Rota raiz"""
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "running"
    }


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check com validação de conexão ao banco
    
    Retorna:
    - ok: True se DB está saudável, False caso contrário
    - service: Nome do serviço (jsp_erp)
    - env: Ambiente atual (development/production/test)
    - app: Nome da aplicação (legado)
    - version: Versão da aplicação
    - database: Status detalhado do banco
    """
    db_healthy = True
    db_status = "healthy"
    
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_healthy = False
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "ok": db_healthy,
        "service": "jsp_erp",
        "env": ENVIRONMENT,
        # Campos legados (manter compatibilidade)
        "app": APP_NAME,
        "version": APP_VERSION,
        "database": db_status
    }
