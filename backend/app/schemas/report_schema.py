"""
Schemas Pydantic para Relatórios Financeiros.
Request e Response models para validação e serialização.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal


# ========================================
# DRE (Demonstração de Resultado)
# ========================================

class DREPeriod(BaseModel):
    """Período do relatório DRE."""
    date_from: date
    date_to: date


class DREResponse(BaseModel):
    """Resposta do endpoint DRE."""
    period: DREPeriod
    revenue_paid_total: float = Field(..., description="Total de receitas pagas")
    expense_paid_total: float = Field(..., description="Total de despesas pagas")
    net_paid: float = Field(..., description="Resultado líquido pago (receitas - despesas)")
    revenue_pending_total: float = Field(..., description="Total de receitas pendentes")
    expense_pending_total: float = Field(..., description="Total de despesas pendentes")
    net_expected: float = Field(..., description="Resultado esperado (pago + pendente)")
    count_entries_total: int = Field(..., description="Total de lançamentos no período")

    class Config:
        json_schema_extra = {
            "example": {
                "period": {"date_from": "2026-01-01", "date_to": "2026-01-31"},
                "revenue_paid_total": 15000.00,
                "expense_paid_total": 8000.00,
                "net_paid": 7000.00,
                "revenue_pending_total": 3000.00,
                "expense_pending_total": 1500.00,
                "net_expected": 8500.00,
                "count_entries_total": 25
            }
        }


# ========================================
# Cashflow Diário
# ========================================

class CashflowDailyItem(BaseModel):
    """Item de fluxo de caixa de um dia."""
    date: date
    revenue_paid: float = Field(..., description="Receitas pagas no dia")
    expense_paid: float = Field(..., description="Despesas pagas no dia")
    net_paid: float = Field(..., description="Resultado líquido pago (receita - despesa)")
    revenue_pending: float = Field(..., description="Receitas pendentes com occurred_at neste dia")
    expense_pending: float = Field(..., description="Despesas pendentes com occurred_at neste dia")
    net_expected: float = Field(..., description="Resultado esperado (pago + pendente)")


class CashflowDailyResponse(BaseModel):
    """Resposta do endpoint cashflow diário."""
    period: DREPeriod
    days: List[CashflowDailyItem] = Field(..., description="Lista de dias (pode ter dias com zeros)")

    class Config:
        json_schema_extra = {
            "example": {
                "period": {"date_from": "2026-02-01", "date_to": "2026-02-05"},
                "days": [
                    {
                        "date": "2026-02-01",
                        "revenue_paid": 1000.00,
                        "expense_paid": 500.00,
                        "net_paid": 500.00,
                        "revenue_pending": 200.00,
                        "expense_pending": 0.00,
                        "net_expected": 700.00
                    },
                    {
                        "date": "2026-02-02",
                        "revenue_paid": 0.00,
                        "expense_paid": 0.00,
                        "net_paid": 0.00,
                        "revenue_pending": 0.00,
                        "expense_pending": 0.00,
                        "net_expected": 0.00
                    }
                ]
            }
        }


# ========================================
# Aging de Pendências
# ========================================

class AgingBucket(BaseModel):
    """Faixa de aging (0-7, 8-30, 31+)."""
    days_0_7: float = Field(..., alias="0_7_days", description="Pendências de 0 a 7 dias")
    days_8_30: float = Field(..., alias="8_30_days", description="Pendências de 8 a 30 dias")
    days_31_plus: float = Field(..., alias="31_plus_days", description="Pendências acima de 31 dias")
    total: float = Field(..., description="Total de pendências")

    class Config:
        populate_by_name = True  # Permite usar alias
        json_schema_extra = {
            "example": {
                "0_7_days": 1500.00,
                "8_30_days": 800.00,
                "31_plus_days": 200.00,
                "total": 2500.00
            }
        }


class AgingResponse(BaseModel):
    """Resposta do endpoint aging de pendências."""
    period: DREPeriod
    reference_date: date = Field(..., description="Data de referência para cálculo de aging")
    pending_revenue: AgingBucket = Field(..., description="Receitas pendentes por faixa")
    pending_expense: AgingBucket = Field(..., description="Despesas pendentes por faixa")

    class Config:
        json_schema_extra = {
            "example": {
                "period": {"date_from": "2026-01-01", "date_to": "2026-02-16"},
                "reference_date": "2026-02-16",
                "pending_revenue": {
                    "0_7_days": 1500.00,
                    "8_30_days": 800.00,
                    "31_plus_days": 200.00,
                    "total": 2500.00
                },
                "pending_expense": {
                    "0_7_days": 500.00,
                    "8_30_days": 300.00,
                    "31_plus_days": 100.00,
                    "total": 900.00
                }
            }
        }


# ========================================
# Top Lançamentos
# ========================================

class TopEntryItem(BaseModel):
    """Item de top lançamento."""
    description: str
    total_amount: float = Field(..., description="Soma dos valores desta descrição")
    count: int = Field(..., description="Quantidade de lançamentos")
    last_occurred_at: datetime = Field(..., description="Data do último lançamento")


class TopEntriesResponse(BaseModel):
    """Resposta do endpoint top lançamentos."""
    period: DREPeriod
    kind: str = Field(..., description="revenue ou expense")
    status: str = Field(..., description="paid, pending ou canceled")
    items: List[TopEntryItem] = Field(..., description="Top lançamentos ordenados por total DESC")

    class Config:
        json_schema_extra = {
            "example": {
                "period": {"date_from": "2026-01-01", "date_to": "2026-01-31"},
                "kind": "revenue",
                "status": "paid",
                "items": [
                    {
                        "description": "Venda Produto X",
                        "total_amount": 5000.00,
                        "count": 3,
                        "last_occurred_at": "2026-01-28T10:30:00"
                    },
                    {
                        "description": "Serviço Consultoria",
                        "total_amount": 3500.00,
                        "count": 1,
                        "last_occurred_at": "2026-01-15T14:20:00"
                    }
                ]
            }
        }
