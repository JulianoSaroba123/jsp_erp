"""
Testes para PATCH /orders/{id} - ETAPA 5

Cobertura:
1. Atualizar apenas description (total intacto)
2. Atualizar total com financial pending (deve atualizar amount)
3. Atualizar total com financial paid (deve bloquear)  
4. Atualizar total para 0 (deve cancelar financial pending)
5. Atualizar total com financial canceled (deve reabrir para pending)
6. Atualizar order de outro user (anti-enumeration 404
7. Atualizar total > 0 sem financial (deve criar entry)
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry


@pytest.mark.integration
@pytest.mark.orders
def test_patch_description_only(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 1: Atualizar apenas description (total intacto).
    
    Expected:
    - description alterada
    - total mantido
    - updated_at atualizado
    - 200 OK
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Descrição original",
        total=Decimal("100.00")
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"description": "Descrição atualizada"}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Descrição atualizada"
    assert Decimal(data["total"]) == Decimal("100.00")


@pytest.mark.integration
@pytest.mark.orders
@pytest.mark.financial
def test_patch_total_pending_updates_financial(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 2: Atualizar total com financial entry pending (deve atualizar amount).
    
    Expected:
    - order.total atualizado
    - financial_entry.amount atualizado
    - financial_entry.status mantém 'pending'
    - 200 OK
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=Decimal("100.00")
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=Decimal("100.00"),
        description="Auto"
    )
    db_session.add(financial)
    db_session.commit()
    financial_id = financial.id
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 200.00}
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verificar financial entry atualizada
    db_session.expire_all()  # Forçar reload do banco
    updated_financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.id == financial_id
    ).first()
    
    assert updated_financial.amount == Decimal("200.00")
    assert updated_financial.status == "pending"


@pytest.mark.integration
@pytest.mark.orders
@pytest.mark.financial
def test_patch_total_paid_blocked(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 3: Atualizar total com financial entry paid (deve bloquear).
    
    Expected:
    - 400 Bad Request
    - Mensagem contém "pago" or "paid"
    - Financial entry mantém valores originais
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=Decimal("100.00")
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",  # PAID
        amount=Decimal("100.00"),
        description="Auto"
    )
    db_session.add(financial)
    db_session.commit()
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 200.00}
    )
    
    # Assert
    assert response.status_code == 400
    assert "pago" in response.json()["detail"].lower() or "paid" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.orders
@pytest.mark.financial
def test_patch_cancel_when_zero(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 4: Atualizar total para 0 (deve cancelar financial pending).
    
    Expected:
    - order.total = 0
    - financial_entry.status = 'canceled'
    - 200 OK
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=Decimal("100.00")
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=Decimal("100.00"),
        description="Auto"
    )
    db_session.add(financial)
    db_session.commit()
    financial_id = financial.id
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 0}
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verificar financial entry cancelada
    db_session.expire_all()
    updated_financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.id == financial_id
    ).first()
    
    assert updated_financial.status == "canceled"


@pytest.mark.integration
@pytest.mark.orders
@pytest.mark.financial
def test_patch_reopen_canceled(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 5: Atualizar total com financial canceled (deve reabrir para pending).
    
    Expected:
    - order.total atualizado
    - financial_entry.amount atualizado
    - financial_entry.status = 'pending' (reaberto)
    - 200 OK
    """
    # Arrange
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=Decimal("100.00")
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="canceled",  # CANCELED
        amount=Decimal("100.00"),
        description="Auto"
    )
    db_session.add(financial)
    db_session.commit()
    financial_id = financial.id
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 150.00}
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verificar financial entry reaberta
    db_session.expire_all()
    updated_financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.id == financial_id
    ).first()
    
    assert updated_financial.amount == Decimal("150.00")
    assert updated_financial.status == "pending"  # REABERTO


@pytest.mark.integration
@pytest.mark.orders
def test_patch_multitenant_404(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User,
    auth_headers_user: dict
):
    """
    Test 6: Atualizar order de outro user (anti-enumeration 404).
    
    Expected:
    - 404 Not Found (não 403 Forbidden)
    - Order não alterada no banco
    """
    # Arrange: Order pertence a seed_user_other
    order = Order(
        user_id=seed_user_other.id,
        description="Other user order",
        total=Decimal("100.00")
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    original_description = order.description
    
    # Act: Tentar atualizar como seed_user_normal
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"description": "Hacked"}
    )
    
    # Assert
    assert response.status_code == 404  # Não 403!
    
    # Verificar que order não foi alterada
    db_session.expire_all()
    order_check = db_session.query(Order).filter(Order.id == order.id).first()
    assert order_check.description == original_description


@pytest.mark.integration
@pytest.mark.orders
@pytest.mark.financial
def test_patch_create_financial_if_missing(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test 7: Atualizar total > 0 sem financial entry (deve criar).
    
    Expected:
    - order.total atualizado
    - Nova financial_entry criada
    - financial_entry.amount = novo total
    - financial_entry.status = 'pending'
    - financial_entry.kind = 'revenue'
    - 200 OK
    """
    # Arrange: Order sem financial entry
    order = Order(
        user_id=seed_user_normal.id,
        description="Order test",
        total=Decimal("0.00")
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    # Act
    response = client.patch(
        f"/orders/{order.id}",
        headers=auth_headers_user,
        json={"total": 250.00}
    )
    
    # Assert
    assert response.status_code == 200
    
    # Verificar financial entry criada
    db_session.expire_all()
    financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.order_id == order.id
    ).first()
    
    assert financial is not None
    assert financial.amount == Decimal("250.00")
    assert financial.status == "pending"
    assert financial.kind == "revenue"
    assert financial.user_id == seed_user_normal.id
