"""
Middleware para logging de requests
Loga todas as requests com:
- request_id
- method, path
- status_code
- tempo de processamento
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Loga informações de cada request/response
    NUNCA loga dados sensíveis (senha, token, etc)
    """
    
    async def dispatch(self, request: Request, call_next):
        # Pega request_id (se RequestIDMiddleware estiver antes)
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Marca tempo de início
        start_time = time.time()
        
        # Processa request
        response = await call_next(request)
        
        # Calcula tempo de processamento
        process_time = time.time() - start_time
        
        # Log estruturado
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"| status={response.status_code} | time={process_time:.3f}s"
        )
        
        # Adiciona header com tempo de processamento
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        return response
