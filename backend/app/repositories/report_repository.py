"""
Repository para Relatórios Financeiros - acesso a dados agregados.
Camada exclusiva de queries SQL com agregações (GROUP BY, SUM, COUNT).
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, extract, cast, Date
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta, time
from uuid import UUID

from app.models.financial_entry import FinancialEntry


class ReportRepository:
    """Repositório com queries agregadas para relatórios financeiros."""

    @staticmethod
    def dre_summary(
        db: Session,
        date_from: date,
        date_to: date,
        user_id: Optional[UUID] = None,
        include_canceled: bool = False
    ) -> Dict[str, Any]:
        """
        DRE Simplificada - Demonstração de Resultado do Exercício.
        
        Agregações:
        - Receitas pagas (revenue + paid)
        - Despesas pagas (expense + paid)
        - Resultado líquido pago
        - Receitas pendentes (revenue + pending)
        - Despesas pendentes (expense + pending)
        - Resultado esperado (pago + pendente)
        - Total de lançamentos
        
        Args:
            db: Sessão SQLAlchemy
            date_from: Data inicial (occurred_at >= date_from)
            date_to: Data final (occurred_at <= date_to)
            user_id: Filtro multi-tenant (None = admin vê tudo)
            include_canceled: Se True, inclui status=canceled nos totais
            
        Returns:
            {
                "revenue_paid_total": Decimal,
                "expense_paid_total": Decimal,
                "net_paid": Decimal,
                "revenue_pending_total": Decimal,
                "expense_pending_total": Decimal,
                "net_expected": Decimal,
                "count_entries_total": int
            }
        """
        # Query base com filtros de data e user_id
        query = db.query(FinancialEntry).filter(
            and_(
                cast(FinancialEntry.occurred_at, Date) >= date_from,
                cast(FinancialEntry.occurred_at, Date) <= date_to
            )
        )
        
        # Multi-tenant
        if user_id:
            query = query.filter(FinancialEntry.user_id == user_id)
        
        # Filtro de status (excluir canceled por padrão)
        if not include_canceled:
            query = query.filter(FinancialEntry.status.in_(['pending', 'paid']))
        
        # Filtros de data otimizados (timestamp interval para usar índice)
        start_dt = datetime.combine(date_from, time.min)
        end_dt = datetime.combine(date_to + timedelta(days=1), time.min)
        
        # Agregações condicionais via case
        aggregations = db.query(
            # Receitas pagas
            func.coalesce(
                func.sum(
                    case(
                        (and_(FinancialEntry.kind == 'revenue', FinancialEntry.status == 'paid'), FinancialEntry.amount),
                        else_=0
                    )
                ),
                0
            ).label('revenue_paid_total'),
            
            # Despesas pagas
            func.coalesce(
                func.sum(
                    case(
                        (and_(FinancialEntry.kind == 'expense', FinancialEntry.status == 'paid'), FinancialEntry.amount),
                        else_=0
                    )
                ),
                0
            ).label('expense_paid_total'),
            
            # Receitas pendentes
            func.coalesce(
                func.sum(
                    case(
                        (and_(FinancialEntry.kind == 'revenue', FinancialEntry.status == 'pending'), FinancialEntry.amount),
                        else_=0
                    )
                ),
                0
            ).label('revenue_pending_total'),
            
            # Despesas pendentes
            func.coalesce(
                func.sum(
                    case(
                        (and_(FinancialEntry.kind == 'expense', FinancialEntry.status == 'pending'), FinancialEntry.amount),
                        else_=0
                    )
                ),
                0
            ).label('expense_pending_total'),
            
            # Total de lançamentos
            func.count(FinancialEntry.id).label('count_entries_total')
        ).filter(
            and_(
                FinancialEntry.occurred_at >= start_dt,
                FinancialEntry.occurred_at < end_dt
            )
        )
        
        # Multi-tenant
        if user_id:
            aggregations = aggregations.filter(FinancialEntry.user_id == user_id)
        
        # Filtro de status
        if not include_canceled:
            aggregations = aggregations.filter(FinancialEntry.status.in_(['pending', 'paid']))
        
        result = aggregations.first()
        
        if not result:
            return {
                "revenue_paid_total": 0,
                "expense_paid_total": 0,
                "net_paid": 0,
                "revenue_pending_total": 0,
                "expense_pending_total": 0,
                "net_expected": 0,
                "count_entries_total": 0
            }
        
        # Converter para dict e calcular net
        revenue_paid = float(result.revenue_paid_total)
        expense_paid = float(result.expense_paid_total)
        revenue_pending = float(result.revenue_pending_total)
        expense_pending = float(result.expense_pending_total)
        
        return {
            "revenue_paid_total": revenue_paid,
            "expense_paid_total": expense_paid,
            "net_paid": revenue_paid - expense_paid,
            "revenue_pending_total": revenue_pending,
            "expense_pending_total": expense_pending,
            "net_expected": (revenue_paid + revenue_pending) - (expense_paid + expense_pending),
            "count_entries_total": result.count_entries_total
        }

    @staticmethod
    def cashflow_daily(
        db: Session,
        date_from: date,
        date_to: date,
        user_id: Optional[UUID] = None,
        include_canceled: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fluxo de caixa diário - agregações por data (occurred_at::date).
        
        Retorna lista de dias com totais agregados.
        NOTA: Dias sem lançamentos NÃO aparecem aqui (Service completa com zeros).
        
        Args:
            db: Sessão SQLAlchemy
            date_from: Data inicial
            date_to: Data final
            user_id: Filtro multi-tenant
            include_canceled: Se True, inclui canceled
            
        Returns:
            [
                {
                    "date": date,
                    "revenue_paid": float,
                    "expense_paid": float,
                    "revenue_pending": float,
                    "expense_pending": float
                },
                ...
            ]
        """
        # Filtros de data otimizados (timestamp interval)
        start_dt = datetime.combine(date_from, time.min)
        end_dt = datetime.combine(date_to + timedelta(days=1), time.min)
        
        # Agregação por dia (usar variável para GROUP BY e ORDER BY)
        day = cast(FinancialEntry.occurred_at, Date)
        
        query = db.query(
            day.label('date'),
            
            # Receitas pagas
            func.coalesce(
                func.sum(
                    case(
                        (and_(FinancialEntry.kind == 'revenue', FinancialEntry.status == 'paid'), FinancialEntry.amount),
                        else_=0
                    )
                ),
                0
            ).label('revenue_paid'),
            
            # Despesas pagas
            func.coalesce(
                func.sum(
                    case(
                        (and_(FinancialEntry.kind == 'expense', FinancialEntry.status == 'paid'), FinancialEntry.amount),
                        else_=0
                    )
                ),
                0
            ).label('expense_paid'),
            
            # Receitas pendentes
            func.coalesce(
                func.sum(
                    case(
                        (and_(FinancialEntry.kind == 'revenue', FinancialEntry.status == 'pending'), FinancialEntry.amount),
                        else_=0
                    )
                ),
                0
            ).label('revenue_pending'),
            
            # Despesas pendentes
            func.coalesce(
                func.sum(
                    case(
                        (and_(FinancialEntry.kind == 'expense', FinancialEntry.status == 'pending'), FinancialEntry.amount),
                        else_=0
                    )
                ),
                0
            ).label('expense_pending')
        ).filter(
            and_(
                FinancialEntry.occurred_at >= start_dt,
                FinancialEntry.occurred_at < end_dt
            )
        )
        
        # Multi-tenant
        if user_id:
            query = query.filter(FinancialEntry.user_id == user_id)
        
        # Filtro de status
        if not include_canceled:
            query = query.filter(FinancialEntry.status.in_(['pending', 'paid']))
        
        # Agrupar por dia e ordenar
        query = query.group_by(day).order_by(day)
        
        results = query.all()
        
        # Converter para lista de dicts
        daily_data = []
        for row in results:
            daily_data.append({
                "date": row.date,
                "revenue_paid": float(row.revenue_paid),
                "expense_paid": float(row.expense_paid),
                "revenue_pending": float(row.revenue_pending),
                "expense_pending": float(row.expense_pending)
            })
        
        return daily_data

    @staticmethod
    def aging_pending(
        db: Session,
        date_from: date,
        date_to: date,
        reference_date: date,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Aging de pendências - classificação em faixas de dias.
        
        Calcula: dias_atraso = reference_date - occurred_at
        
        Faixas:
        - 0-7 dias
        - 8-30 dias
        - 31+ dias
        
        Args:
            db: Sessão SQLAlchemy
            date_from: Data inicial (occurred_at)
            date_to: Data final (occurred_at)
            reference_date: Data de referência para cálculo de aging (ex: hoje)
            user_id: Filtro multi-tenant
            
        Returns:
            {
                "pending_revenue": {
                    "0_7_days": float,
                    "8_30_days": float,
                    "31_plus_days": float,
                    "total": float
                },
                "pending_expense": {
                    "0_7_days": float,
                    "8_30_days": float,
                    "31_plus_days": float,
                    "total": float
                }
            }
        """
        # Filtros de data otimizados (timestamp interval)
        start_dt = datetime.combine(date_from, time.min)
        end_dt = datetime.combine(date_to + timedelta(days=1), time.min)
        
        # Query base: apenas pending no período
        query = db.query(FinancialEntry).filter(
            and_(
                FinancialEntry.status == 'pending',
                FinancialEntry.occurred_at >= start_dt,
                FinancialEntry.occurred_at < end_dt
            )
        )
        
        # Multi-tenant
        if user_id:
            query = query.filter(FinancialEntry.user_id == user_id)
        
        # Buscar todos pending
        entries = query.all()
        
        # Inicializar estruturas
        revenue_aging = {"0_7_days": 0.0, "8_30_days": 0.0, "31_plus_days": 0.0, "total": 0.0}
        expense_aging = {"0_7_days": 0.0, "8_30_days": 0.0, "31_plus_days": 0.0, "total": 0.0}
        
        # Calcular aging para cada entry
        for entry in entries:
            # Converter occurred_at para date
            occurred_date = entry.occurred_at.date() if isinstance(entry.occurred_at, datetime) else entry.occurred_at
            
            # Calcular dias de atraso (não permitir negativo)
            days_old = max(0, (reference_date - occurred_date).days)
            
            # Classificar em faixa
            amount = float(entry.amount)
            
            if entry.kind == 'revenue':
                revenue_aging["total"] += amount
                if days_old <= 7:
                    revenue_aging["0_7_days"] += amount
                elif days_old <= 30:
                    revenue_aging["8_30_days"] += amount
                else:
                    revenue_aging["31_plus_days"] += amount
            else:  # expense
                expense_aging["total"] += amount
                if days_old <= 7:
                    expense_aging["0_7_days"] += amount
                elif days_old <= 30:
                    expense_aging["8_30_days"] += amount
                else:
                    expense_aging["31_plus_days"] += amount
        
        return {
            "pending_revenue": revenue_aging,
            "pending_expense": expense_aging
        }

    @staticmethod
    def top_entries(
        db: Session,
        kind: str,
        status: str,
        date_from: date,
        date_to: date,
        limit: int,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Top lançamentos por valor (agregados por descrição).
        
        Agrupa por description e soma amounts, ordena por total DESC.
        
        Args:
            db: Sessão SQLAlchemy
            kind: 'revenue' ou 'expense'
            status: 'paid', 'pending', 'canceled'
            date_from: Data inicial
            date_to: Data final
            limit: Limite de resultados (max 50)
            user_id: Filtro multi-tenant
            
        Returns:
            [
                {
                    "description": str,
                    "total_amount": float,
                    "count": int,
                    "last_occurred_at": datetime
                },
                ...
            ]
        """
        # Filtros de data otimizados (timestamp interval)
        start_dt = datetime.combine(date_from, time.min)
        end_dt = datetime.combine(date_to + timedelta(days=1), time.min)
        
        query = db.query(
            FinancialEntry.description,
            func.sum(FinancialEntry.amount).label('total_amount'),
            func.count(FinancialEntry.id).label('count'),
            func.max(FinancialEntry.occurred_at).label('last_occurred_at')
        ).filter(
            and_(
                FinancialEntry.kind == kind,
                FinancialEntry.status == status,
                FinancialEntry.occurred_at >= start_dt,
                FinancialEntry.occurred_at < end_dt
            )
        )
        
        # Multi-tenant
        if user_id:
            query = query.filter(FinancialEntry.user_id == user_id)
        
        # Agrupar por descrição e ordenar por total DESC
        query = query.group_by(FinancialEntry.description).order_by(func.sum(FinancialEntry.amount).desc()).limit(limit)
        
        results = query.all()
        
        # Converter para lista de dicts
        top_list = []
        for row in results:
            top_list.append({
                "description": row.description,
                "total_amount": float(row.total_amount),
                "count": row.count,
                "last_occurred_at": row.last_occurred_at
            })
        
        return top_list
