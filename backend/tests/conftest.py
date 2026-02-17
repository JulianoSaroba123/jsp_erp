"""
Pytest fixtures for ERP JSP test suite.

Provides:
- Transactional database isolation (each test runs in a transaction + ROLLBACK)
- Test client for API requests with dependency override
- User fixtures (admin and normal users)
- Authentication headers
- Automatic table creation (once per session)

STRATEGY:
- Each test runs inside a PostgreSQL transaction
- At test end: ROLLBACK (automatic cleanup, no TRUNCATE needed)
- Uses SAVEPOINT (begin_nested) to allow endpoints to commit internally
- FastAPI app uses the same Session via get_db override
"""

import os
from typing import Generator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine, Connection

from app.main import app
from app.database import Base
from app.security.deps import get_db
from app.config import SECRET_KEY, ALGORITHM
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry
from app.auth.security import hash_password, create_access_token


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def engine_test() -> Generator[Engine, None, None]:
    """
    Create SQLAlchemy engine for test database (session-scoped).
    
    FAIL-FAST: Requires DATABASE_URL_TEST environment variable.
    This prevents accidentally running tests on production database.
    
    Returns:
        Engine connected to test database
    
    Raises:
        RuntimeError: If DATABASE_URL_TEST not set
    """
    test_url = os.getenv("DATABASE_URL_TEST")
    
    if not test_url:
        raise RuntimeError(
            "❌ DATABASE_URL_TEST environment variable is required for tests!\n"
            "Example: export DATABASE_URL_TEST='postgresql://user:pass@localhost:5432/jsp_erp_test'\n"
            "This prevents accidentally running tests on production database."
        )
    
    # Create engine
    engine = create_engine(test_url, echo=False)
    
    # Import all models to register with Base.metadata
    from app.models.user import User  # noqa
    from app.models.order import Order  # noqa
    from app.models.financial_entry import FinancialEntry  # noqa
    
    # Create tables once (if not exist)
    try:
        # Try to create pgcrypto extension (may require superuser)
        with engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
                conn.commit()
            except Exception:
                # Extension already exists or permission denied (OK)
                conn.rollback()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
    
    except Exception as e:
        engine.dispose()
        raise RuntimeError(f"Failed to setup test database: {e}")
    
    yield engine
    
    # Cleanup: dispose engine after all tests
    engine.dispose()


@pytest.fixture(scope="function")
def db_connection(engine_test: Engine) -> Generator[Connection, None, None]:
    """
    Create database connection with transaction (function-scoped).
    
    Each test gets a fresh connection with an active transaction.
    At test end: ROLLBACK (all changes discarded, database pristine).
    
    This ensures complete test isolation without TRUNCATE.
    
    Yields:
        Connection with active transaction
    """
    connection = engine_test.connect()
    transaction = connection.begin()
    
    try:
        yield connection
    finally:
        # ROLLBACK: discard all changes (check if active to avoid SAWarning)
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def db_session(db_connection: Connection) -> Generator[Session, None, None]:
    """
    Create SQLAlchemy Session bound to test connection (function-scoped).
    
    SIMPLIFIED APPROACH: No SAVEPOINT, just override commit() to flush().
    All test data is flushed (visible) but never committed.
    At test end: connection.rollback() discards everything.
    
    Yields:
        Session with commit() = flush()
    """
    # Create Session bound to test connection
    SessionLocal = sessionmaker(
        bind=db_connection,
        autocommit=False,
        autoflush=True
    )
    session = SessionLocal()
    
    # Override commit() to just flush
    # Tests can call commit(), but we just flush (no actual COMMIT/SAVEPOINT)
    original_commit = session.commit
    
    def fake_commit():
        """
        Fake commit that just flushes data to make it visible.
        No actual COMMIT or SAVEPOINT - data stays in transaction.
        """
        session.flush()  # Make data visible within transaction
    
    session.commit = fake_commit
    
    try:
        yield session
    finally:
        session.commit = original_commit  # Restore original
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client with database dependency override.
    
    Overrides app.security.deps.get_db to return the test session.
    This ensures endpoints use the same transactional session as tests.
    
    IMPORTANT: All endpoints will use db_session, so commits are local
    to the SAVEPOINT and won't affect other tests.
    
    Yields:
        TestClient configured for testing
    """
    def override_get_db():
        """
        Override get_db dependency to return test session.
        
        CRITICAL: Do NOT create a new session here.
        MUST yield the same db_session that the test is using.
        """
        try:
            yield db_session
        finally:
            # Don't close session here (handled by db_session fixture)
            pass
    
    # Override FastAPI dependency
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clear overrides after test
        app.dependency_overrides.clear()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def seed_user_admin(db_session: Session) -> User:
    """
    Create admin user for testing.
    
    Credentials: admin@test.com / testpass123
    """
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
