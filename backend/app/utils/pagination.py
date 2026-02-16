"""
Utilitários para paginação
"""
from app.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def validate_pagination(page: int, page_size: int) -> tuple:
    """
    Valida e normaliza parâmetros de paginação
    
    Args:
        page: número da página (começa em 1)
        page_size: tamanho da página
    
    Returns:
        tuple (page, page_size) validados
    
    Raises:
        ValueError se parâmetros inválidos
    """
    if page < 1:
        raise ValueError("page deve ser >= 1")
    
    if page_size < 1:
        raise ValueError("page_size deve ser >= 1")
    
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE
    
    return page, page_size


def calculate_skip(page: int, page_size: int) -> int:
    """
    Calcula offset (skip) para query SQL
    
    Args:
        page: número da página (começa em 1)
        page_size: tamanho da página
    
    Returns:
        int: número de registros para pular (offset)
    """
    return (page - 1) * page_size


def paginate_response(items: list, page: int, page_size: int, total: int) -> dict:
    """
    Formata resposta paginada no padrão da API
    
    Args:
        items: lista de itens da página
        page: número da página atual
        page_size: tamanho da página
        total: total de registros
    
    Returns:
        dict com formato padrão:
        {
            "items": [...],
            "page": 1,
            "page_size": 20,
            "total": 123
        }
    """
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total
    }
