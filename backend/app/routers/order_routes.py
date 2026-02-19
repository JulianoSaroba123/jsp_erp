"""
Router de Orders - endpoints HTTP.
Responsabilidade: receber requests e chamar OrderService.

 contém lógica de negócio nem queries SQL.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.services.order_service import OrderService
from app.schemas.order_schema import OrderCreate, OrderCreateRequest, OrderOut, OrderUpdate
from app.security.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.exceptions.errors import ConflictError, NotFoundError, ValidationError


router = APIRouter(prefix="/orders", tags=["Orders"])


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


@router.patch("/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderOut)
def update_order(
    order_id: UUID,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza pedido existente (PATCH).
    
    **Autenticação obrigatória (Bearer token)**
    
    Body (OrderUpdate - todos os campos opcionais):
    - description: Nova descrição (opcional)
    - total: Novo total (opcional, sincroniza com financeiro)
    
    **Regras de sincronização financeira:**
    1. Financial pending + total alterado: Atualiza amount
    2. Financial paid + total alterado: BLOQUEIA (400)
    3. Financial canceled + total > 0: REABRE para pending
    4. Total = 0 + pending financial: CANCELA financial
    5. Sem financial + total > 0: CRIA financial idempotente
    
    **Multi-tenant:**
    - User só pode atualizar seus próprios pedidos
    - Admin pode atualizar qualquer pedido
    - Anti-enumeration: 404 se pedido não existe ou não pertence ao user
    """
    try:
        # Admin pode atualizar qualquer pedido, user comum só seus próprios
        user_id_filter = current_user.id if current_user.role != "admin" else None
        
        # Se admin, buscar order e usar user_id do owner
        if current_user.role == "admin":
            order = OrderService.get_order(db=db, order_id=order_id)
            if not order:
                raise NotFoundError("Pedido não encontrado")
            user_id_filter = order.user_id
        
        updated_order = OrderService.update_order(
            db=db,
            order_id=order_id,
            user_id=user_id_filter,
            description=order_data.description,
            total=order_data.total
        )
        
        return OrderOut.from_orm(updated_order)
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao atualizar pedido")
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
    
    except ConflictError as e:
        # Erro de regra de negócio (ex: lançamento financeiro paid = não pode deletar)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
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


@router.post("/{order_id}/restore", status_code=status.HTTP_200_OK)
def restore_order(
    order_id: UUID,
    current_user: User = Depends(require_admin),  # Apenas admin pode restaurar
    db: Session = Depends(get_db)
):
    """
    Restaura pedido soft-deleted (apenas admin).
    
    **Autenticação obrigatória: ADMIN role**
    
    Path params:
    - order_id: UUID do pedido a restaurar
    
    Returns:
        OrderOut: Pedido restaurado
        
    Raises:
        404: Pedido não encontrado ou não está deletado
        403: Usuário não é admin
    """
    from app.repositories.order_repository import OrderRepository
    
    try:
        # Busca pedido incluindo soft-deleted
        order = OrderRepository.get_by_id(db=db, order_id=order_id, include_deleted=True)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {order_id} não encontrado"
            )
        
        # Verifica se está realmente deletado
        if order.deleted_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pedido não está deletado"
            )
        
        # Restaura
        restored = OrderRepository.restore(db=db, order=order)
        return OrderOut.from_orm(restored)
        
    except HTTPException:
        raise
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao restaurar pedido")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
