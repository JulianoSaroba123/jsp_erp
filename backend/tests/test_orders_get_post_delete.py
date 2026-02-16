"""
Tests for orders endpoints (ETAPA 1).

Tests:
- POST /orders creates order (and financial entry if total > 0)
- GET /orders respects multi-tenant (user sees only their orders)
- DELETE /orders works when financial not paid
- DELETE /orders blocked when financial is paid
- Anti-enumeration: accessing other user's order returns 404
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry


@pytest.mark.integration
def test_create_order_with_zero_total_no_financial(
    client: TestClient,
    db_session: Session,
    auth_headers_user: dict
):
    """
    Test creating order with total=0 does NOT create financial entry.
    """
    response = client.post(
        "/orders",
        headers=auth_headers_user,
        json={
            "description": "Order without payment",
            "total": 0
        }
    )
    
    assert response.status_code == 201
    
    data = response.json()
    assert data["description"] == "Order without payment"
    assert data["total"] == 0
    
    # Verify no financial entry created
    order_id = data["id"]
    financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.order_id == order_id
    ).first()
    
    assert financial is None


@pytest.mark.integration
def test_create_order_with_positive_total_creates_financial(
    client: TestClient,
    db_session: Session,
    auth_headers_user: dict
):
    """
    Test creating order with total > 0 automatically creates financial entry.
    """
    response = client.post(
        "/orders",
        headers=auth_headers_user,
        json={
            "description": "Order with payment",
            "total": 150.50
        }
    )
    
    assert response.status_code == 201
    
    data = response.json()
    order_id = data["id"]
    
    # Verify financial entry created
    financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.order_id == order_id
    ).first()
    
    assert financial is not None
    assert financial.amount == 150.50
    assert financial.kind == "revenue"
    assert financial.status == "pending"
    assert financial.description == "Receita gerada automaticamente pelo pedido"


@pytest.mark.integration
def test_get_orders_multi_tenant(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User,
    auth_headers_user: dict
):
    """
    Test GET /orders returns only current user's orders.
    """
    # Create order for seed_user_normal
    order1 = Order(
        user_id=seed_user_normal.id,
        description="User's order",
        total=100
    )
    db_session.add(order1)
    
    # Create order for seed_user_other
    order2 = Order(
        user_id=seed_user_other.id,
        description="Other user's order",
        total=200
    )
    db_session.add(order2)
    db_session.commit()
    
    # Get orders as seed_user_normal
    response = client.get("/orders", headers=auth_headers_user)
    
    assert response.status_code == 200
    
    data = response.json()
    items = data["items"]
    
    # Should only see own order
    assert len(items) == 1
    assert items[0]["description"] == "User's order"


@pytest.mark.integration
def test_get_orders_admin_sees_all(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User,
    auth_headers_admin: dict
):
    """
    Test admin sees all orders (no multi-tenant filter).
    """
    # Create orders for different users
    order1 = Order(user_id=seed_user_normal.id, description="Order 1", total=100)
    order2 = Order(user_id=seed_user_other.id, description="Order 2", total=200)
    db_session.add_all([order1, order2])
    db_session.commit()
    
    # Get orders as admin
    response = client.get("/orders", headers=auth_headers_admin)
    
    assert response.status_code == 200
    
    data = response.json()
    items = data["items"]
    
    # Admin sees all orders
    assert len(items) == 2


@pytest.mark.integration
def test_delete_order_with_pending_financial_succeeds(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test DELETE /orders/{id} works when financial entry is pending.
    """
    # Create order with financial entry
    order = Order(
        user_id=seed_user_normal.id,
        description="Order to delete",
        total=100
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100,
        description="Auto-generated"
    )
    db_session.add(financial)
    db_session.commit()
    
    # Delete order
    response = client.delete(f"/orders/{order.id}", headers=auth_headers_user)
    
    assert response.status_code == 200


@pytest.mark.integration
def test_delete_order_with_paid_financial_blocked(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test DELETE /orders/{id} blocked when financial entry is paid.
    """
    # Create order with PAID financial entry
    order = Order(
        user_id=seed_user_normal.id,
        description="Order with paid financial",
        total=100
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    financial = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",  # PAID
        amount=100,
        description="Auto-generated"
    )
    db_session.add(financial)
    db_session.commit()
    
    # Try to delete order
    response = client.delete(f"/orders/{order.id}", headers=auth_headers_user)
    
    # Should be blocked (400 or 409)
    assert response.status_code in [400, 409]


@pytest.mark.integration
def test_anti_enumeration_other_user_order_returns_404(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User,
    auth_headers_user: dict
):
    """
    Test accessing another user's order returns 404 (not 403).
    
    This prevents user enumeration attacks.
    """
    # Create order owned by seed_user_other
    order = Order(
        user_id=seed_user_other.id,
        description="Other user's order",
        total=100
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    # Try to access as seed_user_normal
    response = client.get(f"/orders/{order.id}", headers=auth_headers_user)
    
    # Should return 404 (not 403)
    assert response.status_code == 404


@pytest.mark.integration
def test_delete_nonexistent_order_returns_404(
    client: TestClient,
    auth_headers_user: dict
):
    """
    Test deleting non-existent order returns 404.
    """
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/orders/{fake_uuid}", headers=auth_headers_user)
    
    assert response.status_code == 404
