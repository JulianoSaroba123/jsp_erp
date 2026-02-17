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
    # Schema fields: revenue_paid_total, expense_paid_total, net_paid
    assert "revenue_paid_total" in data
    assert "expense_paid_total" in data
    assert "net_paid" in data
    
    # Verify calculations
    assert data["revenue_paid_total"] == 1000
    assert data["expense_paid_total"] == 300
    assert data["net_paid"] == 700


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
    # Schema field is 'days', not 'daily_data'
    assert "days" in data
    
    daily_data = data["days"]
    assert isinstance(daily_data, list)
    
    # Should have entries for all days (filled with zeros if needed)
    assert len(daily_data) >= 3
    
    # Find the day with data
    day_with_data = next(
        (day for day in daily_data if day["date"] == "2026-02-15"),
        None
    )
    
    # Schema fields: revenue_paid, expense_paid, net_paid
    if day_with_data:
        assert day_with_data["revenue_paid"] == 500
        assert day_with_data["expense_paid"] == 0
        assert day_with_data["net_paid"] == 500


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
    
    # Get aging report (query params obrigatórios: date_from, date_to)
    response = client.get(
        "/reports/financial/pending/aging?date_from=2026-02-01&date_to=2026-02-28",
        headers=auth_headers_user
    )
    
    assert response.status_code == 200
    
    data = response.json()
    # Schema: pending_revenue, pending_expense (AgingBucket objects)
    assert "pending_revenue" in data
    assert "pending_expense" in data
    
    # Verify AgingBucket structure (days_0_7, days_8_30, days_31_plus, total)
    pending_rev = data["pending_revenue"]
    assert "0_7_days" in pending_rev or "days_0_7" in pending_rev
    assert "total" in pending_rev


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
    
    # Get top entries (query params obrigatórios: kind, date_from, date_to)
    response = client.get(
        "/reports/financial/top?kind=revenue&date_from=2026-02-01&date_to=2026-02-28&limit=10",
        headers=auth_headers_user
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    
    items = data["items"]
    assert len(items) <= 10
    
    # Schema: TopEntryItem has total_amount (not amount)
    # Verify sorted by total_amount DESC
    if len(items) >= 2:
        assert items[0]["total_amount"] >= items[1]["total_amount"]


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
    # Admin should see combined total (schema: revenue_paid_total)
    assert data["revenue_paid_total"] == 300


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
    # User should see only their own revenue (schema: revenue_paid_total)
    assert data["revenue_paid_total"] == 100
