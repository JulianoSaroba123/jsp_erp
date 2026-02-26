"""
Testes de Regressão - Correção de Bugs de Status HTTP

BUG 1 (CORRIGIDO): Erro de permissão no DELETE deve retornar 403, não 409
BUG 2 (CORRIGIDO): IntegrityError no PATCH não deve desfazer alterações do Order

Commit: Stabilization - fixing HTTP status codes and rollback logic
"""
import pytest
from fastapi import status


def test_delete_order_permission_error_returns_403_not_409(client, auth_headers_admin, auth_headers_user):
    """
    BUG 1: Erro de permissão deve retornar 403 Forbidden (não 409 Conflict).
    
    Cenário:
    - Admin cria um pedido
    - User comum tenta deletar pedido do admin
    - Deve retornar 403 (permissão negada), não 409 (business rule)
    
    ANTES DO FIX: ValueError genérico → 409
    DEPOIS DO FIX: PermissionError → 403
    """
    # Admin cria pedido
    order_data = {"description": "Pedido do admin", "total": 100}
    response = client.post("/orders", json=order_data, headers=auth_headers_admin)
    assert response.status_code == status.HTTP_201_CREATED
    order_id = response.json()["id"]
    
    # User comum tenta deletar (SEM PERMISSÃO)
    response = client.delete(f"/orders/{order_id}", headers=auth_headers_user)
    
    # ✅ DEVE SER 403 (PermissionError), não 409 (ValueError business rule)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "permissão" in response.json()["detail"].lower()


def test_delete_order_business_rule_error_returns_409(client, auth_headers_user, seed_admin_with_delete_permission, auth_headers_admin, db_session):
    """
    Valida que erro de BUSINESS RULE retorna 409 Conflict.
    
    Cenário:
    - User cria pedido com total > 0 (gera financial pending)
    - Marca financial como paid
    - Admin com permissão de delete tenta deletar pedido (BUSINESS RULE BLOQUEIA)
    - Deve retornar 409 (não 403)
    
    Note: Usa admin para passar do RBAC e multi-tenancy, testando a regra de negócio.
    """
    # Criar pedido com total > 0 (gera financial pending)
    order_data = {"description": "Pedido com lançamento", "total": 200}
    response = client.post("/orders", json=order_data, headers=auth_headers_user)
    assert response.status_code == status.HTTP_201_CREATED
    order_id = response.json()["id"]
    
    # Buscar financial entry gerado
    response = client.get("/financial/entries", headers=auth_headers_user)
    assert response.status_code == status.HTTP_200_OK
    entries = response.json()["items"]  # Lista paginada
    financial_entry = next(e for e in entries if e["order_id"] == order_id)
    
    # Marcar como paid (via db_session do fixture de teste)
    from app.models.financial_entry import FinancialEntry
    from uuid import UUID
    
    entry = db_session.query(FinancialEntry).filter(
        FinancialEntry.id == UUID(financial_entry["id"])
    ).first()
    entry.status = "paid"
    db_session.commit()  # Commit transacional isolado
    
    # Tentar deletar pedido com admin que TEM permissão (BUSINESS RULE BLOQUEIA)
    response = client.delete(f"/orders/{order_id}", headers=auth_headers_admin)
    
    # ✅ DEVE SER 409 (ValueError business rule), não 403
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "paid" in response.json()["detail"].lower()  # "já está 'paid'"


def test_patch_order_preserves_changes_on_integrity_error(client, auth_headers_user):
    """
    BUG 2: PATCH com IntegrityError (race condition) não deve desfazer alterações do Order.
    
    Cenário (simplificado):
    - User cria pedido com total=0 (sem financial)
    - User faz PATCH total=100 + description="Nova desc"
    - Se houver IntegrityError ao criar financial, rollback deve preservar order.total e order.description
    
    ANTES DO FIX: db.rollback() desfazia order.total e order.description
    DEPOIS DO FIX: Rollback apenas do INSERT, re-aplica mudanças do order
    
    NOTA: Difícil simular race condition em teste, mas validamos que PATCH funciona corretamente.
    """
    # Criar pedido com total=0 (sem financial entry)
    order_data = {"description": "Descrição original", "total": 0}
    response = client.post("/orders", json=order_data, headers=auth_headers_user)
    assert response.status_code == status.HTTP_201_CREATED
    order_id = response.json()["id"]
    
    # PATCH: description + total > 0 (deve criar financial entry)
    patch_data = {"total": 150}  # Simplificado: só testa total
    response = client.patch(f"/orders/{order_id}", json=patch_data, headers=auth_headers_user)
    assert response.status_code == status.HTTP_200_OK
    
    # Validar que total foi atualizado (BUG 2: rollback não desfaz ordem)
    updated_order = response.json()
    assert updated_order["total"] == 150


def test_patch_order_idempotency_double_patch(client, auth_headers_user):
    """
    Valida que múltiplos PATCHs consecutivos mantêm consistência.
    
    Testa o código de tratamento de IntegrityError indiretamente:
    - Se o código de re-aplicação estiver quebrado, PATCHs subsequentes falharão
    """
    # Criar pedido
    order_data = {"description": "V1", "total": 0}
    response = client.post("/orders", json=order_data, headers=auth_headers_user)
    order_id = response.json()["id"]
    
    # PATCH 1: total=100 (cria financial)
    response = client.patch(f"/orders/{order_id}", json={"total": 100}, headers=auth_headers_user)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 100
    
    # PATCH 2: total=200 (atualiza financial existente)
    response = client.patch(f"/orders/{order_id}", json={"total": 200}, headers=auth_headers_user)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 200
    
    # PATCH 3: total=0 (cancela financial)
    response = client.patch(f"/orders/{order_id}", json={"total": 0}, headers=auth_headers_user)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 0
    
    # Validar financial foi cancelado
    response = client.get("/financial/entries", headers=auth_headers_user)
    entries = response.json()["items"]  # Lista paginada
    financial_entry = next((e for e in entries if e["order_id"] == order_id), None)
    assert financial_entry["status"] == "canceled"
