"""
Router de Customers - endpoints HTTP.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.customer_schema import CustomerCreate, CustomerUpdate, CustomerOut
from app.security.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.services.customer_service import CustomerService
from app.exceptions.errors import NotFoundError, ConflictError, ValidationError
from app.core.errors import sanitize_error_message


router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", status_code=status.HTTP_200_OK)
def list_customers(
    page: int = 1,
    page_size: int = 20,
    status_filter: str = None,
    current_user: User = Depends(require_permission("customers", "read")),
    db: Session = Depends(get_db)
):
    """
    Lista clientes com paginação.
    
    **Permissão necessária: customers:read**
    
    Query params:
    - page: número da página (default 1, min 1)
    - page_size: itens por página (default 20, max 100)
    - status_filter: filtro por status ('active'/'inactive')
    
    Response:
    {
      "items": [...],
      "page": 1,
      "page_size": 20,
      "total": 123
    }
    """
    try:
        service = CustomerService(db)
        result = service.list_customers(page, page_size, status_filter)
        
        # Converter items para Pydantic
        result["items"] = [CustomerOut.model_validate(c) for c in result["items"]]
        
        return result
    
    except Exception as e:
        detail = sanitize_error_message(e, "Erro ao listar clientes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CustomerOut)
def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(require_permission("customers", "create")),
    db: Session = Depends(get_db)
):
    """
    Cria novo cliente.
    
    **Permissão necessária: customers:create**
    
    Body: CustomerCreate schema
    """
    try:
        service = CustomerService(db)
        customer = service.create_customer(customer_data)
        return CustomerOut.model_validate(customer)
    
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        detail = sanitize_error_message(e, "Erro ao criar cliente")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/{customer_id}", status_code=status.HTTP_200_OK, response_model=CustomerOut)
def get_customer(
    customer_id: UUID,
    current_user: User = Depends(require_permission("customers", "read")),
    db: Session = Depends(get_db)
):
    """
    Busca cliente por ID.
    
    **Permissão necessária: customers:read**
    """
    try:
        service = CustomerService(db)
        customer = service.get_customer_by_id(customer_id)
        return CustomerOut.model_validate(customer)
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        detail = sanitize_error_message(e, "Erro ao buscar cliente")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.patch("/{customer_id}", status_code=status.HTTP_200_OK, response_model=CustomerOut)
def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    current_user: User = Depends(require_permission("customers", "update")),
    db: Session = Depends(get_db)
):
    """
    Atualiza cliente (PATCH parcial).
    
    **Permissão necessária: customers:update**
    """
    try:
        service = CustomerService(db)
        customer = service.update_customer(customer_id, customer_data)
        return CustomerOut.model_validate(customer)
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        detail = sanitize_error_message(e, "Erro ao atualizar cliente")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: UUID,
    current_user: User = Depends(require_permission("customers", "delete")),
    db: Session = Depends(get_db)
):
    """
    Deleta cliente (soft delete).
    
    **Permissão necessária: customers:delete**
    """
    try:
        service = CustomerService(db)
        service.delete_customer(customer_id)
        return None
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        detail = sanitize_error_message(e, "Erro ao deletar cliente")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
