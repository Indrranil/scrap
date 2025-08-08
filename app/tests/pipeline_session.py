import logging
import time

import pytest
from fastapi.testclient import TestClient
from main import app
from models.application import Application
from models.general_property import GeneralProperty
from models.pipeline_session import PipelineSession
from models.pipeline_session_output import PipelineSessionOutput
from models.pipeline_session_output_unit import PipelineSessionOutputUnit
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware

from app.database.connection import Base, get_db

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

mock_admin_user = {"id": 1, "roles": ["app_admin"]}


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


class MockAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.user = mock_admin_user
        response = await call_next(request)
        return response


app.user_middleware = []
app.middleware_stack = None
app.add_middleware(MockAuthMiddleware)

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def setup_application(db_session):
    """Creates a test application in the database"""
    test_app = Application(
        name="Test Application", created_at=int(time.time()), is_usable=1
    )
    db_session.add(test_app)
    db_session.commit()
    db_session.refresh(test_app)
    return test_app


@pytest.fixture(scope="function")
def setup_general_property(db_session):
    """Creates a test general property in the database"""
    test_property = GeneralProperty(
        referrer_id=1,
        property_type="pipeline_input",
        property_label="Test Property",
        property_key="test_key",
        property_value="test_value",
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(test_property)
    db_session.commit()
    db_session.refresh(test_property)
    return test_property


def test_create_pipeline_session_verify_db(test_db, db_session, setup_application):
    """
    Test pipeline session creation and verify the database state
    """
    test_data = {
        "pipeline_id": setup_application.id,
        "pipeline_input_id": 1,
        "name": "Test Pipeline Session",
        "ended_at": None,
    }

    response = client.post("/v1/pipeline-session/new", json=test_data)

    if response.status_code != 201:
        print(f"Response: {response.text}")

    assert response.status_code == 201  # nosec B101
    created_session = response.json()
    assert created_session["name"] == test_data["name"]  # nosec B101
    assert created_session["pipeline_id"] == test_data["pipeline_id"]  # nosec B101

    db_session.expire_all()
    db_session_entry = (
        db_session.query(PipelineSession).filter_by(id=created_session["id"]).first()
    )

    assert db_session_entry is not None  # nosec B101
    assert db_session_entry.name == test_data["name"]  # nosec B101
    assert db_session_entry.pipeline_id == test_data["pipeline_id"]  # nosec B101
    assert (
        db_session_entry.pipeline_input_id == test_data["pipeline_input_id"]
    )  # nosec B101
    assert db_session_entry.created_by == mock_admin_user["id"]  # nosec B101
    assert db_session_entry.is_usable == 1  # nosec B101
    assert db_session_entry.created_at is not None  # nosec B101
    assert db_session_entry.ended_at is None  # nosec B101

    assert db_session_entry.pipeline_id == setup_application.id  # nosec B101


def test_create_pipeline_session_invalid_application(test_db, db_session):
    """
    Test pipeline session creation with non-existent application ID
    """
    test_data = {
        "pipeline_id": 999,
        "pipeline_input_id": 1,
        "name": "Test Pipeline Session",
    }
    response = client.post("/v1/pipeline-session/new", json=test_data)
    assert response.status_code in [400, 500]  # nosec B101
    session_count = db_session.query(PipelineSession).count()  # nosec B101
    assert session_count == 0  # nosec B101


def test_get_pipeline_session(test_db, db_session, setup_application):
    """
    Test retrieving a single pipeline session by ID
    """
    # Create a test session first
    test_session = PipelineSession(
        pipeline_id=setup_application.id,
        pipeline_input_id=1,
        name="Test Session",
        created_by=mock_admin_user["id"],
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(test_session)
    db_session.commit()
    db_session.refresh(test_session)

    response = client.get(f"/v1/pipeline-session/{test_session.id}")

    assert response.status_code == 200  # nosec B101
    fetched_session = response.json()
    assert fetched_session["name"] == "Test Session"  # nosec B101
    assert fetched_session["pipeline_id"] == setup_application.id  # nosec B101
    assert fetched_session["is_usable"] == 1  # nosec B101


def test_get_pipeline_session_not_found(test_db):
    """
    Test retrieving a non-existent pipeline session
    """
    response = client.get("/v1/pipeline-session/999")
    assert response.status_code == 404  # nosec B101


def test_get_all_pipeline_sessions(test_db, db_session, setup_application):
    """Test retrieving all pipeline sessions"""
    # Create multiple test sessions
    sessions = []
    for i in range(3):
        session = PipelineSession(
            pipeline_id=setup_application.id,
            pipeline_input_id=1,
            name=f"Test Session {i}",
            created_by=mock_admin_user["id"],
            created_at=int(time.time()),
            is_usable=1,
        )
        sessions.append(session)

    db_session.bulk_save_objects(sessions)
    db_session.commit()

    logger.info("Testing get all sessions")
    logger.debug("Attempting to fetch from /v1/pipeline-session/all")
    response = client.get("/v1/pipeline-session/all")
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")

    assert response.status_code == 200  # nosec B101
    fetched_sessions = response.json()  # nosec B101
    assert "total" in fetched_sessions  # nosec B101
    assert fetched_sessions["total"] == 3  # nosec B101
    assert len(fetched_sessions["data"]) == 3  # nosec B101
    assert all(s["is_usable"] == 1 for s in fetched_sessions["data"])  # nosec B101


def test_get_pipeline_session_with_outputs(
    test_db, db_session, setup_application, setup_general_property
):
    """
    Test retrieving a pipeline session with its outputs (overview=0)
    """
    # Create a test session
    test_session = PipelineSession(
        pipeline_id=setup_application.id,
        pipeline_input_id=1,
        name="Test Session",
        created_by=mock_admin_user["id"],
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(test_session)
    db_session.commit()
    db_session.refresh(test_session)

    # Create a test output for the session
    test_output = PipelineSessionOutput(
        pipeline_session_id=test_session.id,
        name="Test Output",
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(test_output)
    db_session.commit()
    db_session.refresh(test_output)

    # Create a test output unit using the general property we created
    test_output_unit = PipelineSessionOutputUnit(
        pipeline_session_output_id=test_output.id,
        property_reference_id=setup_general_property.id,
        output_key="test_key",
        output_value="test_value",
        status="success",
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(test_output_unit)
    db_session.commit()

    # Try to get the data first to verify it exists
    db_check = db_session.query(PipelineSession).filter_by(id=test_session.id).first()
    print(f"Session in DB: {db_check}")
    db_output = (
        db_session.query(PipelineSessionOutput)
        .filter_by(pipeline_session_id=test_session.id)
        .first()
    )
    print(f"Output in DB: {db_output}")
    db_unit = (
        db_session.query(PipelineSessionOutputUnit)
        .filter_by(pipeline_session_output_id=test_output.id)
        .first()
    )
    print(f"Unit in DB: {db_unit}")

    response = client.get(f"/v1/pipeline-session/{test_session.id}?overview=0")

    # Print response for debugging
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")

    assert response.status_code == 200  # nosec B101
    fetched_session = response.json()  # nosec B101
    assert "outputs" in fetched_session  # nosec B101
    assert len(fetched_session["outputs"]) == 1  # nosec B101
    assert len(fetched_session["outputs"][0]["units"]) == 1  # nosec B101
    assert fetched_session["outputs"][0]["name"] == "Test Output"  # nosec B101
    assert (
        fetched_session["outputs"][0]["units"][0]["output_key"] == "test_key"
    )  # nosec B101
    assert (
        fetched_session["outputs"][0]["units"][0]["output_value"] == "test_value"
    )  # nosec B101


def test_create_pipeline_session_missing_fields(test_db):
    """Test pipeline session creation with missing required fields"""
    test_data = {"pipeline_id": None, "name": "Test Session"}
    response = client.post("/v1/pipeline-session/new", json=test_data)
    assert response.status_code == 422  # nosec B101


def test_get_pipeline_session_soft_deleted(test_db, db_session, setup_application):
    """Test retrieving a soft-deleted pipeline session"""
    # Create a session and soft delete it
    test_session = PipelineSession(
        pipeline_id=setup_application.id,
        pipeline_input_id=1,
        name="Test Session",
        created_by=mock_admin_user["id"],
        created_at=int(time.time()),
        is_usable=0,  # Soft deleted
    )
    db_session.add(test_session)
    db_session.commit()
    db_session.refresh(test_session)

    response = client.get(f"/v1/pipeline-session/{test_session.id}")
    assert response.status_code == 404  # nosec B101


def test_get_pipeline_session_with_invalid_overview(
    test_db, db_session, setup_application
):
    """Test getting pipeline session with invalid overview parameter"""
    test_session = PipelineSession(
        pipeline_id=setup_application.id,
        pipeline_input_id=1,
        name="Test Session",
        created_by=mock_admin_user["id"],
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(test_session)
    db_session.commit()

    response = client.get(f"/v1/pipeline-session/{test_session.id}?overview=invalid")
    assert response.status_code == 422  # nosec B101


def test_get_pipeline_session_outputs_empty(test_db, db_session, setup_application):
    """Test getting pipeline session with no outputs"""
    test_session = PipelineSession(
        pipeline_id=setup_application.id,
        pipeline_input_id=1,
        name="Test Session",
        created_by=mock_admin_user["id"],
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(test_session)
    db_session.commit()

    response = client.get(f"/v1/pipeline-session/{test_session.id}?overview=0")
    assert response.status_code == 200  # nosec B101
    data = response.json()  # nosec B101
    assert "outputs" in data  # nosec B101
    assert len(data["outputs"]) == 0  # nosec B101


def test_get_pipeline_session_with_deleted_outputs(
    test_db, db_session, setup_application
):
    """Test getting pipeline session with soft-deleted outputs"""
    # Create session with a soft-deleted output
    test_session = PipelineSession(
        pipeline_id=setup_application.id,
        pipeline_input_id=1,
        name="Test Session",
        created_by=mock_admin_user["id"],
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(test_session)
    db_session.commit()

    test_output = PipelineSessionOutput(
        pipeline_session_id=test_session.id,
        name="Deleted Output",
        created_at=int(time.time()),
        is_usable=0,  # Soft deleted
    )
    db_session.add(test_output)
    db_session.commit()

    response = client.get(f"/v1/pipeline-session/{test_session.id}?overview=0")
    assert response.status_code == 200  # nosec B101
    data = response.json()  # nosec B101
    assert len(data["outputs"]) == 0  # nosec B101


def test_unauthorized_access(test_db):
    """Test accessing endpoints without proper authorization"""
    # Temporarily remove admin role
    original_roles = mock_admin_user["roles"]
    mock_admin_user["roles"] = []

    response = client.get("/v1/pipeline-session/all")
    assert response.status_code == 403  # nosec B101

    # Restore admin role
    mock_admin_user["roles"] = original_roles
