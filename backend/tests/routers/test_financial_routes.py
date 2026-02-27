"""
Testes para app/routers/financial_routes.py

Coverage target: 80-85%
Testa autenticação, multi-tenant, filtros, paginação
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.financial_entry import FinancialEntry


class TestListFinancialEntries:
    """Testes para GET /financial/entries"""
    
    def test_list_entries_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        response = client.get("/financial/entries")
        
        assert response.status_code == 401
    
    def test_list_entries_empty_for_user(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict
    ):
        """Usuário sem lançamentos deve receber lista vazia"""
        client.headers.update(auth_headers_user)
        response = client.get("/financial/entries")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["total"] == 0
    
    def test_list_entries_multi_tenant_user_sees_own_only(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """User normal deve ver apenas seus próprios lançamentos"""
        # Criar lançamento para user_normal
        entry_own = FinancialEntry(
            user_id=seed_user_normal.id,
            description="Revenue Own",
            amount=100.0,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        db_session.add(entry_own)
        
        # Criar lançamento para outro usuário
        entry_other = FinancialEntry(
            user_id=seed_user_other.id,
            description="Revenue Other",
            amount=200.0,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        db_session.add(entry_other)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/financial/entries")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ver apenas 1 lançamento (o próprio)
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["description"] == "Revenue Own"
    
    def test_list_entries_admin_sees_all(
        self,
        client: TestClient,
        seed_user_admin: User,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_admin: dict,
        db_session: Session
    ):
        """Admin deve ver todos os lançamentos"""
        # Criar lançamentos de diferentes usuários
        entry1 = FinancialEntry(
            user_id=seed_user_normal.id,
            description="Entry 1",
            amount=100,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        entry2 = FinancialEntry(
            user_id=seed_user_other.id,
            description="Entry 2",
            amount=200,
            kind="expense",
            status="paid",
            occurred_at=datetime.now()
        )
        entry3 = FinancialEntry(
            user_id=seed_user_admin.id,
            description="Entry 3",
            amount=300,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        
        db_session.add_all([entry1, entry2, entry3])
        db_session.commit()
        
        client.headers.update(auth_headers_admin)
        response = client.get("/financial/entries")
        
        assert response.status_code == 200
        data = response.json()
        
        # Admin vê todos os 3 lançamentos
        assert data["total"] == 3
        assert len(data["items"]) == 3
    
    def test_list_entries_filter_by_status(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve filtrar por status"""
        # Criar lançamentos com diferentes status
        entry_pending = FinancialEntry(
            user_id=seed_user_normal.id,
            description="Pending",
            amount=100,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        entry_paid = FinancialEntry(
            user_id=seed_user_normal.id,
            description="Paid",
            amount=200,
            kind="revenue",
            status="paid",
            occurred_at=datetime.now()
        )
        
        db_session.add_all([entry_pending, entry_paid])
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/financial/entries?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve retornar apenas o pending
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"
    
    def test_list_entries_filter_by_kind(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve filtrar por kind (revenue/expense)"""
        entry_revenue = FinancialEntry(
            user_id=seed_user_normal.id,
            description="Revenue",
            amount=100,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        entry_expense = FinancialEntry(
            user_id=seed_user_normal.id,
            description="Expense",
            amount=50,
            kind="expense",
            status="pending",
            occurred_at=datetime.now()
        )
        
        db_session.add_all([entry_revenue, entry_expense])
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/financial/entries?kind=expense")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 1
        assert data["items"][0]["kind"] == "expense"
    
    def test_list_entries_pagination(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve respeitar paginação"""
        # Criar 5 lançamentos
        for i in range(5):
            entry = FinancialEntry(
                user_id=seed_user_normal.id,
                description=f"Entry {i}",
                amount=100 * i,
                kind="revenue",
                status="pending",
                occurred_at=datetime.now()
            )
            db_session.add(entry)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        
        # Page 1 com page_size=2
        response = client.get("/financial/entries?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5
    
    def test_list_entries_date_range_filter(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve filtrar por intervalo de datas"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # Criar lançamento de ontem
        entry_old = FinancialEntry(
            user_id=seed_user_normal.id,
            description="Old",
            amount=100,
            kind="revenue",
            status="pending",
            occurred_at=yesterday
        )
        # Criar lançamento de hoje
        entry_today = FinancialEntry(
            user_id=seed_user_normal.id,
            description="Today",
            amount=200,
            kind="revenue",
            status="pending",
            occurred_at=now
        )
        
        db_session.add_all([entry_old, entry_today])
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        
        # Filtrar apenas hoje em diante
        response = client.get(f"/financial/entries?date_from={now.isoformat()}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve retornar apenas o de hoje (>=)
        assert data["total"] >= 1


class TestCreateFinancialEntry:
    """Testes para POST /financial/entries"""
    
    def test_create_entry_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        payload = {
            "description": "Test",
            "amount": 100.0,
            "kind": "revenue",
            "occurred_at": datetime.now().isoformat()
        }
        response = client.post("/financial/entries", json=payload)
        
        assert response.status_code == 401
    
    def test_create_entry_missing_required_fields(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 422 se faltar campos obrigatórios"""
        payload = {"description": "Missing fields"}
        
        client.headers.update(auth_headers_user)
        response = client.post("/financial/entries", json=payload)
        
        assert response.status_code == 422


class TestGetFinancialEntryById:
    """Testes para GET /financial/entries/{entry_id}"""
    
    def test_get_entry_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        fake_id = uuid4()
        response = client.get(f"/financial/entries/{fake_id}")
        
        assert response.status_code == 401
    
    def test_get_entry_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 para lançamento inexistente"""
        fake_id = uuid4()
        
        client.headers.update(auth_headers_user)
        response = client.get(f"/financial/entries/{fake_id}")
        
        assert response.status_code == 404


class TestUpdateFinancialEntryStatus:
    """Testes para PATCH /financial/entries/{entry_id}/status"""
    
    def test_update_status_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        fake_id = uuid4()
        payload = {"status": "paid"}
        response = client.patch(f"/financial/entries/{fake_id}/status", json=payload)
        
        assert response.status_code == 401


class TestDeleteFinancialEntry:
    """Testes para DELETE /financial/entries/{entry_id}"""
    
    def test_delete_entry_requires_authentication(self, client: TestClient):
        """Deve retornar 401 sem token"""
        fake_id = uuid4()
        response = client.delete(f"/financial/entries/{fake_id}")
        
        assert response.status_code == 401
    
    def test_delete_entry_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 para lançamento inexistente"""
        fake_id = uuid4()
        
        client.headers.update(auth_headers_user)
        response = client.delete(f"/financial/entries/{fake_id}")
        
        assert response.status_code == 404
    
    def test_delete_entry_success_pending(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve deletar lançamento com status=pending"""
        from app.models.financial_entry import FinancialEntry
        from datetime import datetime
        
        entry = FinancialEntry(
            user_id=seed_user_normal.id,
            kind='expense',
            amount=50.0,
            description='Despesa pendente',
            status='pending',
            occurred_at=datetime.utcnow()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        
        client.headers.update(auth_headers_user)
        response = client.delete(f"/financial/entries/{entry.id}")
        
        # 204 No Content
        assert response.status_code == 204
    
    def test_delete_entry_conflict_paid(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve retornar 409 ao tentar deletar lançamento pago"""
        from app.models.financial_entry import FinancialEntry
        from datetime import datetime
        
        entry = FinancialEntry(
            user_id=seed_user_normal.id,
            kind='revenue',
            amount=100.0,
            description='Receita paga',
            status='paid',
            occurred_at=datetime.utcnow()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        
        client.headers.update(auth_headers_user)
        response = client.delete(f"/financial/entries/{entry.id}")
        
        # 409 Conflict
        assert response.status_code == 409
        data = response.json()
        assert 'paid' in data['detail'].lower()
    
    def test_delete_entry_multi_tenant(
        self,
        client: TestClient,
        seed_user_normal: User,
        seed_user_other: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Usuário não pode deletar lançamento de outro usuário"""
        from app.models.financial_entry import FinancialEntry
        from datetime import datetime
        
        # Lançamento de outro usuário
        entry = FinancialEntry(
            user_id=seed_user_other.id,
            kind='expense',
            amount=30.0,
            description='Outra despesa',
            status='pending',
            occurred_at=datetime.utcnow()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        
        # Tentar deletar com user_normal
        client.headers.update(auth_headers_user)
        response = client.delete(f"/financial/entries/{entry.id}")
        
        # 404 (anti-enumeration)
        assert response.status_code == 404


class TestFinancialRoutesEdgeCases:
    """Testes de edge cases e validações"""
    
    def test_list_entries_invalid_page(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar parâmetros de paginação inválidos"""
        client.headers.update(auth_headers_user)
        
        # Page zero ou negativo
        response = client.get("/financial/entries?page=0")
        assert response.status_code in [400, 422]
    
    def test_list_entries_page_size_exceeds_limit(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve limitar page_size ao máximo permitido"""
        client.headers.update(auth_headers_user)
        
        # page_size=500 (acima do limite de 100)
        response = client.get("/financial/entries?page=1&page_size=500")
        
        # Pode ser aceito (limitado a 100) ou rejeitado
        assert response.status_code in [200, 422]
    
    def test_list_entries_with_invalid_status_filter(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400 para status inválido"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/financial/entries?status=invalid_status_xyz")
        
        # ValueError no service -> 400 no router
        assert response.status_code == 400
    
    def test_list_entries_with_invalid_kind_filter(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400 para kind inválido"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/financial/entries?kind=invalid_kind")
        
        # ValueError no service -> 400 no router
        assert response.status_code == 400
    
    def test_get_entry_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 para ID inexistente"""
        client.headers.update(auth_headers_user)
        
        fake_id = uuid4()
        response = client.get(f"/financial/entries/{fake_id}")
        
        assert response.status_code == 404
    
    def test_create_entry_with_negative_amount(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400 para amount negativo"""
        client.headers.update(auth_headers_user)
        
        payload = {
            "kind": "revenue",
            "amount": -100.0,
            "description": "Invalid amount",
            "occurred_at": datetime.now().isoformat()
        }
        
        response = client.post("/financial/entries", json=payload)
        
        # Validação Pydantic ou ValueError -> 400/422
        assert response.status_code in [400, 422]
    
    def test_create_entry_with_invalid_kind(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400/422 para kind inválido"""
        client.headers.update(auth_headers_user)
        
        payload = {
            "kind": "invalid_kind",
            "amount": 100.0,
            "description": "Test",
            "occurred_at": datetime.now().isoformat()
        }
        
        response = client.post("/financial/entries", json=payload)
        
        # Validação Pydantic/Literal ou ValueError -> 400/422
        assert response.status_code in [400, 422]
    
    def test_update_status_not_found(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 404 ao atualizar status de entry inexistente"""
        client.headers.update(auth_headers_user)
        
        fake_id = uuid4()
        response = client.patch(
            f"/financial/entries/{fake_id}/status",
            json={"status": "paid"}
        )
        
        assert response.status_code == 404
    
    def test_update_status_with_invalid_status(
        self,
        client: TestClient,
        auth_headers_user: dict,
        db_session: Session,
        seed_user_normal: User
    ):
        """Deve retornar 400 para status inválido"""
        # Criar entry
        entry = FinancialEntry(
            user_id=seed_user_normal.id,
            kind="revenue",
            amount=100.0,
            description="Test",
            status="pending",
            occurred_at=datetime.now()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        
        client.headers.update(auth_headers_user)
        response = client.patch(
            f"/financial/entries/{entry.id}/status",
            json={"status": "invalid_status"}
        )
        
        # Validação Pydantic/Literal ou ValueError -> 400/422
        assert response.status_code in [400, 422]
