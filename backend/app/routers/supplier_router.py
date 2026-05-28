"""
Router de Suppliers (Fornecedores) - endpoints HTTP.
Baseado na estrutura funcional de customer_routes.py
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.schemas.supplier_schema import SupplierCreate, SupplierUpdate, SupplierOut
from app.security.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.models.supplier import Supplier
from app.core.errors import sanitize_error_message


router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", status_code=status.HTTP_200_OK)
def list_suppliers(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_permission("suppliers", "read")),
    db: Session = Depends(get_db)
):
    """
    Lista fornecedores com paginação.
    
    **Permissão necessária: suppliers:read**
    
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
        # Validação
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        # Query com filtro de ativo
        query = db.query(Supplier).filter(Supplier.ativo == True)
        
        # Total
        total = query.count()
        
        # Paginação
        offset = (page - 1) * page_size
        items = query.order_by(Supplier.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Converter para Pydantic
        items_out = [SupplierOut.model_validate(supplier) for supplier in items]
        
        return {
            "items": items_out,
            "page": page,
            "page_size": page_size,
            "total": total
        }
    
    except Exception as e:
        detail = sanitize_error_message(e, "Erro ao listar fornecedores")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/stats/summary", status_code=status.HTTP_200_OK)
def get_suppliers_stats_summary(
    current_user: User = Depends(require_permission("suppliers", "read")),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas resumidas para cards do frontend.

    **Permissão necessária: suppliers:read**
    """
    try:
        base_query = db.query(Supplier).filter(Supplier.ativo == True)

        total = base_query.count()

        type_rows = (
            db.query(Supplier.tipo, func.count(Supplier.id))
            .filter(Supplier.ativo == True)
            .group_by(Supplier.tipo)
            .all()
        )
        by_type = {tipo: count for tipo, count in type_rows}

        category_rows = (
            db.query(Supplier.categoria, func.count(Supplier.id))
            .filter(Supplier.ativo == True)
            .group_by(Supplier.categoria)
            .order_by(func.count(Supplier.id).desc())
            .all()
        )

        return {
            "total": total,
            "por_tipo": {
                "PF": int(by_type.get("PF", 0)),
                "PJ": int(by_type.get("PJ", 0)),
            },
            "por_categoria": [
                {
                    "categoria": categoria or "Sem categoria",
                    "count": int(count),
                }
                for categoria, count in category_rows
            ],
        }
    except Exception as e:
        detail = sanitize_error_message(e, "Erro ao buscar estatísticas de fornecedores")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SupplierOut)
def create_supplier(
    supplier_data: SupplierCreate,
    current_user: User = Depends(require_permission("suppliers", "create")),
    db: Session = Depends(get_db)
):
    """
    Cria novo fornecedor.
    
    **Permissão necessária: suppliers:create**
    
    Body: SupplierCreate schema
    """
    try:
        # Verificar CNPJ/CPF duplicado (se fornecido)
        normalized_doc = (supplier_data.cnpj_cpf or "").strip()
        if normalized_doc:
            existing = db.query(Supplier).filter(
                and_(
                    Supplier.cnpj_cpf == normalized_doc,
                    Supplier.ativo == True
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="CNPJ/CPF já cadastrado"
                )
        
        # Criar fornecedor
        supplier_dict = supplier_data.model_dump(exclude_none=True)
        supplier_dict['user_id'] = current_user.id
        supplier = Supplier(**supplier_dict)
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        
        return SupplierOut.model_validate(supplier)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        detail = sanitize_error_message(e, "Erro ao criar fornecedor")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/{supplier_id}", status_code=status.HTTP_200_OK, response_model=SupplierOut)
def get_supplier(
    supplier_id: UUID,
    current_user: User = Depends(require_permission("suppliers", "read")),
    db: Session = Depends(get_db)
):
    """
    Busca fornecedor por ID.
    
    **Permissão necessária: suppliers:read**
    """
    try:
        supplier = db.query(Supplier).filter(
            and_(
                Supplier.id == supplier_id,
                Supplier.ativo == True
            )
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fornecedor não encontrado"
            )
        
        return SupplierOut.model_validate(supplier)
    
    except HTTPException:
        raise
    except Exception as e:
        detail = sanitize_error_message(e, "Erro ao buscar fornecedor")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.patch("/{supplier_id}", status_code=status.HTTP_200_OK, response_model=SupplierOut)
def update_supplier(
    supplier_id: UUID,
    supplier_data: SupplierUpdate,
    current_user: User = Depends(require_permission("suppliers", "update")),
    db: Session = Depends(get_db)
):
    """
    Atualiza fornecedor (PATCH parcial).
    
    **Permissão necessária: suppliers:update**
    """
    try:
        supplier = db.query(Supplier).filter(
            and_(
                Supplier.id == supplier_id,
                Supplier.ativo == True
            )
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fornecedor não encontrado"
            )
        
        # Verificar CNPJ/CPF duplicado (se alterando)
        normalized_doc = (supplier_data.cnpj_cpf or "").strip()
        if normalized_doc and normalized_doc != supplier.cnpj_cpf:
            existing = db.query(Supplier).filter(
                and_(
                    Supplier.cnpj_cpf == normalized_doc,
                    Supplier.ativo == True,
                    Supplier.id != supplier_id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="CNPJ/CPF já cadastrado para outro fornecedor"
                )
        
        # Atualizar campos fornecidos
        update_data = supplier_data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)
        
        db.commit()
        db.refresh(supplier)
        
        return SupplierOut.model_validate(supplier)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        detail = sanitize_error_message(e, "Erro ao atualizar fornecedor")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: UUID,
    current_user: User = Depends(require_permission("suppliers", "delete")),
    db: Session = Depends(get_db)
):
    """
    Deleta fornecedor (soft delete).
    
    **Permissão necessária: suppliers:delete**
    """
    try:
        supplier = db.query(Supplier).filter(
            and_(
                Supplier.id == supplier_id,
                Supplier.ativo == True
            )
        ).first()
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fornecedor não encontrado"
            )
        
        # Soft delete
        supplier.ativo = False
        db.commit()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        detail = sanitize_error_message(e, "Erro ao deletar fornecedor")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
