"""
Router de Relatórios Financeiros - endpoints HTTP.
Responsabilidade: receber requests e chamar ReportService.
NÃO contém lógica de negócio nem queries SQL.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.services.report_service import ReportService
from app.schemas.report_schema import (
    DREResponse,
    CashflowDailyResponse,
    AgingResponse,
    TopEntriesResponse
)
from app.auth import get_current_user
from app.models.user import User
from app.security.deps import get_db  # CENTRALIZADO


router = APIRouter(prefix="/reports/financial", tags=["Reports"])


@router.get("/dre", response_model=DREResponse, status_code=status.HTTP_200_OK)
def get_dre_report(
    date_from: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Data final (YYYY-MM-DD)"),
    include_canceled: bool = Query(False, description="Incluir lançamentos cancelados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    DRE Simplificada - Demonstração de Resultado do Exercício.
    
    **Autenticação obrigatória (Bearer token)**
    
    Retorna:
    - Receitas e despesas pagas
    - Receitas e despesas pendentes
    - Resultado líquido (pago e esperado)
    - Total de lançamentos
    
    Regras multi-tenant:
    - **admin**: consolidado de todos usuários
    - **outros roles**: apenas lançamentos do próprio usuário
    
    Validações:
    - date_from <= date_to
    - Intervalo máximo: 366 dias
    
    Query params:
    - date_from: Data inicial (obrigatório, formato YYYY-MM-DD)
    - date_to: Data final (obrigatório, formato YYYY-MM-DD)
    - include_canceled: Se true, inclui lançamentos cancelados (default: false)
    """
    try:
        # Multi-tenant: admin vê tudo, outros veem só seus
        user_id_filter = None if current_user.role == "admin" else current_user.id
        
        result = ReportService.get_dre(
            db=db,
            date_from=date_from,
            date_to=date_to,
            user_id=user_id_filter,
            include_canceled=include_canceled
        )
        
        return result
    
    except ValueError as e:
        # Erros de validação (datas inválidas, intervalo muito grande)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Erros inesperados (sanitizar em produção)
        from app.exceptions.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao gerar relatório DRE")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/cashflow/daily", response_model=CashflowDailyResponse, status_code=status.HTTP_200_OK)
def get_cashflow_daily_report(
    date_from: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Data final (YYYY-MM-DD)"),
    include_canceled: bool = Query(False, description="Incluir lançamentos cancelados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fluxo de Caixa Diário - série temporal completa.
    
    **Autenticação obrigatória (Bearer token)**
    
    Retorna lista de dias (de date_from até date_to) com:
    - Receitas e despesas pagas
    - Receitas e despesas pendentes
    - Resultado líquido (pago e esperado)
    
    **Importante:** Dias sem lançamentos aparecem com valores zero (série completa).
    
    Regras multi-tenant:
    - **admin**: consolidado de todos usuários
    - **outros roles**: apenas lançamentos do próprio usuário
    
    Validações:
    - date_from <= date_to
    - Intervalo máximo: 366 dias
    
    Query params:
    - date_from: Data inicial (obrigatório)
    - date_to: Data final (obrigatório)
    - include_canceled: Se true, inclui lançamentos cancelados (default: false)
    """
    try:
        # Multi-tenant
        user_id_filter = None if current_user.role == "admin" else current_user.id
        
        result = ReportService.get_cashflow_daily(
            db=db,
            date_from=date_from,
            date_to=date_to,
            user_id=user_id_filter,
            include_canceled=include_canceled
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        from app.exceptions.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao gerar cashflow diário")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/pending/aging", response_model=AgingResponse, status_code=status.HTTP_200_OK)
def get_pending_aging_report(
    date_from: date = Query(..., description="Data inicial (occurred_at)"),
    date_to: date = Query(..., description="Data final (occurred_at)"),
    reference_date: Optional[date] = Query(None, description="Data de referência para aging (default: hoje)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aging de Pendências - classificação por faixa de dias.
    
    **Autenticação obrigatória (Bearer token)**
    
    Retorna pendências (status='pending') classificadas por idade:
    - 0-7 dias
    - 8-30 dias
    - 31+ dias
    
    Cálculo de aging: reference_date - occurred_at (em dias)
    Se reference_date não for informado, usa data atual.
    
    Regras multi-tenant:
    - **admin**: consolidado de todos usuários
    - **outros roles**: apenas lançamentos do próprio usuário
    
    Validações:
    - date_from <= date_to
    - Intervalo máximo: 366 dias
    
    Query params:
    - date_from: Data inicial (occurred_at >= date_from)
    - date_to: Data final (occurred_at <= date_to)
    - reference_date: Data de referência (default: hoje)
    """
    try:
        # Multi-tenant
        user_id_filter = None if current_user.role == "admin" else current_user.id
        
        result = ReportService.get_aging_pending(
            db=db,
            date_from=date_from,
            date_to=date_to,
            user_id=user_id_filter,
            reference_date=reference_date
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        from app.exceptions.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao gerar aging de pendências")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/top", response_model=TopEntriesResponse, status_code=status.HTTP_200_OK)
def get_top_entries_report(
    kind: str = Query(..., description="Tipo: 'revenue' ou 'expense'"),
    date_from: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Data final (YYYY-MM-DD)"),
    status_filter: str = Query("paid", alias="status", description="Status: 'paid', 'pending', 'canceled'"),
    limit: int = Query(10, ge=1, le=50, description="Limite de resultados (default: 10, max: 50)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Top Lançamentos por Valor - agregados por descrição.
    
    **Autenticação obrigatória (Bearer token)**
    
    Retorna top N lançamentos ordenados por valor total (soma de amounts).
    Agrupa por description e soma os valores.
    
    Exemplo: Se houver 3 lançamentos "Venda Produto X" (1000, 1500, 2500),
    retorna um item com total_amount=5000 e count=3.
    
    Regras multi-tenant:
    - **admin**: consolidado de todos usuários
    - **outros roles**: apenas lançamentos do próprio usuário
    
    Validações:
    - date_from <= date_to
    - Intervalo máximo: 366 dias
    - kind: 'revenue' ou 'expense' (obrigatório)
    - status: 'paid', 'pending' ou 'canceled' (default: paid)
    - limit: 1 a 50 (default: 10)
    
    Query params:
    - kind: Tipo (revenue ou expense) - obrigatório
    - date_from: Data inicial - obrigatório
    - date_to: Data final - obrigatório
    - status: Status (default: paid)
    - limit: Limite de resultados (default: 10, max: 50)
    """
    try:
        # Multi-tenant
        user_id_filter = None if current_user.role == "admin" else current_user.id
        
        result = ReportService.get_top_entries(
            db=db,
            kind=kind,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            user_id=user_id_filter
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        from app.exceptions.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao gerar top lançamentos")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
