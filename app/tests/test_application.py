import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
import time
import logging
from datetime import datetime
from auth.auth import require_roles
from pydantic import ValidationError, BaseModel, validator
from typing import Optional

from main import app
from database.connection import get_db, Base
from schemas.application import ApplicationCreate
from models.application import Application as ApplicationModel

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    """Create test database tables before each test and drop them after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def sample_application():
    """Fixture for sample application data"""
    return {
        "name": "Test Application",
        "is_usable": 1
    }

# Mock auth setup
mock_admin_user = {
    "id": 1,
    "roles": ["app_admin"]  # Add necessary roles
}

class MockAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger.debug("MockAuthMiddleware: Processing request")
        request.state.user = mock_admin_user
        logger.debug(f"MockAuthMiddleware: Set user state: {request.state.user}")
        response = await call_next(request)
        logger.debug(f"MockAuthMiddleware: Response status: {response.status_code}")
        return response

# Setup test client with auth middleware
app.user_middleware = []
app.middleware_stack = None
app.add_middleware(MockAuthMiddleware)

# Mock the require_roles dependency
def mock_require_roles(allowed_roles: list[str]):
    async def dependency(request: Request):
        user_roles = request.state.user.get("roles", [])
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return True
    return dependency

# Add this after other app configurations
app.dependency_overrides[require_roles] = mock_require_roles

def test_create_application_success(test_db, sample_application):
    """Test successful application creation"""
    logger.info("Testing application creation")
    logger.debug(f"Request data: {sample_application}")
    
    response = client.post("/v1/application/", json=sample_application)
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_application["name"]
    assert data["is_usable"] == 1
    assert "id" in data
    assert "created_at" in data

def test_create_application_empty_name(test_db):
    """Test application creation with empty name"""
    with pytest.raises(ValidationError):
        ApplicationCreate(name="", is_usable=1)
    
    response = client.post("/v1/application/", json={"name": "", "is_usable": 1})
    assert response.status_code == 422
    assert "Value error, Name cannot be empty" in response.json()["detail"][0]["msg"]

def test_create_application_missing_name(test_db):
    """Test application creation with missing name"""
    response = client.post("/v1/application/", json={"is_usable": 1})
    assert response.status_code == 422

def test_create_application_very_long_name(test_db):
    """Test application creation with name exceeding max length"""
    long_name = "x" * 256
    with pytest.raises(ValidationError):
        ApplicationCreate(name=long_name, is_usable=1)
    
    response = client.post("/v1/application/", json={"name": long_name, "is_usable": 1})
    assert response.status_code == 422
    assert "Value error, Name cannot exceed 255 characters" in response.json()["detail"][0]["msg"]

def test_get_all_applications_empty(test_db):
    """Test getting all applications when none exist"""
    response = client.get("/v1/application/all")
    assert response.status_code == 200
    assert response.json() == []

def test_get_all_applications_with_data(test_db, db_session, sample_application):
    """Test getting all applications with existing data"""
    # Create multiple applications
    apps = []
    for i in range(3):
        app = ApplicationModel(
            name=f"Test App {i}",
            created_at=int(time.time()),
            is_usable=1
        )
        apps.append(app)
    
    db_session.bulk_save_objects(apps)
    db_session.commit()

    response = client.get("/v1/application/all")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(app["is_usable"] == 1 for app in data)

def test_get_application_by_id_success(test_db, db_session, sample_application):
    """Test getting a specific application by ID"""
    # Create an application
    app = ApplicationModel(
        name=sample_application["name"],
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    response = client.get(f"/v1/application/{app.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_application["name"]
    assert data["id"] == app.id

def test_get_application_not_found(test_db):
    """Test getting non-existent application"""
    response = client.get("/v1/application/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_update_application_success(test_db, db_session, sample_application):
    """Test successful application update"""
    # Create an application
    app = ApplicationModel(
        name=sample_application["name"],
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    # Update the application
    update_data = {"name": "Updated App Name", "is_usable": 1}
    response = client.patch(f"/v1/application/{app.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated App Name"
    assert data["id"] == app.id

def test_update_application_not_found(test_db):
    """Test updating non-existent application"""
    update_data = {"name": "Updated App Name", "is_usable": 1}
    response = client.patch("/v1/application/999", json=update_data)
    assert response.status_code == 404

def test_update_application_invalid_data(test_db, db_session, sample_application):
    """Test updating application with invalid data"""
    # Create an application
    app = ApplicationModel(
        name=sample_application["name"],
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    # Try to update with empty name
    update_data = {"name": "", "is_usable": 1}
    response = client.patch(f"/v1/application/{app.id}", json=update_data)
    assert response.status_code == 422
    assert "Value error, Name cannot be empty" in response.json()["detail"][0]["msg"]

def test_delete_application_success(test_db, db_session, sample_application):
    """Test successful application deletion (soft delete)"""
    # Create an application
    app = ApplicationModel(
        name=sample_application["name"],
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    response = client.delete(f"/v1/application/{app.id}")
    assert response.status_code == 200
    
    # Verify soft delete
    db_session.expire_all()
    deleted_app = db_session.query(ApplicationModel).filter_by(id=app.id).first()
    assert deleted_app.is_usable == 0

def test_delete_application_not_found(test_db):
    """Test deleting non-existent application"""
    response = client.delete("/v1/application/999")
    assert response.status_code == 404

def test_delete_already_deleted_application(test_db, db_session, sample_application):
    """Test deleting an already deleted application"""
    # Create a deleted application
    app = ApplicationModel(
        name=sample_application["name"],
        created_at=int(time.time()),
        is_usable=0  # Already deleted
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    response = client.delete(f"/v1/application/{app.id}")
    assert response.status_code == 404

def test_concurrent_updates(test_db, db_session, sample_application):
    """Test handling concurrent updates to the same application"""
    # Create an application
    app = ApplicationModel(
        name=sample_application["name"],
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    # Simulate concurrent updates
    update_data_1 = {"name": "Update 1", "is_usable": 1}
    update_data_2 = {"name": "Update 2", "is_usable": 1}

    response1 = client.patch(f"/v1/application/{app.id}", json=update_data_1)
    response2 = client.patch(f"/v1/application/{app.id}", json=update_data_2)

    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Verify final state
    final_response = client.get(f"/v1/application/{app.id}")
    assert final_response.json()["name"] == "Update 2"

def test_application_name_uniqueness(test_db, db_session, sample_application):
    """Test handling duplicate application names"""
    # Create first application
    app1 = ApplicationModel(
        name=sample_application["name"],
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(app1)
    db_session.commit()
    db_session.refresh(app1)

    # Try to create second application with same name
    response = client.post("/v1/application/", json=sample_application)
    assert response.status_code == 400  # Changed from 500 to 400 for business validation
    assert "Application with this name already exists" in response.json()["detail"]

# Add a helper function to check for duplicate names
def check_duplicate_name(db: Session, name: str, exclude_id: Optional[int] = None) -> bool:
    """Check if an application with the given name already exists"""
    query = db.query(ApplicationModel).filter(
        ApplicationModel.name == name,
        ApplicationModel.is_usable == 1
    )
    if exclude_id:
        query = query.filter(ApplicationModel.id != exclude_id)
    return db.query(query.exists()).scalar() 