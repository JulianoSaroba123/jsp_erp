"""
Router de health check
Não depende de services - consulta direta ao banco
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import APP_NAME, APP_VERSION
from app.security.deps import get_db  # CENTRALIZADO


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
    Única rota que pode fazer query direta (SELECT 1)
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "database": db_status
    }
