import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import Base, get_db
from main import app
from models.general_property import GeneralProperty
from models.pipeline_input_referrer import PipelineInputReferrer

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    
    # Add test general properties
    current_timestamp = int(datetime.now().timestamp() * 1000)
    test_properties = [
        GeneralProperty(
            id=1,
            property_type="machine",
            property_label="IP Address",
            property_key="ip_address",
            property_value="192.168.1.1",
            created_at=current_timestamp,
            is_usable=1
        ),
        GeneralProperty(
            id=2,
            property_type="pipeline_input",
            property_label="Weight",
            property_key="target_weight",
            property_value="100",
            created_at=current_timestamp,
            is_usable=1
        ),
        # Add a duplicate property label to test grouping
        GeneralProperty(
            id=3,
            property_type="pipeline_input",
            property_label="Weight",
            property_key="target_weight",
            property_value="200",
            created_at=current_timestamp,
            is_usable=1
        ),
        # Add an unusable property
        GeneralProperty(
            id=4,
            property_type="pipeline_input",
            property_label="Inactive Property",
            property_key="inactive",
            property_value="value",
            created_at=current_timestamp,
            is_usable=0
        )
    ]
    
    # Add test pipeline input referrer
    test_referrer = PipelineInputReferrer(
        id=1,
        key="cld_barcode",
        value="123456",
        pipeline_input_id=1,
        created_at=current_timestamp,
        is_usable=1
    )
    
    db.add_all(test_properties)
    db.add(test_referrer)
    db.commit()
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

def test_get_machine_properties():
    """Test getting machine type properties"""
    response = client.get("/v1/property-description/machine")
    assert response.status_code == 200
    data = response.json()
    
    assert "total" in data
    assert "properties" in data
    assert data["total"] == 1
    
    property_data = data["properties"][0]
    assert property_data["property_label"] == "IP Address"
    assert property_data["property_key"] == "ip_address"
    assert property_data["property_type"] == "machine"

def test_get_pipeline_input_properties():
    """Test getting pipeline_input type properties with CLD barcode"""
    response = client.get("/v1/property-description/pipeline_input")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 2  # Weight property + CLD barcode
    
    # Check if CLD barcode is included
    cld_barcode_exists = any(
        prop["property_key"] == "cld_barcode" 
        for prop in data["properties"]
    )
    assert cld_barcode_exists

def test_invalid_property_type():
    """Test requesting an invalid property type"""
    response = client.get("/v1/property-description/invalid_type")
    assert response.status_code == 400
    assert "Invalid property type" in response.json()["detail"]

def test_property_grouping():
    """Test that duplicate property labels are properly grouped"""
    response = client.get("/v1/property-description/pipeline_input")
    assert response.status_code == 200
    data = response.json()
    
    # Count Weight properties (should be 1 due to grouping)
    weight_props = [
        prop for prop in data["properties"] 
        if prop["property_label"] == "Weight"
    ]
    assert len(weight_props) == 1

def test_inactive_properties_excluded():
    """Test that inactive properties are not included"""
    response = client.get("/v1/property-description/pipeline_input")
    assert response.status_code == 200
    data = response.json()
    
    # Check that inactive property is not included
    inactive_exists = any(
        prop["property_label"] == "Inactive Property" 
        for prop in data["properties"]
    )
    assert not inactive_exists

def test_database_error_handling(monkeypatch):
    """Test handling of database errors"""
    def mock_db_error(*args, **kwargs):
        raise Exception("Database error")
    
    # Mock the database query to raise an error
    monkeypatch.setattr(
        "sqlalchemy.orm.Session.query",
        mock_db_error
    )
    
    response = client.get("/v1/property-description/machine")
    assert response.status_code == 500
    assert "Error fetching properties" in response.json()["detail"]