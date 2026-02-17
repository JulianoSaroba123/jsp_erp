"""
Router de Financial Entries - endpoints HTTP.
Responsabilidade: receber requests e chamar FinancialService.
NÃO contém lógica de negócio nem queries SQL.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.services.financial_service import FinancialService
from app.schemas.financial_schema import (
    FinancialEntryCreate,
    FinancialEntryResponse,
    FinancialEntryUpdateStatus,
    FinancialEntryListResponse
)
from app.auth import get_current_user
from app.models.user import User
from app.security.deps import get_db  # CENTRALIZADO


router = APIRouter(prefix="/financial/entries", tags=["Financeiro"])


@router.get("", response_model=FinancialEntryListResponse, status_code=status.HTTP_200_OK)
def list_entries(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página (max 100)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtro: pending, paid, canceled"),
    kind: Optional[str] = Query(None, description="Filtro: revenue, expense"),
    date_from: Optional[datetime] = Query(None, description="Data inicial (occurred_at >= date_from)"),
    date_to: Optional[datetime] = Query(None, description="Data final (occurred_at <= date_to)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista lançamentos financeiros com paginação e filtros opcionais.
    
    **Autenticação obrigatória (Bearer token)**
    
    Regras multi-tenant:
    - **admin**: vê todos os lançamentos
    - **outros roles**: vê apenas seus próprios lançamentos
    
    Query params:
    - page: número da página (default 1, min 1)
    - page_size: itens por página (default 20, max 100)
    - status: filtro opcional (pending, paid, canceled)
    - kind: filtro opcional (revenue, expense)
    - date_from: data inicial (ISO 8601)
    - date_to: data final (ISO 8601)
    
    Response:
    {
      "items": [...],
      "page": 1,
      "page_size": 20,
      "total": 50
    }
    """
    try:
        # Multi-tenant: admin vê tudo, outros veem só os seus
        user_id_filter = None if current_user.role == "admin" else current_user.id
        
        result = FinancialService.list_entries(
            db=db,
            page=page,
            page_size=page_size,
            user_id=user_id_filter,
            status=status_filter,
            kind=kind,
            date_from=date_from,
            date_to=date_to
        )
        
        # Converte ORM models para FinancialEntryResponse
        items_out = [FinancialEntryResponse.model_validate(entry) for entry in result["items"]]
        
        return {
            "items": items_out,
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"]
        }
    
    except ValueError as e:
        # Erros de validação (filtros inválidos)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Erros inesperados (sanitizar em produção)
        from app.exceptions.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao listar lançamentos financeiros")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/{entry_id}", response_model=FinancialEntryResponse, status_code=status.HTTP_200_OK)
def get_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca lançamento financeiro por ID.
    
    **Autenticação obrigatória (Bearer token)**
    
    Regras multi-tenant:
    - **admin**: pode ver qualquer lançamento
    - **outros roles**: podem ver apenas seus próprios lançamentos (404 se não for dono)
    
    Response: FinancialEntryResponse
    """
    try:
        entry = FinancialService.get_entry_by_id(db=db, entry_id=entry_id)
        
        # Não encontrado ou multi-tenant (retorna 404 em ambos os casos para não vazar)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lançamento {entry_id} não encontrado"
            )
        
        # Multi-tenant: user só pode ver seus lançamentos (admin pode ver tudo)
        if current_user.role != "admin" and entry.user_id != current_user.id:
            # Retorna 404 (não 403) para não revelar existência (anti-enumeration)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lançamento {entry_id} não encontrado"
            )
        
        return FinancialEntryResponse.model_validate(entry)
    
    except HTTPException:
        raise
    except Exception as e:
        from app.exceptions.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao buscar lançamento")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.post("", response_model=FinancialEntryResponse, status_code=status.HTTP_201_CREATED)
def create_manual_entry(
    entry_data: FinancialEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria lançamento financeiro manual (sem vinculação a pedido).
    
    **Autenticação obrigatória (Bearer token)**
    
    Regras:
    - user_id é obtido do token JWT (não pode ser fornecido no body)
    - kind: 'revenue' (receita) ou 'expense' (despesa)
    - amount: >= 0
    - status inicial: 'pending'
    
    Body (FinancialEntryCreate):
    - kind: 'revenue' ou 'expense'
    - amount: valor (>= 0)
    - description: descrição (1-500 chars)
    - occurred_at: data de ocorrência (opcional, default: now)
    
    Response: FinancialEntryResponse (lançamento criado)
    """
    try:
        entry = FinancialService.create_manual_entry(
            db=db,
            user_id=current_user.id,  # user_id vem do token
            kind=entry_data.kind,
            amount=float(entry_data.amount),
            description=entry_data.description,
            occurred_at=entry_data.occurred_at
        )
        
        return FinancialEntryResponse.model_validate(entry)
    
    except ValueError as e:
        # Erros de validação de negócio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        from app.exceptions.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao criar lançamento")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.patch("/{entry_id}/status", response_model=FinancialEntryResponse, status_code=status.HTTP_200_OK)
def update_entry_status(
    entry_id: UUID,
    status_data: FinancialEntryUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza status de um lançamento financeiro.
    
    **Autenticação obrigatória (Bearer token)**
    
    Regras multi-tenant:
    - **admin**: pode atualizar qualquer lançamento
    - **outros roles**: podem atualizar apenas seus próprios lançamentos
    
    Regras de transição permitidas (MVP):
    - pending → paid
    - pending → canceled
    - Demais transições bloqueadas
    
    Body:
    - status: 'pending', 'paid', 'canceled'
    
    Response: FinancialEntryResponse (lançamento atualizado)
    """
    try:
        # Buscar lançamento
        entry = FinancialService.get_entry_by_id(db=db, entry_id=entry_id)
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lançamento {entry_id} não encontrado"
            )
        
        # Multi-tenant: user só pode atualizar seus lançamentos (admin pode atualizar tudo)
        if current_user.role != "admin" and entry.user_id != current_user.id:
            # Retorna 404 (não 403) para não revelar existência
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lançamento {entry_id} não encontrado"
            )
        
        # Atualizar status
        updated_entry = FinancialService.update_status(
            db=db,
            entry=entry,
            new_status=status_data.status
        )
        
        return FinancialEntryResponse.model_validate(updated_entry)
    
    except HTTPException:
        raise
    except ValueError as e:
        # Erros de validação (transição inválida, status inválido)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        from app.exceptions.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao atualizar status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
