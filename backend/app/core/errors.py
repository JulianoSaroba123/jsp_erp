"""
Utilitários para tratamento de erros e sanitização de mensagens em produção.

Em desenvolvimento: retorna detalhes completos do erro.
Em produção: retorna mensagem genérica para não vazar informações sensíveis.
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
