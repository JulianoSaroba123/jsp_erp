"""
Handlers globais de exceções para FastAPI.
Intercepta exceções customizadas e retorna JSON padronizado.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError

from app.exceptions.errors import AppException
import logging

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """Registra todos os exception handlers no app FastAPI"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handler para exceções customizadas da aplicação"""
        request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"
        
        logger.error(f"[{request_id}] {exc.__class__.__name__}: {exc.message}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "request_id": request_id
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handler para erros de validação do Pydantic"""
        request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({
                "error": "ValidationError",
                "message": "Dados inválidos na requisição",
                "details": exc.errors(),
                "request_id": request_id
            })
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(request: Request, exc: IntegrityError):
        """Handler para erros de integridade do banco (ex: constraint violations)"""
        request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"
        
        logger.error(f"[{request_id}] IntegrityError: {str(exc.orig)}")
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "IntegrityError",
                "message": "Conflito de dados (constraint violation)",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handler genérico para exceções não tratadas"""
        request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"
        
        logger.exception(f"[{request_id}] Unhandled exception: {str(exc)}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "Erro interno do servidor",
                "request_id": request_id
            }
        )
