import logging
import time

import pytest
from auth.auth import require_roles
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
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
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Mock auth setup
mock_admin_user = {"id": 1, "roles": ["app_admin", "app_user"]}


class MockAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            request.state.user = mock_admin_user
            response = await call_next(request)
            return response
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": str(e)})


def mock_require_roles(allowed_roles: list[str]):
    async def dependency(request: Request):
        user_roles = request.state.user.get("roles", [])
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return True

    return dependency


# Database override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Test client setup
app.user_middleware = []
app.middleware_stack = None
app.add_middleware(MockAuthMiddleware)
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[require_roles] = mock_require_roles
client = TestClient(app)


# Fixtures
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
    test_app = Application(
        name="Test Application", created_at=int(time.time()), is_usable=1
    )
    db_session.add(test_app)
    db_session.commit()
    db_session.refresh(test_app)
    return test_app


@pytest.fixture(scope="function")
def setup_pipeline_session(db_session, setup_application):
    session = PipelineSession(
        pipeline_id=setup_application.id,
        pipeline_input_id=1,
        name="Test Pipeline Session",
        created_by=mock_admin_user["id"],
        created_at=int(time.time()),
        is_usable=1,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture(scope="function")
def setup_general_properties(db_session):
    properties = []
    property_data = [
        ("coding", "Price", "price"),
        ("coding", "Factory Code", "factory_code"),
        ("perforation", "Min", "min"),
        ("perforation", "Max", "max"),
    ]

    for prop_type, label, key in property_data:
        prop = GeneralProperty(
            referrer_id=1,
            property_type="pipeline_input",
            property_label=label,
            property_key=prop_type,
            property_value="test_value",
            created_at=int(time.time()),
            is_usable=1,
        )
        db_session.add(prop)
        properties.append(prop)

    db_session.commit()
    for prop in properties:
        db_session.refresh(prop)
    return properties


# Test cases
def test_create_pipeline_session_output_unauthorized(test_db, db_session):
    """Test creating pipeline session output with unauthorized user"""
    original_roles = mock_admin_user["roles"]
    mock_admin_user["roles"] = []

    test_data = {"pipeline_session_id": 1, "name": None, "ended_at": None}

    response = client.post(
        "/v1/pipeline-session-output/new", params={"manual": 1}, json=test_data
    )

    mock_admin_user["roles"] = original_roles

    assert response.status_code == 403  # nosec B101
    assert db_session.query(PipelineSessionOutput).count() == 0  # nosec B101


def test_create_pipeline_session_output_different_roles(
    test_db, db_session, setup_pipeline_session
):
    """Test creating pipeline session output with different user roles"""
    test_data = {
        "pipeline_session_id": setup_pipeline_session.id,
        "name": None,
        "ended_at": None,
    }

    # Test with app_user role
    original_roles = mock_admin_user["roles"]

    # Test app_user role
    mock_admin_user["roles"] = ["app_user"]
    response = client.post(
        "/v1/pipeline-session-output/new", params={"manual": 1}, json=test_data
    )
    assert response.status_code == 201  # nosec B101

    # Test app_admin role
    mock_admin_user["roles"] = ["app_admin"]
    response = client.post(
        "/v1/pipeline-session-output/new", params={"manual": 1}, json=test_data
    )
    assert response.status_code == 201  # nosec B101

    mock_admin_user["roles"] = original_roles


# ... [Previous code remains the same up to test_create_pipeline_session_output_different_roles] ...


def test_create_pipeline_session_output_automatic(
    test_db, db_session, setup_pipeline_session
):
    """Test creating pipeline session output in automatic mode"""
    test_data = {
        "pipeline_session_id": setup_pipeline_session.id,
        "name": None,
        "ended_at": None,
    }

    response = client.post("/v1/pipeline-session-output/new", json=test_data)

    assert response.status_code == 201  # nosec B101
    created_output = response.json()  # nosec B101

    db_session.expire_all()
    db_output = (
        db_session.query(PipelineSessionOutput)
        .filter_by(id=created_output["id"])
        .first()
    )

    assert db_output is not None  # nosec B101
    assert db_output.pipeline_session_id == setup_pipeline_session.id  # nosec B101
    assert db_output.is_usable == 1  # nosec B101

    # Verify no output units in automatic mode
    output_units = (
        db_session.query(PipelineSessionOutputUnit)
        .filter_by(pipeline_session_output_id=db_output.id)
        .all()
    )
    assert len(output_units) == 0  # nosec B101


def test_create_pipeline_session_output_manual(
    test_db, db_session, setup_pipeline_session, setup_general_properties
):
    """Test creating pipeline session output in manual mode"""
    print("\nGeneral Properties:")
    for prop in setup_general_properties:
        print(f"ID: {prop.id}, Key: {prop.property_key}, Label: {prop.property_label}")

    test_data = {
        "pipeline_session_id": setup_pipeline_session.id,
        "name": None,
        "ended_at": None,
    }

    response = client.post(
        "/v1/pipeline-session-output/new", params={"manual": 1}, json=test_data
    )
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Content: {response.text}")

    assert response.status_code == 201  # nosec B101
    created_output = response.json()  # nosec B101

    db_session.expire_all()
    db_output = (
        db_session.query(PipelineSessionOutput)
        .filter_by(id=created_output["id"])
        .first()
    )

    assert db_output is not None  # nosec B101
    assert db_output.pipeline_session_id == setup_pipeline_session.id  # nosec B101

    output_units = (
        db_session.query(PipelineSessionOutputUnit)
        .filter_by(pipeline_session_output_id=db_output.id)
        .all()
    )

    print(f"\nOutput Units Count: {len(output_units)}")
    for unit in output_units:
        prop = (
            db_session.query(GeneralProperty)
            .filter_by(id=unit.property_reference_id)
            .first()
        )
        print(
            f"Unit ID: {unit.id}, Property Ref: {unit.property_reference_id}, Key: {unit.output_key}"
        )
        print(
            f"Referenced Property: Key={prop.property_key}, Label={prop.property_label}"
        )

    assert len(output_units) == len(setup_general_properties)  # nosec B101
    for unit in output_units:
        assert unit.output_value is None  # nosec B101
        assert unit.status in ["idle", "ready"]  # nosec B101


def test_create_pipeline_session_output_manual_with_property_key(
    test_db, db_session, setup_pipeline_session, setup_general_properties
):
    """Test creating pipeline session output with specific property keys"""
    print("\nGeneral Properties (Coding):")
    coding_props = [p for p in setup_general_properties if p.property_key == "coding"]
    for prop in coding_props:
        print(f"ID: {prop.id}, Key: {prop.property_key}, Label: {prop.property_label}")

    test_data = {
        "pipeline_session_id": setup_pipeline_session.id,
        "name": None,
        "ended_at": None,
    }

    response = client.post(
        "/v1/pipeline-session-output/new",
        params={"manual": 1, "property-key": "coding"},
        json=test_data,
    )

    assert response.status_code == 201  # nosec B101
    created_output = response.json()  # nosec B101

    db_session.expire_all()
    db_output = (
        db_session.query(PipelineSessionOutput)
        .filter_by(id=created_output["id"])
        .first()
    )

    output_units = (
        db_session.query(PipelineSessionOutputUnit)
        .filter_by(pipeline_session_output_id=db_output.id)
        .all()
    )

    assert len(output_units) == 2  # nosec B101
    for unit in output_units:
        prop = (
            db_session.query(GeneralProperty)
            .filter_by(id=unit.property_reference_id)
            .first()
        )
        assert prop.property_key == "coding"  # nosec B101


def test_create_pipeline_session_output_invalid_session(test_db, db_session):
    """Test creating pipeline session output with invalid session ID"""
    test_data = {
        "pipeline_session_id": 999,  # Non-existent ID
        "name": None,
        "ended_at": None,
    }

    response = client.post("/v1/pipeline-session-output/new", json=test_data)
    assert response.status_code in [400, 500]  # nosec B101

    output_count = db_session.query(PipelineSessionOutput).count()
    assert output_count == 0  # nosec B101


def test_create_pipeline_session_output_multiple_property_keys(
    test_db, db_session, setup_pipeline_session, setup_general_properties
):
    """Test creating pipeline session output with multiple property keys"""
    test_data = {
        "pipeline_session_id": setup_pipeline_session.id,
        "name": None,
        "ended_at": None,
    }

    response = client.post(
        "/v1/pipeline-session-output/new",
        params={"manual": 1, "property-key": "coding,perforation"},
        json=test_data,
    )

    assert response.status_code == 201  # nosec B101
    created_output = response.json()  # nosec B101

    db_session.expire_all()
    output_units = (
        db_session.query(PipelineSessionOutputUnit)
        .filter_by(pipeline_session_output_id=created_output["id"])
        .all()
    )

    assert len(output_units) == 4  # nosec B101 # All properties for both keys

    property_keys = [
        db_session.query(GeneralProperty)
        .filter_by(id=unit.property_reference_id)
        .first()
        .property_key
        for unit in output_units
    ]
    assert property_keys.count("coding") == 2  # nosec B101
    assert property_keys.count("perforation") == 2  # nosec B101


def test_get_pipeline_session_output(
    test_db, db_session, setup_pipeline_session, setup_general_properties
):
    """Test getting a single pipeline session output"""
    # First create an output
    test_data = {
        "pipeline_session_id": setup_pipeline_session.id,
        "name": "Test Output",
        "ended_at": None,
    }

    create_response = client.post(
        "/v1/pipeline-session-output/new", params={"manual": 1}, json=test_data
    )
    assert create_response.status_code == 201  # nosec B101
    created_output = create_response.json()  # nosec B101

    # Get the created output
    response = client.get(f"/v1/pipeline-session-output/{created_output['id']}")
    assert response.status_code == 200  # nosec B101

    fetched_output = response.json()  # nosec B101
    assert fetched_output["name"] == "Test Output"  # nosec B101
    assert (
        fetched_output["pipeline_session_id"] == setup_pipeline_session.id
    )  # nosec B101


def test_get_pipeline_session_output_with_overview(
    test_db, db_session, setup_pipeline_session, setup_general_properties
):
    """Test getting pipeline session output with overview=0"""
    # Create output with units
    test_data = {
        "pipeline_session_id": setup_pipeline_session.id,
        "name": "Test Output",
        "ended_at": None,
    }

    create_response = client.post(
        "/v1/pipeline-session-output/new", params={"manual": 1}, json=test_data
    )
    assert create_response.status_code == 201  # nosec B101
    created_output = create_response.json()  # nosec B101

    # Get with overview=0
    response = client.get(
        f"/v1/pipeline-session-output/{created_output['id']}", params={"overview": 0}
    )
    assert response.status_code == 200  # nosec B101

    fetched_output = response.json()  # nosec B101
    assert "units" in fetched_output  # nosec B101
    assert len(fetched_output["units"]) == len(setup_general_properties)  # nosec B101


def test_get_pipeline_session_output_not_found(test_db):
    """Test getting non-existent pipeline session output"""
    response = client.get("/v1/pipeline-session-output/999")
    assert response.status_code == 404  # nosec B101


def test_get_all_pipeline_session_outputs(test_db, db_session, setup_pipeline_session):
    """Test getting all pipeline session outputs"""
    # Create multiple outputs
    outputs = []
    for i in range(3):
        test_data = {
            "pipeline_session_id": setup_pipeline_session.id,
            "name": f"Test Output {i}",
            "ended_at": None,
        }
        response = client.post("/v1/pipeline-session-output/new", json=test_data)
        assert response.status_code == 201  # nosec B101
        outputs.append(response.json())

    # Verify outputs were created
    db_outputs = db_session.query(PipelineSessionOutput).filter_by(is_usable=1).all()
    logger.info(f"Created outputs in DB: {len(db_outputs)}")
    for out in db_outputs:
        logger.debug(f"Output ID: {out.id}, Name: {out.name}")

    assert len(db_outputs) == 3  # nosec B101
    assert all(out.is_usable == 1 for out in db_outputs)  # nosec B101
