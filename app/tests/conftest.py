"""
Pytest configuration file for the refactored API tests.
This file contains shared fixtures and configuration for all tests.
"""

import os
import sys

import pytest
from fastapi import Request

try:
    from fastapi.testclient import TestClient
except ImportError:
    from starlette.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.auth import require_roles
from app.database.connection import Base, get_db
from app.main import app

# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_refactored_api.db"

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine for the session"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create session factory for tests"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create and clean up test database for each test"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after test
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_session_factory):
    """Provide a database session for tests"""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def mock_admin_user():
    """Mock admin user for authentication"""
    return {"id": 413, "username": "test_admin", "roles": ["app_admin", "app_user"]}


@pytest.fixture(scope="session")
def mock_regular_user():
    """Mock regular user for authentication"""
    return {"id": 100, "username": "test_user", "roles": ["app_user"]}


class MockAuthMiddleware(BaseHTTPMiddleware):
    """Mock authentication middleware for testing"""

    def __init__(self, app, user_data):
        super().__init__(app)
        self.user_data = user_data

    async def dispatch(self, request: Request, call_next):
        request.state.user = self.user_data
        response = await call_next(request)
        return response


@pytest.fixture(scope="function")
def test_client_admin(test_session_factory, mock_admin_user):
    """Test client with admin authentication"""

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    def mock_require_roles(allowed_roles: list[str]):
        def dependency():
            return True

        return dependency

    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_roles] = mock_require_roles

    # Add auth middleware
    app.user_middleware = []
    app.middleware_stack = None
    app.add_middleware(MockAuthMiddleware, user_data=mock_admin_user)

    # Use TestClient with the working import pattern
    # Import TestClient directly from the working module
    try:
        from fastapi.testclient import TestClient

        # Use FastAPI's TestClient which should work correctly
        client = TestClient(app)
    except (ImportError, TypeError):
        # If FastAPI TestClient fails, try alternative approach
        import httpx

        client = httpx.Client(app=app, base_url="http://testserver")
    yield client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client_user(test_session_factory, mock_regular_user):
    """Test client with regular user authentication"""

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    def mock_require_roles(allowed_roles: list[str]):
        def dependency():
            # Check if user has required roles
            user_roles = mock_regular_user.get("roles", [])
            if any(role in user_roles for role in allowed_roles):
                return True
            return False

        return dependency

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_roles] = mock_require_roles

    app.user_middleware = []
    app.middleware_stack = None
    app.add_middleware(MockAuthMiddleware, user_data=mock_regular_user)

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_application_data():
    """Sample application data for tests"""
    return {"name": "Test Application", "is_usable": 1}


@pytest.fixture
def sample_pipeline_data():
    """Sample pipeline data for tests"""
    return {
        "name": "Test Pipeline",
        "is_running": False,
        "application_id": 1,  # Will be updated in tests
        "is_usable": 1,
    }


@pytest.fixture
def sample_pipeline_input_data():
    """Sample pipeline input data for tests"""
    return {"name": "Test Pipeline Input", "is_usable": 1}


@pytest.fixture
def sample_pipeline_session_data():
    """Sample pipeline session data for tests"""
    return {
        "pipeline_id": 1,  # Will be updated in tests
        "pipeline_input_id": 1,  # Will be updated in tests
        "name": "Test Pipeline Session",
    }


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "service: mark test as a service layer test")
    config.addinivalue_line("markers", "endpoint: mark test as an API endpoint test")
    config.addinivalue_line("markers", "auth: mark test as requiring authentication")


# Cleanup function
def pytest_sessionfinish(session, exitstatus):
    """Clean up after all tests are done"""
    # Remove test database file if it exists
    if os.path.exists("test_refactored_api.db"):
        os.remove("test_refactored_api.db")
