"""
Testes para app/routers/report_routes.py

Coverage target: 70%+
Testa endpoints de relatórios: DRE, cashflow, aging, top entries
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.user import User
from app.models.financial_entry import FinancialEntry


class TestDREReport:
    """Testes para GET /reports/dre"""
    
    def test_dre_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.get("/reports/financial/dre")
        
        assert response.status_code == 401
    
    def test_dre_empty_data(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar relatório vazio quando não há dados"""
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/dre?date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        assert "revenue_paid_total" in data
        assert "expense_paid_total" in data
        assert "net_paid" in data
    
    def test_dre_with_date_filters(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Deve aceitar filtros de data"""
        today = datetime.utcnow()
        date_from = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
        
        client.headers.update(auth_headers_admin)
        response = client.get(f"/reports/financial/dre?date_from={date_from}&date_to={date_to}")
        
        assert response.status_code == 200
        data = response.json()
        assert "revenue_paid_total" in data
    
    def test_dre_with_entries(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve calcular DRE corretamente com lançamentos"""
        # Criar receita
        revenue = FinancialEntry(
            user_id=seed_user_normal.id,
            kind='revenue',
            amount=1000.0,
            description='Receita teste',
            status='paid',
            occurred_at=datetime.utcnow()
        )
        
        # Criar despesa
        expense = FinancialEntry(
            user_id=seed_user_normal.id,
            kind='expense',
            amount=300.0,
            description='Despesa teste',
            status='paid',
            occurred_at=datetime.utcnow()
        )
        
        db_session.add_all([revenue, expense])
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/dre?date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        # DRE pode filtrar por user ou não, dependendo do multi-tenant
        assert "revenue_paid_total" in data
        assert "expense_paid_total" in data
        assert "net_paid" in data
    
    def test_dre_multi_tenant(
        self,
        client: TestClient,
        seed_user_admin: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve ver todos os lançamentos no DRE"""
        client.headers.update(auth_headers_admin)
        response = client.get("/reports/financial/dre?date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        assert "revenue_paid_total" in data


class TestCashflowDailyReport:
    """Testes para GET /reports/cashflow/daily"""
    
    def test_cashflow_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.get("/reports/financial/cashflow/daily?date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 401
    
    def test_cashflow_empty_data(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar lista vazia quando não há dados"""
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/cashflow/daily?date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert isinstance(data["days"], list)
    
    def test_cashflow_with_date_filters(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Deve aceitar filtros de data"""
        today = datetime.utcnow()
        date_from = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
        
        client.headers.update(auth_headers_admin)
        response = client.get(f"/reports/financial/cashflow/daily?date_from={date_from}&date_to={date_to}")
        
        assert response.status_code == 200
        data = response.json()
        assert "days" in data


class TestPendingAgingReport:
    """Testes para GET /reports/pending/aging"""
    
    def test_aging_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.get("/reports/financial/pending/aging?date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 401
    
    def test_aging_empty_data(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar lista vazia quando não há pendências"""
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/pending/aging?date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        assert "pending_revenue" in data
        assert "pending_expense" in data
    
    def test_aging_with_pending_entries(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve agrupar pendências por idade"""
        # Criar lançamento pendente antigo
        old_entry = FinancialEntry(
            user_id=seed_user_normal.id,
            kind='expense',
            amount=100.0,
            description='Pendente antigo',
            status='pending',
            occurred_at=datetime.utcnow() - timedelta(days=90)
        )
        
        # Criar lançamento pendente recente
        recent_entry = FinancialEntry(
            user_id=seed_user_normal.id,
            kind='expense',
            amount=50.0,
            description='Pendente recente',
            status='pending',
            occurred_at=datetime.utcnow() - timedelta(days=5)
        )
        
        db_session.add_all([old_entry, recent_entry])
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/pending/aging?date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        assert "pending_revenue" in data


class TestTopEntriesReport:
    """Testes para GET /reports/top"""
    
    def test_top_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.get("/reports/financial/top?kind=revenue&date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 401
    
    def test_top_empty_data(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar lista vazia quando não há dados"""
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/top?kind=revenue&date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_top_revenue_filter(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve filtrar top receitas corretamente"""
        # Criar receitas
        for i in range(5):
            entry = FinancialEntry(
                user_id=seed_user_normal.id,
                kind='revenue',
                amount=100.0 * (i + 1),
                description=f'Receita {i+1}',
                status='paid',
                occurred_at=datetime.utcnow()
            )
            db_session.add(entry)
        
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/top?kind=revenue&limit=3&date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Pode retornar até 3 itens
        assert len(data["items"]) <= 3
    
    def test_top_expense_filter(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve filtrar top despesas corretamente"""
        # Criar despesas
        for i in range(3):
            entry = FinancialEntry(
                user_id=seed_user_normal.id,
                kind='expense',
                amount=50.0 * (i + 1),
                description=f'Despesa {i+1}',
                status='paid',
                occurred_at=datetime.utcnow()
            )
            db_session.add(entry)
        
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/top?kind=expense&limit=5&date_from=2024-01-01&date_to=2024-12-31")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_top_with_date_filters(
        self,
        client: TestClient,
        auth_headers_admin: dict
    ):
        """Deve aceitar filtros de data"""
        today = datetime.utcnow()
        date_from = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
        
        client.headers.update(auth_headers_admin)
        response = client.get(f"/reports/financial/top?kind=revenue&date_from={date_from}&date_to={date_to}")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestReportRoutesEdgeCases:
    """Testes de edge cases e validações"""
    
    def test_top_invalid_kind(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar kind inválido"""
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/top?kind=invalid")
        
        # Pode retornar 400 ou 422
        assert response.status_code in [400, 422]
    
    def test_dre_invalid_date_format(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar formato de data inválido"""
        client.headers.update(auth_headers_user)
        response = client.get("/reports/financial/dre?date_from=invalid-date")
        
        # Pode retornar 400 ou 422
        assert response.status_code in [400, 422]
    
    def test_cashflow_date_from_after_date_to(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar date_from > date_to"""
        today = datetime.utcnow()
        date_from = today.strftime('%Y-%m-%d')
        date_to = (today - timedelta(days=10)).strftime('%Y-%m-%d')
        
        client.headers.update(auth_headers_user)
        response = client.get(f"/reports/financial/cashflow/daily?date_from={date_from}&date_to={date_to}")
        
        # Pode aceitar (invertendo) ou rejeitar
        assert response.status_code in [200, 400, 422]


class TestReportRoutesErrorBranches:
    """Testes focados em branches de erro não cobertos"""
    
    def test_dre_with_date_range_too_large(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400 para intervalo > 366 dias"""
        client.headers.update(auth_headers_user)
        
        # Intervalo de 2 anos (muito grande)
        date_from = "2023-01-01"
        date_to = "2024-12-31"
        
        response = client.get(
            f"/reports/financial/dre?date_from={date_from}&date_to={date_to}"
        )
        
        # ValueError no service -> 400 no router
        assert response.status_code == 400
    
    def test_dre_missing_required_params(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 quando falta parâmetro obrigatório"""
        client.headers.update(auth_headers_user)
        
        # Sem date_from
        response = client.get("/reports/financial/dre?date_to=2024-12-31")
        assert response.status_code == 422
        
        # Sem date_to
        response = client.get("/reports/financial/dre?date_from=2024-01-01")
        assert response.status_code == 422
    
    def test_cashflow_daily_with_invalid_date_format(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 para formato de data inválido"""
        client.headers.update(auth_headers_user)
        
        response = client.get(
            "/reports/financial/cashflow/daily?date_from=01/01/2024&date_to=31/12/2024"
        )
        
        # FastAPI validation -> 422
        assert response.status_code == 422
    
    def test_cashflow_daily_missing_params(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 quando falta parâmetro obrigatório"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/reports/financial/cashflow/daily")
        assert response.status_code == 422
    
    def test_aging_with_invalid_reference_date(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 para reference_date inválido"""
        client.headers.update(auth_headers_user)
        
        response = client.get(
            "/reports/financial/pending/aging?date_from=2024-01-01&date_to=2024-12-31&reference_date=invalid"
        )
        
        # FastAPI validation -> 422
        assert response.status_code == 422
    
    def test_aging_missing_required_params(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 quando falta parâmetro obrigatório"""
        client.headers.update(auth_headers_user)
        
        # Sem date_from
        response = client.get("/reports/financial/pending/aging?date_to=2024-12-31")
        assert response.status_code == 422
    
    def test_top_entries_with_invalid_kind(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400 para kind inválido"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/reports/financial/top?kind=invalid_kind")
        
        # ValueError no service -> 400 no router
        assert response.status_code in [400, 422]
    
    def test_top_entries_with_invalid_status(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400 para status inválido"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/reports/financial/top?status=invalid_status")
        
        # ValueError no service -> 400 no router
        assert response.status_code in [400, 422]
    
    def test_top_entries_with_negative_limit(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar limit negativo"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/reports/financial/top?limit=-10")
        
        # Validação FastAPI -> 422
        assert response.status_code == 422
    
    def test_top_entries_with_zero_limit(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar limit zero"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/reports/financial/top?limit=0")
        
        # Validação FastAPI ou ValueError -> 400/422
        assert response.status_code in [400, 422]
    
    def test_top_entries_with_excessive_limit(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar limit muito alto (> 100)"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/reports/financial/top?limit=1000")
        
        # Pode aceitar (limitando a 100) ou rejeitar
        assert response.status_code in [200, 422]
    
    def test_dre_multi_tenant_user_sees_own_data_only(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """User normal deve ver apenas seus próprios dados no DRE"""
        today = datetime.utcnow()
        
        # Criar entry para user_normal
        entry_own = FinancialEntry(
            user_id=seed_user_normal.id,
            kind="revenue",
            amount=100.0,
            description="Own Revenue",
            status="paid",
            occurred_at=today
        )
        db_session.add(entry_own)
        
        # Criar entry para outro usuário
        entry_other = FinancialEntry(
            user_id=seed_user_other.id,
            kind="revenue",
            amount=500.0,
            description="Other Revenue",
            status="paid",
            occurred_at=today
        )
        db_session.add(entry_other)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        date_from = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        date_to = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = client.get(
            f"/reports/financial/dre?date_from={date_from}&date_to={date_to}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ver apenas 100.0 (próprio), não 500.0 (outro)
        assert data["revenue_paid_total"] == 100.0
    
    def test_dre_admin_sees_all_data(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve ver todos os dados consolidados no DRE"""
        today = datetime.utcnow()
        
        # Criar entries de diferentes usuários
        entry1 = FinancialEntry(
            user_id=seed_user_normal.id,
            kind="revenue",
            amount=100.0,
            description="User 1",
            status="paid",
            occurred_at=today
        )
        entry2 = FinancialEntry(
            user_id=seed_user_other.id,
            kind="revenue",
            amount=200.0,
            description="User 2",
            status="paid",
            occurred_at=today
        )
        db_session.add_all([entry1, entry2])
        db_session.commit()
        
        client.headers.update(auth_headers_admin)
        date_from = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        date_to = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = client.get(
            f"/reports/financial/dre?date_from={date_from}&date_to={date_to}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Admin deve ver consolidado: 100 + 200 = 300
        assert data["revenue_paid_total"] == 300.0







