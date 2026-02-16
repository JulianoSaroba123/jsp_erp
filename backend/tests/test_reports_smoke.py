"""
Smoke tests for reports endpoints (ETAPA 4).

Tests:
- GET /reports/financial/dre returns 200 and expected structure
- GET /reports/financial/cashflow/daily returns time series
- GET /reports/financial/pending/aging returns aging buckets
- GET /reports/financial/top returns top entries
- Multi-tenant filtering works
- Date validation works
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.user import User
from app.models.financial_entry import FinancialEntry


@pytest.mark.reports
@pytest.mark.smoke
def test_dre_report_structure(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test GET /reports/financial/dre returns correct structure.
    """
    # Create sample data
    entry1 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",
        amount=1000,
        description="Revenue 1"
    )
    entry2 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="expense",
        status="paid",
        amount=300,
        description="Expense 1"
    )
    db_session.add_all([entry1, entry2])
    db_session.commit()
    
    # Get DRE report
    response = client.get(
        "/reports/financial/dre?date_from=2026-02-01&date_to=2026-02-28",
        headers=auth_headers_user
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "total_revenue" in data
    assert "total_expense" in data
    assert "net_result" in data
    
    # Verify calculations
    assert data["total_revenue"] == 1000
    assert data["total_expense"] == 300
    assert data["net_result"] == 700


@pytest.mark.reports
@pytest.mark.smoke
def test_cashflow_daily_returns_time_series(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test GET /reports/financial/cashflow/daily returns daily time series.
    """
    # Create entry on specific date
    specific_date = datetime(2026, 2, 15, 12, 0, 0)
    entry = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",
        amount=500,
        description="Revenue",
        occurred_at=specific_date
    )
    db_session.add(entry)
    db_session.commit()
    
    # Get cashflow report
    response = client.get(
        "/reports/financial/cashflow/daily?date_from=2026-02-14&date_to=2026-02-16",
        headers=auth_headers_user
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "daily_data" in data
    
    daily_data = data["daily_data"]
    assert isinstance(daily_data, list)
    
    # Should have entries for all days (filled with zeros if needed)
    assert len(daily_data) >= 3
    
    # Find the day with data
    day_with_data = next(
        (day for day in daily_data if day["date"] == "2026-02-15"),
        None
    )
    
    if day_with_data:
        assert day_with_data["total_revenue"] == 500
        assert day_with_data["total_expense"] == 0
        assert day_with_data["net_cashflow"] == 500


@pytest.mark.reports
@pytest.mark.smoke
def test_pending_aging_buckets(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test GET /reports/financial/pending/aging returns aging buckets.
    """
    # Create pending entries with different ages
    today = datetime.utcnow()
    
    entry1 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=100,
        description="Recent",
        occurred_at=today - timedelta(days=5)
    )
    entry2 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=200,
        description="Old",
        occurred_at=today - timedelta(days=35)
    )
    db_session.add_all([entry1, entry2])
    db_session.commit()
    
    # Get aging report
    response = client.get(
        "/reports/financial/pending/aging",
        headers=auth_headers_user
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "aging_buckets" in data
    
    buckets = data["aging_buckets"]
    assert isinstance(buckets, list)
    assert len(buckets) > 0
    
    # Verify bucket structure
    for bucket in buckets:
        assert "range" in bucket
        assert "count" in bucket
        assert "total_amount" in bucket


@pytest.mark.reports
@pytest.mark.smoke
def test_top_entries_report(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_user: dict
):
    """
    Test GET /reports/financial/top returns top entries by amount.
    """
    # Create entries with different amounts
    entry1 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",
        amount=1000,
        description="Large revenue"
    )
    entry2 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="expense",
        status="paid",
        amount=50,
        description="Small expense"
    )
    entry3 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",
        amount=500,
        description="Medium revenue"
    )
    db_session.add_all([entry1, entry2, entry3])
    db_session.commit()
    
    # Get top entries (limit 10)
    response = client.get(
        "/reports/financial/top?limit=10",
        headers=auth_headers_user
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    
    items = data["items"]
    assert len(items) <= 10
    
    # Verify sorted by amount DESC
    if len(items) >= 2:
        assert items[0]["amount"] >= items[1]["amount"]


@pytest.mark.reports
def test_dre_date_validation_max_range(
    client: TestClient,
    auth_headers_user: dict
):
    """
    Test DRE report rejects date ranges > 366 days.
    """
    response = client.get(
        "/reports/financial/dre?date_from=2026-01-01&date_to=2027-01-03",
        headers=auth_headers_user
    )
    
    # Should reject (400 or 422)
    assert response.status_code in [400, 422]


@pytest.mark.reports
def test_reports_multi_tenant_admin_sees_all(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User,
    auth_headers_admin: dict
):
    """
    Test admin sees all users' data in reports.
    """
    # Create entries for different users
    entry1 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",
        amount=100,
        description="User entry"
    )
    entry2 = FinancialEntry(
        user_id=seed_user_other.id,
        kind="revenue",
        status="paid",
        amount=200,
        description="Other user entry"
    )
    db_session.add_all([entry1, entry2])
    db_session.commit()
    
    # Get DRE as admin
    response = client.get(
        "/reports/financial/dre?date_from=2026-02-01&date_to=2026-02-28",
        headers=auth_headers_admin
    )
    
    assert response.status_code == 200
    
    data = response.json()
    # Admin should see combined total
    assert data["total_revenue"] == 300


@pytest.mark.reports
def test_reports_multi_tenant_user_sees_own_only(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User,
    auth_headers_user: dict
):
    """
    Test normal user sees only their own data in reports.
    """
    # Create entries for different users
    entry1 = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="paid",
        amount=100,
        description="User entry"
    )
    entry2 = FinancialEntry(
        user_id=seed_user_other.id,
        kind="revenue",
        status="paid",
        amount=200,
        description="Other user entry"
    )
    db_session.add_all([entry1, entry2])
    db_session.commit()
    
    # Get DRE as normal user
    response = client.get(
        "/reports/financial/dre?date_from=2026-02-01&date_to=2026-02-28",
        headers=auth_headers_user
    )
    
    assert response.status_code == 200
    
    data = response.json()
    # User should see only their own revenue
    assert data["total_revenue"] == 100
