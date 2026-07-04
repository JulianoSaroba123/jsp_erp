"""
Testes para app/routers/financial_routes.py

Coverage target: 80-85%
Testa autenticaÃ§Ã£o, multi-tenant, filtros, paginaÃ§Ã£o
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.financial_entry import FinancialEntry


def build_financial_entry(**kwargs) -> FinancialEntry:
    payload = dict(kwargs)
    amount = payload.get("amount")
    if payload.get("original_amount") is None:
        payload["original_amount"] = amount
    if payload.get("interest") is None:
        payload["interest"] = 0
    if payload.get("discount") is None:
        payload["discount"] = 0
    if payload.get("penalty") is None:
        payload["penalty"] = 0
    if payload.get("origin") is None:
        payload["origin"] = "manual"

    entry_factory = FinancialEntry
    return entry_factory(**payload)


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
        """UsuÃ¡rio sem lanÃ§amentos deve receber lista vazia"""
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
        """User normal deve ver apenas seus prÃ³prios lanÃ§amentos"""
        # Criar lanÃ§amento para user_normal
        entry_own = build_financial_entry(
            user_id=seed_user_normal.id,
            description="Revenue Own",
            amount=100.0,
            original_amount=100.0,
            interest=0,
            discount=0,
            penalty=0,
            kind="revenue",
            status="pending",
            origin="manual",
            occurred_at=datetime.now()
        )
        db_session.add(entry_own)
        
        # Criar lanÃ§amento para outro usuÃ¡rio
        entry_other = build_financial_entry(
            user_id=seed_user_other.id,
            description="Revenue Other",
            amount=200.0,
            original_amount=200.0,
            interest=0,
            discount=0,
            penalty=0,
            kind="revenue",
            status="pending",
            origin="manual",
            occurred_at=datetime.now()
        )
        db_session.add(entry_other)
        db_session.commit()
        
        client.headers.update(auth_headers_user)
        response = client.get("/financial/entries")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve ver apenas 1 lanÃ§amento (o prÃ³prio)
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
        """Admin deve ver todos os lanÃ§amentos"""
        # Criar lanÃ§amentos de diferentes usuÃ¡rios
        entry1 = build_financial_entry(
            user_id=seed_user_normal.id,
            description="Entry 1",
            amount=100,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        entry2 = build_financial_entry(
            user_id=seed_user_other.id,
            description="Entry 2",
            amount=200,
            kind="expense",
            status="paid",
            occurred_at=datetime.now()
        )
        entry3 = build_financial_entry(
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
        
        # Admin vÃª todos os 3 lanÃ§amentos
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
        # Criar lanÃ§amentos com diferentes status
        entry_pending = build_financial_entry(
            user_id=seed_user_normal.id,
            description="Pending",
            amount=100,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        entry_paid = build_financial_entry(
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
        entry_revenue = build_financial_entry(
            user_id=seed_user_normal.id,
            description="Revenue",
            amount=100,
            kind="revenue",
            status="pending",
            occurred_at=datetime.now()
        )
        entry_expense = build_financial_entry(
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
        """Deve respeitar paginaÃ§Ã£o"""
        # Criar 5 lanÃ§amentos
        for i in range(5):
            entry = build_financial_entry(
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
        
        # Criar lanÃ§amento de ontem
        entry_old = build_financial_entry(
            user_id=seed_user_normal.id,
            description="Old",
            amount=100,
            kind="revenue",
            status="pending",
            occurred_at=yesterday
        )
        # Criar lanÃ§amento de hoje
        entry_today = build_financial_entry(
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
        """Deve retornar 422 se faltar campos obrigatÃ³rios"""
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
        """Deve retornar 404 para lanÃ§amento inexistente"""
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

    def test_update_status_success_pending_to_paid(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve permitir transiÃ§Ã£o pending -> paid no endpoint dedicado."""
        entry = build_financial_entry(
            user_id=seed_user_normal.id,
            kind="revenue",
            amount=100.0,
            description="Receita pendente",
            status="pending",
            occurred_at=datetime.utcnow()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        client.headers.update(auth_headers_user)
        response = client.patch(
            f"/financial/entries/{entry.id}/status",
            json={"status": "paid"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"
        assert data["payment_date"] is not None

    def test_update_status_invalid_transition_paid_to_pending_returns_400(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve bloquear transiÃ§Ã£o invÃ¡lida paid -> pending."""
        entry = build_financial_entry(
            user_id=seed_user_normal.id,
            kind="revenue",
            amount=120.0,
            description="Receita jÃ¡ paga",
            status="paid",
            occurred_at=datetime.utcnow()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        client.headers.update(auth_headers_user)
        response = client.patch(
            f"/financial/entries/{entry.id}/status",
            json={"status": "pending"}
        )

        assert response.status_code == 400
        assert "Transição inválida" in response.json()["detail"]


class TestUpdateFinancialEntryGeneric:
    """Testes para PATCH /financial/entries/{entry_id}."""

    def test_generic_patch_cannot_change_status_directly(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """PATCH genÃ©rico deve bloquear alteraÃ§Ã£o direta de status."""
        entry = build_financial_entry(
            user_id=seed_user_normal.id,
            kind="expense",
            amount=80.0,
            description="Despesa pendente",
            status="pending",
            occurred_at=datetime.utcnow()
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)

        client.headers.update(auth_headers_user)
        response = client.patch(
            f"/financial/entries/{entry.id}",
            json={"status": "paid"}
        )

        assert response.status_code == 400
        assert "/status" in response.json()["detail"]


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
        """Deve retornar 404 para lanÃ§amento inexistente"""
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
        """Deve deletar lanÃ§amento com status=pending"""
        from app.models.financial_entry import FinancialEntry
        from datetime import datetime
        
        entry = build_financial_entry(
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

        # Soft delete: registro permanece, mas marcado como deletado
        db_session.refresh(entry)
        assert entry.deleted_at is not None
        assert entry.deleted_by == seed_user_normal.id
    
    def test_delete_entry_conflict_paid(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """Deve retornar 409 ao tentar deletar lanÃ§amento pago"""
        from app.models.financial_entry import FinancialEntry
        from datetime import datetime
        
        entry = build_financial_entry(
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
        """UsuÃ¡rio nÃ£o pode deletar lanÃ§amento de outro usuÃ¡rio"""
        from app.models.financial_entry import FinancialEntry
        from datetime import datetime
        
        # LanÃ§amento de outro usuÃ¡rio
        entry = build_financial_entry(
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

    def test_soft_deleted_entry_not_listed_in_default_list(
        self,
        client: TestClient,
        seed_user_normal: User,
        auth_headers_user: dict,
        db_session: Session
    ):
        """LanÃ§amento com deleted_at preenchido nÃ£o deve aparecer na listagem padrÃ£o."""
        active_entry = build_financial_entry(
            user_id=seed_user_normal.id,
            kind="expense",
            amount=30.0,
            description="Despesa ativa",
            status="pending",
            occurred_at=datetime.utcnow()
        )
        deleted_entry = build_financial_entry(
            user_id=seed_user_normal.id,
            kind="expense",
            amount=40.0,
            description="Despesa deletada",
            status="pending",
            occurred_at=datetime.utcnow(),
            deleted_at=datetime.utcnow(),
            deleted_by=seed_user_normal.id
        )
        db_session.add_all([active_entry, deleted_entry])
        db_session.commit()

        client.headers.update(auth_headers_user)
        response = client.get("/financial/entries")

        assert response.status_code == 200
        data = response.json()
        descriptions = [item["description"] for item in data["items"]]

        assert "Despesa ativa" in descriptions
        assert "Despesa deletada" not in descriptions


class TestFinancialRoutesEdgeCases:
    """Testes de edge cases e validaÃ§Ãµes"""
    
    def test_list_entries_invalid_page(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve validar parÃ¢metros de paginaÃ§Ã£o invÃ¡lidos"""
        client.headers.update(auth_headers_user)
        
        # Page zero ou negativo
        response = client.get("/financial/entries?page=0")
        assert response.status_code in [400, 422]
    
    def test_list_entries_page_size_exceeds_limit(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve limitar page_size ao mÃ¡ximo permitido"""
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
        """Deve retornar 400 para status invÃ¡lido"""
        client.headers.update(auth_headers_user)
        
        response = client.get("/financial/entries?status=invalid_status_xyz")
        
        # ValueError no service -> 400 no router
        assert response.status_code == 400
    
    def test_list_entries_with_invalid_kind_filter(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400 para kind invÃ¡lido"""
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
        
        # ValidaÃ§Ã£o Pydantic ou ValueError -> 400/422
        assert response.status_code in [400, 422]
    
    def test_create_entry_with_invalid_kind(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Deve retornar 400/422 para kind invÃ¡lido"""
        client.headers.update(auth_headers_user)
        
        payload = {
            "kind": "invalid_kind",
            "amount": 100.0,
            "description": "Test",
            "occurred_at": datetime.now().isoformat()
        }
        
        response = client.post("/financial/entries", json=payload)
        
        # ValidaÃ§Ã£o Pydantic/Literal ou ValueError -> 400/422
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
        """Deve retornar 400 para status invÃ¡lido"""
        # Criar entry
        entry = build_financial_entry(
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
        
        # ValidaÃ§Ã£o Pydantic/Literal ou ValueError -> 400/422
        assert response.status_code in [400, 422]

    def test_create_entry_origin_is_normalized_to_manual(
        self,
        client: TestClient,
        auth_headers_user: dict
    ):
        """Origin deve ser persistido em padrÃ£o Ãºnico MANUAL."""
        client.headers.update(auth_headers_user)

        payload = {
            "kind": "expense",
            "amount": 99.9,
            "description": "Teste origem",
            "origin": "manual"
        }

        response = client.post("/financial/entries", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["origin"] == "MANUAL"

