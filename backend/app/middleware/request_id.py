"""
Middleware para Request ID
Gera UUID único para cada request (rastreabilidade)
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adiciona request_id único (UUID) em cada request
    Disponível em request.state.request_id
    Incluído no header de resposta: X-Request-ID
    """
    
    async def dispatch(self, request: Request, call_next):
        # Gera UUID único para esta request
        request_id = str(uuid.uuid4())
        
        # Armazena no request.state (acessível em handlers/logs)
        request.state.request_id = request_id
        
        # Processa request
        response = await call_next(request)
        
        # Adiciona header na resposta
        response.headers["X-Request-ID"] = request_id
        
        return response
