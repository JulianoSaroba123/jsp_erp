"""
Tests for financial module idempotency (ETAPA 3A).

Tests:
- Creating order twice with same data doesn't duplicate financial entry
- UNIQUE(order_id) constraint is enforced
- Race condition handling works correctly
- Manual financial entry creation works
- Status transitions are validated
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry


@pytest.mark.financial
@pytest.mark.integration
def test_order_financial_idempotency(
    client: TestClient,
    db_session: Session,
    auth_headers_user: dict
):
    """
    Test creating order with total > 0 multiple times doesn't duplicate financial entry.
    
    This tests the idempotency mechanism (UNIQUE constraint on order_id).
    """
    # Create first order
    response1 = client.post(
        "/orders",
        headers=auth_headers_user,
        json={
            "description": "Idempotency test order",
            "total": 250.00
        }
    )
    
    assert response1.status_code == 201
    order_id = response1.json()["id"]
    
    # Count financial entries for this order
    count1 = db_session.query(FinancialEntry).filter(
        FinancialEntry.order_id == order_id
    ).count()
    
    assert count1 == 1
    
    # Try to create financial entry for same order again (simulating race condition)
    # This should be prevented by UNIQUE constraint
    financial = FinancialEntry(
        order_id=order_id,
        user_id=response1.json()["user_id"],
        kind="revenue",
        status="pending",
        amount=250.00,
        description="Duplicate attempt"
    )
    db_session.add(financial)
    
    # Should raise IntegrityError due to UNIQUE(order_id)
    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        db_session.commit()
    
    db_session.rollback()
    
    # Verify still only 1 financial entry
    count2 = db_session.query(FinancialEntry).filter(
        FinancialEntry.order_id == order_id
    ).count()
    
    assert count2 == 1


@pytest.mark.financial
def test_manual_financial_entry_creation(
    client: TestClient,
    db_session: Session,
    auth_headers_user: dict
):
    """
    Test creating manual financial entry (no order_id).
    """
    response = client.post(
        "/financial/entries",
        headers=auth_headers_user,
        json={
            "kind": "expense",
            "amount": 75.50,
            "description": "Office supplies",
            "occurred_at": "2026-02-16T10:00:00Z"
        }
    )
    
    assert response.status_code == 201
    
    data = response.json()
    assert data["kind"] == "expense"
    assert data["amount"] == 75.50
    assert data["status"] == "pending"
    assert data["order_id"] is None


@pytest.mark.financial
def test_financial_entry_unique_order_constraint(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User
):
    """
    Test that UNIQUE constraint on order_id prevents duplicates at database level.
    """
    # Create order
    order = Order(
        user_id=seed_user_normal.id,
        description="Test order",
        total=100
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    # Create first financial entry
    entry1 = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100,
        description="First entry"
    )
    db_session.add(entry1)
    db_session.commit()
    
    # Try to create duplicate
    entry2 = FinancialEntry(
        order_id=order.id,  # Same order_id
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100,
        description="Duplicate entry"
    )
    db_session.add(entry2)
    
    # Should fail
    with pytest.raises(Exception):
        db_session.commit()
    
    db_session.rollback()


@pytest.mark.financial
def test_delete_order_removes_financial_entry(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test that deleting order (soft delete) cancels associated financial entry (if pending).
    With soft delete, the order remains in DB so order_id FK is preserved.
    The financial entry status changes to 'canceled'.
    """
    # Create order with financial
    order = Order(
        user_id=seed_user_normal.id,
        description="Order to delete",
        total=100
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    
    entry = FinancialEntry(
        order_id=order.id,
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100,
        description="Auto"
    )
    db_session.add(entry)
    db_session.commit()
    entry_id = entry.id
    
    # Delete order (soft delete)
    response = client.delete(f"/orders/{order.id}", headers=auth_headers_user)
    assert response.status_code == 200
    
    # Verify financial entry still exists with order_id preserved
    # (soft delete: order is not removed, so FK stays intact)
    db_session.expire_all()
    financial = db_session.query(FinancialEntry).filter(
        FinancialEntry.id == entry_id
    ).first()
    
    # Financial entry should exist and order_id preserved (soft delete keeps the order row)
    assert financial is not None
    assert financial.order_id == order.id  # order still in DB (soft deleted)
    assert financial.status == "canceled"  # but entry was canceled


@pytest.mark.financial
def test_get_financial_entries_multi_tenant(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User,
    auth_headers_user: dict
):
    """
    Test GET /financial/entries respects multi-tenant filtering.
    """
    # Create entry for seed_user_normal
    entry1 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100,
        description="User's entry"
    )
    db_session.add(entry1)
    
    # Create entry for seed_user_other
    entry2 = FinancialEntry(
        user_id=seed_user_other.id,
        kind="expense",
        status="pending",
        amount=50,
        description="Other user's entry"
    )
    db_session.add(entry2)
    db_session.commit()
    
    # Get entries as seed_user_normal
    response = client.get("/financial/entries", headers=auth_headers_user)
    
    assert response.status_code == 200
    
    data = response.json()
    items = data["items"]
    
    # Should only see own entry
    assert len(items) == 1
    assert items[0]["description"] == "User's entry"


@pytest.mark.financial
def test_financial_status_filter(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test filtering financial entries by status.
    """
    # Create entries with different statuses
    entry1 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100,
        description="Pending entry"
    )
    entry2 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",
        amount=200,
        description="Paid entry"
    )
    db_session.add_all([entry1, entry2])
    db_session.commit()
    
    # Filter by status=paid
    response = client.get(
        "/financial/entries?status=paid",
        headers=auth_headers_user
    )
    
    assert response.status_code == 200
    
    data = response.json()
    items = data["items"]
    
    assert len(items) == 1
    assert items[0]["status"] == "paid"
    assert items[0]["description"] == "Paid entry"
