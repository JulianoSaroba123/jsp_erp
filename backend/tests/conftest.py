"""
Pytest fixtures for ERP JSP test suite.

Provides:
- Database session management with isolated test database
- Test client for API requests
- User fixtures (admin and normal users)
- Authentication headers
- Automatic migration application
"""

import os
import subprocess
from typing import Generator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base
from app.security.deps import get_db
from app.config import SECRET_KEY, ALGORITHM
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry
from app.models.role import Role
from app.models.permission import Permission
from app.auth.security import hash_password, create_access_token


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

def get_test_database_url() -> str:
    """
    Get test database URL from environment.
    
    Falls back to test database if DATABASE_URL_TEST not set.
    """
    test_url = os.getenv(
        "DATABASE_URL_TEST",
        "postgresql://jsp_user:jsp123456@localhost:5432/jsp_erp_test"
    )
    return test_url


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Verifica que o banco de teste existe com schema correto.

    O banco deve ser preparado com: .\\prepare_test_db.ps1
    Este fixture apenas valida a conectividade e importa os modelos.
    """
    test_db_url = get_test_database_url()

    from sqlalchemy import create_engine as create_engine_
    test_engine = create_engine_(test_db_url)

    # Importar modelos para o SQLAlchemy mapear corretamente
    from app.models.user import User  # noqa
    from app.models.order import Order  # noqa
    from app.models.financial_entry import FinancialEntry  # noqa
    from app.models.audit_log import AuditLog  # noqa

    # Verificar conectividade
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    yield

    test_engine.dispose()



@pytest.fixture(scope="function")
def db_session(setup_test_database) -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    
    Cleans up all data after test completes.
    """
    test_db_url = get_test_database_url()
    engine = create_engine(test_db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    
    try:
        yield session
    finally:
        # Rollback any pending transaction to clear session state
        session.rollback()
        
        # Cleanup data in reverse order (FK constraints)
        # Note: RBAC tables (roles, permissions, user_roles, role_permissions) não são limpas aqui
        # para evitar conflitos em testes paralelos. Rode seed_rbac novamente se necessário.
        session.execute(text("TRUNCATE TABLE core.audit_logs CASCADE"))
        session.execute(text("TRUNCATE TABLE core.financial_entries CASCADE"))
        session.execute(text("TRUNCATE TABLE core.orders CASCADE"))
        session.execute(text("TRUNCATE TABLE core.users CASCADE"))
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with overridden database dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def client_authenticated(client: TestClient, seed_user_normal: User, auth_headers_user: dict) -> TestClient:
    """
    Test client pré-autenticado como usuário normal.
    """
    client.headers.update(auth_headers_user)
    return client


@pytest.fixture
def client_admin(client: TestClient, seed_user_admin: User, auth_headers_admin: dict) -> TestClient:
    """
    Test client pré-autenticado como admin.
    """
    client.headers.update(auth_headers_admin)
    return client


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def seed_user_admin(db_session: Session) -> User:
    """
    Create admin user for testing.
    
    Credentials: admin@test.com / testpass123
    """
    # Check if user already exists (idempotent fixture)
    existing = db_session.query(User).filter(User.email == "admin@test.com").first()
    if existing:
        return existing
    
    user = User(
        name="Admin Test",
        email="admin@test.com",
        password_hash=hash_password("testpass123"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_user_normal(db_session: Session) -> User:
    """
    Create normal user for testing.
    
    Credentials: user@test.com / testpass123
    """
    # Check if user already exists (idempotent fixture)
    existing = db_session.query(User).filter(User.email == "user@test.com").first()
    if existing:
        return existing
    
    user = User(
        name="User Test",
        email="user@test.com",
        password_hash=hash_password("testpass123"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_user_other(db_session: Session) -> User:
    """
    Create another normal user for multi-tenant testing.
    
    Credentials: other@test.com / testpass123
    """
    # Check if user already exists (idempotent fixture)
    existing = db_session.query(User).filter(User.email == "other@test.com").first()
    if existing:
        return existing
    
    user = User(
        name="Other User",
        email="other@test.com",
        password_hash=hash_password("testpass123"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def auth_headers_admin(seed_user_admin: User) -> dict:
    """
    Generate Bearer token headers for admin user.
    """
    token = create_access_token(subject=str(seed_user_admin.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user(seed_user_normal: User) -> dict:
    """
    Generate Bearer token headers for normal user.
    """
    token = create_access_token(subject=str(seed_user_normal.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_other(seed_user_other: User) -> dict:
    """
    Generate Bearer token headers for other user (anti-enumeration tests).
    """
    token = create_access_token(subject=str(seed_user_other.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_user_with_delete_permission(db_session: Session) -> User:
    """
    Create user with orders:delete permission for testing RBAC.
    
    Credentials: deleter@test.com / testpass123
    """
    # Check if user already exists
    existing = db_session.query(User).filter(User.email == "deleter@test.com").first()
    if existing:
        return existing
    
    # Create user
    user = User(
        name="Deleter User",
        email="deleter@test.com",
        password_hash=hash_password("testpass123"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    # Create permission if not exists
    delete_permission = db_session.query(Permission).filter_by(
        resource="orders", action="delete"
    ).first()
    if not delete_permission:
        delete_permission = Permission(resource="orders", action="delete")
        db_session.add(delete_permission)
        db_session.flush()
    
    # Create role if not exists
    deleter_role = db_session.query(Role).filter_by(name="order_deleter").first()
    if not deleter_role:
        deleter_role = Role(name="order_deleter", description="Can delete orders")
        deleter_role.permissions.append(delete_permission)
        db_session.add(deleter_role)
        db_session.flush()
    
    # Assign role to user
    if deleter_role not in user.roles:
        user.roles.append(deleter_role)
    
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_admin_with_delete_permission(db_session: Session, seed_user_admin: User) -> User:
    """
    Add orders:delete permission to admin user.
    
    Used in tests that require admin to delete orders.
    """
    # Create permission if not exists
    delete_permission = db_session.query(Permission).filter_by(
        resource="orders", action="delete"
    ).first()
    if not delete_permission:
        delete_permission = Permission(resource="orders", action="delete")
        db_session.add(delete_permission)
        db_session.flush()
    
    # Create role if not exists
    admin_deleter_role = db_session.query(Role).filter_by(name="admin_order_deleter").first()
    if not admin_deleter_role:
        admin_deleter_role = Role(name="admin_order_deleter", description="Admin can delete orders")
        admin_deleter_role.permissions.append(delete_permission)
        db_session.add(admin_deleter_role)
        db_session.flush()
    
    # Assign role to admin if not already assigned
    if admin_deleter_role not in seed_user_admin.roles:
        seed_user_admin.roles.append(admin_deleter_role)
        db_session.commit()
    
    db_session.refresh(seed_user_admin)
    return seed_user_admin


@pytest.fixture
def auth_headers_with_delete(seed_user_with_delete_permission: User) -> dict:
    """
    Generate Bearer token headers for user with delete permission.
    """
    token = create_access_token(subject=str(seed_user_with_delete_permission.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin_with_delete(seed_admin_with_delete_permission: User) -> dict:
    """
    Generate Bearer token headers for admin with delete permission.
    """
    token = create_access_token(subject=str(seed_admin_with_delete_permission.id))
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_order(db_session: Session, seed_user_normal: User) -> Order:
    """
    Create a sample order for testing.
    """
    order = Order(
        user_id=seed_user_normal.id,
        description="Test Order",
        total=100.00
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def sample_financial_entry(db_session: Session, seed_user_normal: User) -> FinancialEntry:
    """
    Create a sample financial entry (manual, no order).
    """
    entry = FinancialEntry(
        user_id=seed_user_normal.id,
        kind="revenue",
        status="pending",
        amount=50.00,
        description="Test Revenue",
        occurred_at=datetime.utcnow()
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry
