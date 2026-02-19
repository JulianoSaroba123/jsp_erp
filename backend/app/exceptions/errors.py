"""
Exceções customizadas para o projeto.
Todas herdam de Exception base e incluem status_code HTTP.
"""
import logging
from app.config import ENVIRONMENT, DEBUG

logger = logging.getLogger(__name__)


def sanitize_error_message(error: Exception, generic_message: str = "Erro interno do servidor") -> str:
    """
    Sanitiza mensagem de erro para não vazar informações em produção.
    
    Args:
        error: Exceção original
        generic_message: Mensagem genérica a retornar em produção
        
    Returns:
        Mensagem sanitizada
        
    Example:
        >>> try:
        ...     # código que pode falhar
        ... except Exception as e:
        ...     logger.error(f"Erro: {e}", exc_info=True)
        ...     detail = sanitize_error_message(e, "Erro ao processar pedido")
        ...     raise HTTPException(status_code=500, detail=detail)
    """
    # Sempre loga o erro completo (com stack trace)
    logger.error(f"Erro capturado: {error}", exc_info=True)
    
    # Em desenvolvimento ou debug, retornar detalhes
    if ENVIRONMENT == "development" or DEBUG:
        return f"{generic_message}: {str(error)}"
    
    # Em produção, retornar apenas mensagem genérica
    return generic_message


class AppException(Exception):
    """Exceção base da aplicação"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """Recurso não encontrado (404)"""
    def __init__(self, message: str = "Recurso não encontrado"):
        super().__init__(message, status_code=404)


class ConflictError(AppException):
    """Conflito de dados (409) - ex: email duplicado"""
    def __init__(self, message: str = "Conflito de dados"):
        super().__init__(message, status_code=409)


class ValidationError(AppException):
    """Erro de validação de negócio (422)"""
    def __init__(self, message: str = "Erro de validação"):
        super().__init__(message, status_code=422)


class UnauthorizedError(AppException):
    """Não autorizado (401)"""
    def __init__(self, message: str = "Não autorizado"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    """Acesso negado (403)"""
    def __init__(self, message: str = "Acesso negado"):
        super().__init__(message, status_code=403)
