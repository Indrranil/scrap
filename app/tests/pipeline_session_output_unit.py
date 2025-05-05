import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
import time

from main import app
from app.database.connection import get_db, Base
from models.pipeline_session import PipelineSession
from models.pipeline_session_output import PipelineSessionOutput
from models.pipeline_session_output_unit import PipelineSessionOutputUnit
from models.application import Application
from models.general_property import GeneralProperty
from auth.auth import require_roles

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
mock_admin_user = {
    "id": 1,
    "roles": ["app_admin", "app_user"]
}

class MockAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.user = mock_admin_user
        response = await call_next(request)
        return response

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Setup test client
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
    # First verify if test application exists
    app = db_session.query(Application).filter_by(
        name="Test Application",
        is_usable=1
    ).first()
    
    if app is None:
        app = Application(
            name="Test Application",
            created_at=int(time.time()),
            is_usable=1
        )
        db_session.add(app)
        db_session.commit()
        db_session.refresh(app)
        
        # Verify in database
        print("\nCreated Application:")
        print(f"ID: {app.id}")
        print(f"Name: {app.name}")
    
    return app

@pytest.fixture(scope="function")
def setup_pipeline_session(db_session, setup_application):
    """Create test pipeline session"""
    session = PipelineSession(
        pipeline_id=setup_application.id,
        pipeline_input_id=1,
        name="Test Pipeline Session",
        created_by=mock_admin_user["id"],
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session

@pytest.fixture(scope="function")
def setup_pipeline_output(db_session):
    """Create a test pipeline session output"""
    output = PipelineSessionOutput(
        pipeline_session_id=1,
        name="Test Output",
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(output)
    db_session.commit()
    db_session.refresh(output)
    return output

@pytest.fixture(scope="function")
def setup_general_property(db_session):
    """Create a test general property"""
    prop = GeneralProperty(
        referrer_id=1,
        property_type="pipeline_input",
        property_label="Test Property",
        property_key="test_key",
        property_value="test_value",
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(prop)
    db_session.commit()
    db_session.refresh(prop)
    return prop



@pytest.fixture(scope="function")
def setup_pipeline_output(db_session, setup_pipeline_session):
    """Create test pipeline session output"""
    output = PipelineSessionOutput(
        pipeline_session_id=setup_pipeline_session.id,  # Use the actual pipeline session ID
        name="Test Output",
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(output)
    db_session.commit()
    db_session.refresh(output)
    
    # Verify in database
    db_output = db_session.query(PipelineSessionOutput).filter_by(
        id=output.id
    ).first()
    assert db_output is not None
    assert db_output.pipeline_session_id == setup_pipeline_session.id
    
    return output

def test_create_pipeline_session_output_unit(
    test_db,
    db_session,
    setup_pipeline_output,
    setup_general_property
):
    """Test creating a new pipeline session output unit"""
    # Print initial database state
    print("\nInitial Database State:")
    print(f"Pipeline Output ID: {setup_pipeline_output.id}")
    print(f"General Property ID: {setup_general_property.id}")
    
    test_data = {
        "pipeline_session_output_id": setup_pipeline_output.id,
        "property_reference_id": setup_general_property.id,
        "output_key": "test_key",
        "output_value": "test_value",
        "status": "idle",
        "name": "Test Unit"
    }
    
    response = client.post("/v1/pipeline-session-output-unit/new", json=test_data)
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Content: {response.text}")
    
    assert response.status_code == 201
    created_unit = response.json()
    
    # Verify in database
    db_session.expire_all()
    db_unit = db_session.query(PipelineSessionOutputUnit).filter_by(
        id=created_unit["id"]
    ).first()
    
    print("\nDatabase Verification:")
    print(f"Created Unit ID: {db_unit.id}")
    print(f"Pipeline Output ID: {db_unit.pipeline_session_output_id}")
    print(f"Property Reference ID: {db_unit.property_reference_id}")
    
    assert db_unit is not None
    assert db_unit.pipeline_session_output_id == setup_pipeline_output.id
    assert db_unit.property_reference_id == setup_general_property.id
    assert db_unit.output_key == "test_key"
    assert db_unit.output_value == "test_value"
    assert db_unit.status == "idle"

def test_update_pipeline_session_output_unit(
    test_db,
    db_session,
    setup_pipeline_output,
    setup_general_property
):
    """Test updating a single pipeline session output unit"""
    # Create a unit first
    unit = PipelineSessionOutputUnit(
        pipeline_session_output_id=setup_pipeline_output.id,
        property_reference_id=setup_general_property.id,
        output_key="test_key",
        output_value="old_value",
        status="idle",
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    
    print("\nInitial Unit State:")
    print(f"Unit ID: {unit.id}")
    print(f"Old Value: {unit.output_value}")
    
    # Update the unit
    update_data = {
        "output_value": "new_value",
        "status": "success"
    }
    
    response = client.patch(
        f"/v1/pipeline-session-output-unit?unit_id={unit.id}",
        json=update_data
    )
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Content: {response.text}")
    
    assert response.status_code == 200
    
    # Verify in database
    db_session.expire_all()
    updated_unit = db_session.query(PipelineSessionOutputUnit).filter_by(
        id=unit.id
    ).first()
    
    print("\nUpdated Database State:")
    print(f"New Value: {updated_unit.output_value}")
    print(f"New Status: {updated_unit.status}")
    
    assert updated_unit.output_value == "new_value"
    assert updated_unit.status == "success"

def test_batch_update_pipeline_session_output_units(
    test_db, 
    db_session, 
    setup_pipeline_output,
    setup_general_property
):
    """Test batch updating pipeline session output units"""
    # Create multiple units
    units = []
    for i in range(3):
        unit = PipelineSessionOutputUnit(
            pipeline_session_output_id=setup_pipeline_output.id,
            property_reference_id=setup_general_property.id,
            output_key="test_key",
            output_value=f"value_{i}",
            status="idle",
            created_at=int(time.time()),
            is_usable=1
        )
        units.append(unit)
    
    db_session.bulk_save_objects(units)
    db_session.commit()
    
    # Store output ID for later use
    output_id = setup_pipeline_output.id
    
    # Verify initial state
    created_units = db_session.query(PipelineSessionOutputUnit).filter_by(
        pipeline_session_output_id=output_id
    ).all()
    print("\nInitial Database State:")
    for unit in created_units:
        print(f"Unit ID: {unit.id}, Value: {unit.output_value}, Status: {unit.status}")
    
    # Batch update
    update_data = {
        "status": "ready",
        "output_value": ""
    }
    
    url = f"/v1/pipeline-session-output-unit/all?pipeline_session_output_id={output_id}"
    print(f"\nMaking PATCH request to: {url}")
    print(f"Update data: {update_data}")
    
    response = client.patch(url, json=update_data)
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Content: {response.text}")
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["updated_count"] == 3
    
    # Query with same session after refresh
    db_session.expire_all()
    updated_units = db_session.query(PipelineSessionOutputUnit).filter_by(
        pipeline_session_output_id=output_id
    ).all()
    
    print("\nFinal Database State:")
    for unit in updated_units:
        print(f"Unit ID: {unit.id}, Value: {unit.output_value}, Status: {unit.status}")
        assert unit.status == "ready"
        assert unit.output_value == ""

def test_batch_update_with_output_key_filter(
    test_db, 
    db_session, 
    setup_pipeline_output,
    setup_general_property
):
    """Test batch updating units with output key filter"""
    # Store output ID
    output_id = setup_pipeline_output.id
    
    # Create units with different output keys
    units = [
        PipelineSessionOutputUnit(
            pipeline_session_output_id=output_id,
            property_reference_id=setup_general_property.id,
            output_key="coding",
            output_value="value1",
            status="idle",
            created_at=int(time.time()),
            is_usable=1
        ),
        PipelineSessionOutputUnit(
            pipeline_session_output_id=output_id,
            property_reference_id=setup_general_property.id,
            output_key="perforation",
            output_value="value2",
            status="idle",
            created_at=int(time.time()),
            is_usable=1
        )
    ]
    
    db_session.bulk_save_objects(units)
    db_session.commit()
    
    # Update only coding units
    update_data = {
        "status": "ready",
        "output_value": ""
    }
    
    url = "/v1/pipeline-session-output-unit/all"
    params = {
        "pipeline_session_output_id": output_id,
        "output_key": "coding"
    }
    
    response = client.patch(url, params=params, json=update_data)
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Content: {response.text}")
    
    assert response.status_code == 200
    result = response.json()
    assert result["updated_count"] == 1
    
    # Refresh and verify final state
    db_session.expire_all()
    
    coding_units = db_session.query(PipelineSessionOutputUnit).filter_by(
        pipeline_session_output_id=output_id,
        output_key="coding"
    ).all()
    other_units = db_session.query(PipelineSessionOutputUnit).filter_by(
        pipeline_session_output_id=output_id,
        output_key="perforation"
    ).all()
    
    print("\nFinal database state:")
    print("Coding units:")
    for unit in coding_units:
        print(f"Unit ID: {unit.id}, Value: {unit.output_value}, Status: {unit.status}")
    print("Other units:")
    for unit in other_units:
        print(f"Unit ID: {unit.id}, Value: {unit.output_value}, Status: {unit.status}")
    
    assert all(unit.status == "ready" and unit.output_value == "" for unit in coding_units)
    assert all(unit.status == "idle" and unit.output_value == "value2" for unit in other_units)

def test_get_pipeline_session_output_unit(
    test_db,
    db_session,
    setup_pipeline_output,
    setup_general_property
):
    """Test getting a single pipeline session output unit"""
    unit = PipelineSessionOutputUnit(
        pipeline_session_output_id=setup_pipeline_output.id,
        property_reference_id=setup_general_property.id,
        output_key="test_key",
        output_value="test_value",
        status="idle",
        created_at=int(time.time()),
        is_usable=1
    )
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    
    response = client.get(f"/v1/pipeline-session-output-unit/{unit.id}")
    
    assert response.status_code == 200
    fetched_unit = response.json()
    assert fetched_unit["id"] == unit.id
    assert fetched_unit["output_key"] == "test_key"
    assert fetched_unit["output_value"] == "test_value"

def test_get_all_pipeline_session_output_units(
    test_db,
    db_session,
    setup_pipeline_output,
    setup_general_property
):
    """Test getting all pipeline session output units"""
    # Create multiple units
    units = []
    for i in range(3):
        unit = PipelineSessionOutputUnit(
            pipeline_session_output_id=setup_pipeline_output.id,
            property_reference_id=setup_general_property.id,
            output_key=f"key_{i}",
            output_value=f"value_{i}",
            status="idle",
            created_at=int(time.time()),
            is_usable=1
        )
        units.append(unit)
    
    db_session.bulk_save_objects(units)
    db_session.commit()
    
    response = client.get(f"/v1/pipeline-session-output-unit?pipeline_session_output_id={setup_pipeline_output.id}")
    
    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 3
    assert len(result["items"]) == 3