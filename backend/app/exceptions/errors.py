"""
Exceções customizadas para o projeto.
Todas herdam de Exception base e incluem status_code HTTP.
"""

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
