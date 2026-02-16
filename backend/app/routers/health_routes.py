"""
Router de health check
Não depende de services - consulta direta ao banco
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import SessionLocal
from app.config import APP_NAME, APP_VERSION


router = APIRouter(prefix="", tags=["Health"])


def get_db():
    """Dependência de banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
