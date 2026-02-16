"""
Service para Relatórios Financeiros - regras de negócio e validações.
Camada de validações, transformações e lógica de negócio para relatórios.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from app.repositories.report_repository import ReportRepository


class ReportService:
    """Service com regras de negócio para relatórios financeiros."""

    # Constantes de validação
    MAX_DATE_RANGE_DAYS = 366  # Máximo 1 ano de dados
    MAX_TOP_LIMIT = 50
    DEFAULT_TOP_LIMIT = 10
    VALID_KINDS = ['revenue', 'expense']
    VALID_STATUSES = ['pending', 'paid', 'canceled']

    @staticmethod
    def validate_date_range(date_from: date, date_to: date) -> None:
        """
        Valida intervalo de datas.
        
        Regras:
        - date_from <= date_to
        - Intervalo máximo de 366 dias
        
        Raises:
            ValueError: Se validação falhar
        """
        if date_from > date_to:
            raise ValueError(f"date_from ({date_from}) não pode ser maior que date_to ({date_to})")
        
        days_diff = (date_to - date_from).days
        if days_diff > ReportService.MAX_DATE_RANGE_DAYS:
            raise ValueError(
                f"Intervalo muito grande: {days_diff} dias. "
                f"Máximo permitido: {ReportService.MAX_DATE_RANGE_DAYS} dias"
            )

    @staticmethod
    def get_dre(
        db: Session,
        date_from: date,
        date_to: date,
        user_id: Optional[UUID] = None,
        include_canceled: bool = False
    ) -> dict:
        """
        DRE Simplificada - Demonstração de Resultado do Exercício.
        
        Args:
            db: Sessão SQLAlchemy
            date_from: Data inicial (obrigatório)
            date_to: Data final (obrigatório)
            user_id: Filtro multi-tenant (None = admin vê tudo)
            include_canceled: Se True, inclui lançamentos cancelados
            
        Returns:
            {
                "period": {"date_from": date, "date_to": date},
                "revenue_paid_total": float,
                "expense_paid_total": float,
                "net_paid": float,
                "revenue_pending_total": float,
                "expense_pending_total": float,
                "net_expected": float,
                "count_entries_total": int
            }
        """
        # Validar intervalo de datas
        ReportService.validate_date_range(date_from, date_to)
        
        # Buscar dados agregados
        summary = ReportRepository.dre_summary(
            db=db,
            date_from=date_from,
            date_to=date_to,
            user_id=user_id,
            include_canceled=include_canceled
        )
        
        # Montar resposta
        return {
            "period": {
                "date_from": date_from,
                "date_to": date_to
            },
            **summary
        }

    @staticmethod
    def get_cashflow_daily(
        db: Session,
        date_from: date,
        date_to: date,
        user_id: Optional[UUID] = None,
        include_canceled: bool = False
    ) -> dict:
        """
        Fluxo de caixa diário com série temporal completa (preenche zeros).
        
        Args:
            db: Sessão SQLAlchemy
            date_from: Data inicial
            date_to: Data final
            user_id: Filtro multi-tenant
            include_canceled: Se True, inclui canceled
            
        Returns:
            {
                "period": {"date_from": date, "date_to": date},
                "days": [
                    {
                        "date": date,
                        "revenue_paid": float,
                        "expense_paid": float,
                        "net_paid": float,
                        "revenue_pending": float,
                        "expense_pending": float,
                        "net_expected": float
                    },
                    ...
                ]
            }
        """
        # Validar intervalo
        ReportService.validate_date_range(date_from, date_to)
        
        # Buscar dados agregados do banco (apenas dias com dados)
        daily_data = ReportRepository.cashflow_daily(
            db=db,
            date_from=date_from,
            date_to=date_to,
            user_id=user_id,
            include_canceled=include_canceled
        )
        
        # Criar dict de lookup rápido: date -> data
        data_by_date = {item["date"]: item for item in daily_data}
        
        # Preencher série temporal completa (todos os dias)
        complete_days = []
        current_date = date_from
        
        while current_date <= date_to:
            if current_date in data_by_date:
                # Dia com dados: copiar para não mutar original
                day_data = dict(data_by_date[current_date])
            else:
                # Dia sem dados: criar com zeros
                day_data = {
                    "date": current_date,
                    "revenue_paid": 0.0,
                    "expense_paid": 0.0,
                    "revenue_pending": 0.0,
                    "expense_pending": 0.0
                }
            
            # Garantir tipos float e calcular net (sempre)
            rp = float(day_data["revenue_paid"])
            ep = float(day_data["expense_paid"])
            rpen = float(day_data["revenue_pending"])
            epen = float(day_data["expense_pending"])
            
            day_data["net_paid"] = rp - ep
            day_data["net_expected"] = (rp + rpen) - (ep + epen)
            
            complete_days.append(day_data)
            current_date += timedelta(days=1)
        
        return {
            "period": {
                "date_from": date_from,
                "date_to": date_to
            },
            "days": complete_days
        }

    @staticmethod
    def get_aging_pending(
        db: Session,
        date_from: date,
        date_to: date,
        user_id: Optional[UUID] = None,
        reference_date: Optional[date] = None
    ) -> dict:
        """
        Aging de pendências - classificação em faixas de dias.
        
        Calcula quantos dias cada lançamento pendente está atrasado
        em relação à reference_date (padrão: hoje).
        
        Args:
            db: Sessão SQLAlchemy
            date_from: Data inicial (occurred_at)
            date_to: Data final (occurred_at)
            user_id: Filtro multi-tenant
            reference_date: Data de referência (default: hoje)
            
        Returns:
            {
                "period": {"date_from": date, "date_to": date},
                "reference_date": date,
                "pending_revenue": {
                    "0_7_days": float,
                    "8_30_days": float,
                    "31_plus_days": float,
                    "total": float
                },
                "pending_expense": {...}
            }
        """
        # Validar intervalo
        ReportService.validate_date_range(date_from, date_to)
        
        # Reference date padrão: hoje
        if reference_date is None:
            reference_date = date.today()
        
        # Buscar aging
        aging_data = ReportRepository.aging_pending(
            db=db,
            date_from=date_from,
            date_to=date_to,
            reference_date=reference_date,
            user_id=user_id
        )
        
        return {
            "period": {
                "date_from": date_from,
                "date_to": date_to
            },
            "reference_date": reference_date,
            **aging_data
        }

    @staticmethod
    def get_top_entries(
        db: Session,
        kind: str,
        status: str,
        date_from: date,
        date_to: date,
        limit: int = DEFAULT_TOP_LIMIT,
        user_id: Optional[UUID] = None
    ) -> dict:
        """
        Top lançamentos por valor (agregados por descrição).
        
        Args:
            db: Sessão SQLAlchemy
            kind: 'revenue' ou 'expense' (obrigatório)
            status: 'paid', 'pending' ou 'canceled' (default: paid)
            date_from: Data inicial
            date_to: Data final
            limit: Limite de resultados (default 10, max 50)
            user_id: Filtro multi-tenant
            
        Returns:
            {
                "period": {"date_from": date, "date_to": date},
                "kind": str,
                "status": str,
                "items": [
                    {
                        "description": str,
                        "total_amount": float,
                        "count": int,
                        "last_occurred_at": datetime
                    },
                    ...
                ]
            }
        """
        # Validar intervalo
        ReportService.validate_date_range(date_from, date_to)
        
        # Validar kind
        if kind not in ReportService.VALID_KINDS:
            raise ValueError(
                f"kind inválido: '{kind}'. Use: {', '.join(ReportService.VALID_KINDS)}"
            )
        
        # Validar status
        if status not in ReportService.VALID_STATUSES:
            raise ValueError(
                f"status inválido: '{status}'. Use: {', '.join(ReportService.VALID_STATUSES)}"
            )
        
        # Validar e ajustar limit
        if limit < 1:
            limit = ReportService.DEFAULT_TOP_LIMIT
        if limit > ReportService.MAX_TOP_LIMIT:
            limit = ReportService.MAX_TOP_LIMIT
        
        # Buscar top entries
        items = ReportRepository.top_entries(
            db=db,
            kind=kind,
            status=status,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            user_id=user_id
        )
        
        return {
            "period": {
                "date_from": date_from,
                "date_to": date_to
            },
            "kind": kind,
            "status": status,
            "items": items
        }
