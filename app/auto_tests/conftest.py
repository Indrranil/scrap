from app.auto_tests.test_env_setup import *

import os
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

try:
    from app.database.connection import Base, get_db
    from app.main import app
    from app.models.application import Application
    from app.models.application_container import ApplicationContainer
    from app.models.application_status_log import ApplicationStatusLog
    from app.models.general_property import GeneralProperty
    from app.models.machine import Machine
    from app.models.pipeline import Pipeline
    from app.models.pipeline_input import PipelineInput
    from app.models.pipeline_session import PipelineSession
    from app.models.pipeline_session_output import PipelineSessionOutput
    from app.models.pipeline_session_output_unit import (
        PipelineSessionOutputUnit,
    )
    from app.models.property_description import PropertyDescription
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise



@pytest.fixture(scope="session")
def test_engine():
    """Create a test SQLite database engine."""
    # Use in-memory SQLite database to avoid file permission issues
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # No cleanup needed for in-memory database


@pytest.fixture
def test_db_session(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    mock_session = Mock(spec=Session)
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.refresh = Mock()
    mock_session.delete = Mock()
    mock_session.query = Mock()
    mock_session.close = Mock()
    return mock_session


@pytest.fixture
def mock_auth():
    """Mock authentication for protected endpoints."""
    def mock_require_roles(roles):
        def decorator(func):
            return func
        return decorator
    
    with patch("app.auth.auth.require_roles", side_effect=mock_require_roles):
        yield


@pytest.fixture
def mock_request_with_user():
    """Mock FastAPI request with user state."""
    mock_request = Mock()
    mock_request.state.user = {"id": "test-user-123", "username": "testuser"}
    return mock_request


@pytest.fixture
def mock_keycloak():
    """Mock Keycloak admin for user management tests."""
    with patch("app.routers.users.keycloak_admin") as mock_kc:
        mock_kc.get_users.return_value = []
        mock_kc.create_user.return_value = "test-user-id"
        mock_kc.get_user.return_value = {
            "id": "test-user-id",
            "username": "testuser",
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
            "enabled": True
        }
        mock_kc.update_user.return_value = None
        mock_kc.delete_user.return_value = None
        mock_kc.get_realm_roles.return_value = [
            {"name": "app_admin", "id": "admin-role-id"},
            {"name": "app_user", "id": "user-role-id"}
        ]
        mock_kc.assign_realm_roles.return_value = None
        yield mock_kc
