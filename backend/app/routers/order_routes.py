"""
Router de Orders - endpoints HTTP.
Responsabilidade: receber requests e chamar OrderService.
NÃO contém lógica de negócio nem queries SQL.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.order_service import OrderService
from app.schemas.order_schema import OrderCreate, OrderCreateRequest, OrderOut
from app.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/orders", tags=["Orders"])


def get_db():
    """Dependency para obter sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", status_code=status.HTTP_200_OK)
def list_orders(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista pedidos com paginação.
    
    **Autenticação obrigatória (Bearer token)**
    
    Regras multi-tenant:
    - **admin**: vê todos os pedidos
    - **user, technician, finance**: vê apenas seus próprios pedidos
    
    Query params:
    - page: número da página (default 1, min 1)
    - page_size: itens por página (default 20, max 100)
    
    Response:
    {
      "items": [...],
      "page": 1,
      "page_size": 20,
      "total": 123
    }
    """
    try:
        # Multi-tenant: admin vê tudo, outros veem só os seus
        user_id_filter = None if current_user.role == "admin" else current_user.id
        
        result = OrderService.list_orders(
            db=db, 
            page=page, 
            page_size=page_size,
            user_id=user_id_filter
        )
        
        # Converte ORM models para OrderOut (Pydantic)
        items_out = [OrderOut.from_orm(order) for order in result["items"]]
        
        return {
            "items": items_out,
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"]
        }
    
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao listar pedidos")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderOut)
def create_order(
    order_data: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria novo pedido.
    
    **Autenticação obrigatória (Bearer token)**
    
    Regras multi-tenant:
    - O pedido será criado automaticamente para o usuário autenticado
    - user_id é obtido do token JWT (não pode ser fornecido no body)
    
    Body (OrderCreateRequest):
    - description: descrição (1-500 chars)
    - total: valor total (>= 0)
    
    Validações automáticas:
    - Pydantic valida tipos e constraints
    - Service valida regras de negócio
    """
    try:
        # Multi-tenant: user_id vem do token, não do body
        order = OrderService.create_order(
            db=db,
            user_id=current_user.id,  # Sempre usa ID do usuário autenticado
            description=order_data.description,
            total=float(order_data.total)
        )
        
        return OrderOut.from_orm(order)
    
    except ValueError as e:
        # Erros de validação de negócio (Service)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao criar pedido")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderOut)
def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),  # Adicionado para multi-tenant
    db: Session = Depends(get_db)
):
    """
    Busca pedido por ID.
    
    **Autenticação obrigatória (Bearer token)**
    
    Regras multi-tenant:
    - **admin**: pode ver qualquer pedido
    - **user, technician, finance**: só pode ver seus próprios pedidos
    """
    try:
        order = OrderService.get_order(db=db, order_id=order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {order_id} não encontrado"
            )
        
        # Validação multi-tenant: user só pode ver seus próprios pedidos
        if current_user.role != "admin" and order.user_id != current_user.id:
            # Retornar 404 em vez de 403 para não revelar existência do pedido
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {order_id} não encontrado"
            )
        
        return OrderOut.from_orm(order)
    
    except HTTPException:
        raise
    except Exception as e:
        # Sanitizar erro usando utilitário
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao buscar pedido")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
def delete_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove pedido por ID.
    
    **Autenticação obrigatória (Bearer token)**
    
    Regras multi-tenant:
    - **admin**: pode deletar qualquer pedido
    - **user, technician, finance**: só pode deletar seus próprios pedidos
    """
    try:
        is_admin = current_user.role == "admin"
        
        deleted = OrderService.delete_order(
            db=db, 
            order_id=order_id,
            user_id=current_user.id,
            is_admin=is_admin
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {order_id} não encontrado"
            )
        
        return {"ok": True}
    
    except ValueError as e:
        # Erro de permissão (tentou deletar pedido de outro usuário)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao deletar pedido")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
