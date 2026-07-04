"""
Testes de Audit Log

Valida funcionalidade de rastreamento de ações.

ETAPA 6 - Features Enterprise
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models.user import User
from app.models.order import Order
from app.services.audit_log_service import AuditLogService


@pytest.mark.audit
def test_create_audit_log_manual(
    db_session: Session,
    seed_user_normal: User
):
    """
    Test creating audit log entry manually.
    """
    # Arrange
    order_id = uuid4()
    request_id = "test-request-123"
    
    # Act
    log = AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=order_id,
        request_id=request_id,
        before=None,
        after={"description": "New Order", "total": 100.00}
    )
    
    # Assert
    assert log.id is not None
    assert log.user_id == seed_user_normal.id
    assert log.action == "create"
    assert log.entity_type == "order"
    assert log.entity_id == order_id
    assert log.before is None
    assert log.after["description"] == "New Order"
    assert log.request_id == request_id


@pytest.mark.audit
def test_audit_log_update_records_before_after(
    db_session: Session,
    seed_user_normal: User
):
    """Test update action records both before and after states."""
    order_id = uuid4()
    
    log = AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="update",
        entity_type="order",
        entity_id=order_id,
        request_id="req-456",
        before={"description": "Old", "total": 50.00}, 
        after={"description": "Updated", "total": 75.00}
    )
    
    assert log.before["total"] == 50.00
    assert log.after["total"] == 75.00


@pytest.mark.audit
def test_audit_log_delete_records_before_only(
    db_session: Session,
    seed_user_normal: User
):
    """Test delete action records before state only."""
    order_id = uuid4()
    
    log = AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="delete",
        entity_type="order",
        entity_id=order_id,
        request_id="req-789",
        before={"description": "Deleted Order", "total": 100.00},
        after=None
    )
    
    assert log.before is not None
    assert log.after is None


@pytest.mark.audit
def test_get_logs_no_filters(
    db_session: Session,
    seed_user_normal: User
):
    """Test retrieving logs without filters."""
    # Create some logs
    for i in range(5):
        AuditLogService.log_action(
            db=db_session,
            user_id=seed_user_normal.id,
            action="create",
            entity_type="order",
            entity_id=uuid4(),
            request_id=f"req-{i}",
            after={"id": i}
        )
    
    logs, total = AuditLogService.get_logs(db=db_session)
    
    assert total >= 5
    assert len(logs) >= 5


@pytest.mark.audit
def test_get_logs_filter_by_user(
    db_session: Session,
    seed_user_normal: User,
    seed_user_other: User
):
    """Test filtering logs by user_id."""
    # User normal creates 2 logs
    for i in range(2):
        AuditLogService.log_action(
            db=db_session,
            user_id=seed_user_normal.id,
            action="create",
            entity_type="order",
            entity_id=uuid4(),
            request_id=f"req-normal-{i}",
            after={}
        )
    
    # User other creates 3 logs
    for i in range(3):
        AuditLogService.log_action(
            db=db_session,
            user_id=seed_user_other.id,
            action="create",
            entity_type="order",
            entity_id=uuid4(),
            request_id=f"req-other-{i}",
            after={}
        )
    
    # Filter by user normal
    logs, total = AuditLogService.get_logs(db=db_session, user_id=seed_user_normal.id)
    
    assert total >= 2
    assert all(log.user_id == seed_user_normal.id for log in logs)


@pytest.mark.audit
def test_get_logs_filter_by_action(
    db_session: Session,
    seed_user_normal: User
):
    """Test filtering logs by action type."""
    order_id = uuid4()
    
    # Create
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=order_id,
        request_id="req-1",
        after={"total": 100}
    )
    
    # Update
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="update",
        entity_type="order",
        entity_id=order_id,
        request_id="req-2",
        before={"total": 100},
        after={"total": 150}
    )
    
    # Delete
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="delete",
        entity_type="order",
        entity_id=order_id,
        request_id="req-3",
        before={"total": 150}
    )
    
    # Filter only deletes
    logs, total = AuditLogService.get_logs(db=db_session, action="delete")
    
    assert total >= 1
    assert all(log.action == "delete" for log in logs)


@pytest.mark.audit
def test_get_entity_history(
    db_session: Session,
    seed_user_normal: User
):
    """Test retrieving complete history of an entity."""
    order_id = uuid4()
    
    # Create
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=order_id,
        request_id="req-1",
        after={"total": 100}
    )
    
    # Update 1
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="update",
        entity_type="order",
        entity_id=order_id,
        request_id="req-2",
        before={"total": 100},
        after={"total": 150}
    )
    
    # Update 2
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="update",
        entity_type="order",
        entity_id=order_id,
        request_id="req-3",
        before={"total": 150},
        after={"total": 200}
    )
    
    # Get history
    history = AuditLogService.get_entity_history(
        db=db_session,
        entity_type="order",
        entity_id=order_id
    )
    
    assert len(history) == 3
    assert history[0].action == "create"
    assert history[1].action == "update"
    assert history[2].action == "update"


@pytest.mark.audit
def test_get_user_actions(
    db_session: Session,
    seed_user_normal: User
):
    """Test retrieving all actions by a user."""
    # Create several actions
    for i in range(3):
        AuditLogService.log_action(
            db=db_session,
            user_id=seed_user_normal.id,
            action="create",
            entity_type="order",
            entity_id=uuid4(),
            request_id=f"req-{i}",
            after={}
        )
    
    actions = AuditLogService.get_user_actions(
        db=db_session,
        user_id=seed_user_normal.id
    )
    
    assert len(actions) >= 3
    assert all(action.user_id == seed_user_normal.id for action in actions)


@pytest.mark.audit
def test_audit_logs_endpoint_requires_admin(
    client: TestClient,
    auth_headers_user: dict
):
    """Test audit logs endpoint requires admin role."""
    response = client.get(
        "/audit-logs",
        headers=auth_headers_user
    )
    
    # Normal user should get 403 Forbidden
    assert response.status_code == 403


@pytest.mark.audit
def test_audit_logs_endpoint_admin_success(
    client: TestClient,
    db_session: Session,
    seed_user_admin: User,
    seed_user_normal: User,
    auth_headers_admin: dict
):
    """Test admin can access audit logs endpoint."""
    # Create some test logs
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=uuid4(),
        request_id="test-req",
        after={"total": 100}
    )
    
    response = client.get(
        "/audit-logs",
        headers=auth_headers_admin
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data


@pytest.mark.audit
def test_audit_logs_pagination(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_admin: dict
):
    """Test pagination works correctly."""
    # Create 25 logs
    for i in range(25):
        AuditLogService.log_action(
            db=db_session,
            user_id=seed_user_normal.id,
            action="create",
            entity_type="order",
            entity_id=uuid4(),
            request_id=f"req-{i}",
            after={}
        )
    
    # Get page 1 (default page_size=20)
    response = client.get(
        "/audit-logs?page=1&page_size=20",
        headers=auth_headers_admin
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 20
    assert data["total"] >= 25


@pytest.mark.audit
def test_entity_history_endpoint(
    client: TestClient,
    db_session: Session,
    seed_user_normal: User,
    auth_headers_admin: dict
):
    """Test entity history endpoint."""
    order_id = uuid4()
    
    # Create history
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=order_id,
        request_id="req-1",
        after={"total": 100}
    )
    
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="update",
        entity_type="order",
        entity_id=order_id,
        request_id="req-2",
        before={"total": 100},
        after={"total": 200}
    )
    
    # Get history
    response = client.get(
        f"/audit-logs/entity/order/{order_id}",
        headers=auth_headers_admin
    )
    
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert history[0]["action"] == "create"
    assert history[1]["action"] == "update"


@pytest.mark.audit
def test_get_logs_filter_by_entity_type(
    db_session: Session,
    seed_user_normal: User
):
    """
    COVERAGE: audit_log_service.py:136 - Filtro por entity_type
    
    Test filtering logs by entity_type.
    """
    # Create order log
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=uuid4(),
        request_id="req-order",
        after={}
    )
    
    # Create financial_entry log
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="financial_entry",
        entity_id=uuid4(),
        request_id="req-financial",
        after={}
    )
    
    # Filter by entity_type="order"
    logs, total = AuditLogService.get_logs(db=db_session, entity_type="order")
    
    assert total >= 1
    assert all(log.entity_type == "order" for log in logs)


@pytest.mark.audit
def test_get_logs_filter_by_entity_id(
    db_session: Session,
    seed_user_normal: User
):
    """
    COVERAGE: audit_log_service.py:139 - Filtro por entity_id
    
    Test filtering logs by specific entity_id.
    """
    order_id = uuid4()
    
    # Create multiple logs for same entity
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=order_id,
        request_id="req-1",
        after={"total": 100}
    )
    
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="update",
        entity_type="order",
        entity_id=order_id,
        request_id="req-2",
        before={"total": 100},
        after={"total": 150}
    )
    
    # Filter by entity_id
    logs, total = AuditLogService.get_logs(db=db_session, entity_id=order_id)
    
    assert total >= 2
    assert all(log.entity_id == order_id for log in logs)


@pytest.mark.audit
def test_get_logs_filter_by_date_range(
    db_session: Session,
    seed_user_normal: User
):
    """
    COVERAGE: audit_log_service.py:142 (date_from) e 145 (date_to)
    
    Test filtering logs by date range.
    """
    from datetime import datetime, timedelta
    
    # Create log
    log = AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=uuid4(),
        request_id="req-date",
        after={}
    )
    db_session.flush()  # Ensure log is persisted to DB
    
    # Filter with date_from (muito atrás, deve incluir todos os logs)
    date_from = datetime.utcnow() - timedelta(days=1)
    logs, total = AuditLogService.get_logs(db=db_session, date_from=date_from)
    
    assert total >= 1
    
    # Filter with date_to (bem no futuro, deve incluir todos os logs)
    date_to = datetime.utcnow() + timedelta(days=1)
    logs, total = AuditLogService.get_logs(db=db_session, date_to=date_to)
    
    assert total >= 1


@pytest.mark.audit
def test_get_user_actions_with_date_filters(
    db_session: Session,
    seed_user_normal: User
):
    """
    COVERAGE: audit_log_service.py:206 (date_from) e 209 (date_to) em get_user_actions
    
    Test get_user_actions with date filters.
    """
    from datetime import datetime, timedelta
    
    # Create log for user
    AuditLogService.log_action(
        db=db_session,
        user_id=seed_user_normal.id,
        action="create",
        entity_type="order",
        entity_id=uuid4(),
        request_id="req-user-action",
        after={}
    )
    db_session.flush()  # Ensure log is persisted
    
    # Get actions with date_from (muito atrás para garantir que pega o log)
    date_from = datetime.utcnow() - timedelta(days=1)
    logs = AuditLogService.get_user_actions(
        db=db_session,
        user_id=seed_user_normal.id,
        date_from=date_from
    )
    
    assert len(logs) >= 1
    
    # Get actions with date_to (bem no futuro para garantir que pega o log)
    date_to = datetime.utcnow() + timedelta(days=1)
    logs = AuditLogService.get_user_actions(
        db=db_session,
        user_id=seed_user_normal.id,
        date_to=date_to
    )
    
    assert len(logs) >= 1
    
    # Get actions with both date_from and date_to
    logs = AuditLogService.get_user_actions(
        db=db_session,
        user_id=seed_user_normal.id,
        date_from=date_from,
        date_to=date_to
    )
    
    assert len(logs) >= 1

