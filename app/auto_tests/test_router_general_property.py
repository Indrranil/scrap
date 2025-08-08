from unittest.mock import Mock, patch, MagicMock
import time

import pytest
from pydantic import ValidationError

from app.models.general_property import GeneralProperty, PropertyType
from app.schemas.general_property import GeneralPropertyBase, GeneralPropertyUpdate, GeneralPropertyResponse


class TestGeneralPropertyService:
    """Test cases for General Property Service layer focusing on validation and core logic"""

    def test_general_property_base_schema_validation_success(self, mock_db_session):
        """Test successful GeneralPropertyBase schema validation"""
        # Test valid property data
        valid_property = GeneralPropertyBase(
            referrer_id=1,
            property_type="machine",
            property_key="temperature",
            property_label="Temperature",
            property_value="25°C",
            is_usable=1
        )
        
        assert valid_property.referrer_id == 1
        assert valid_property.property_type == "machine"
        assert valid_property.property_key == "temperature"
        assert valid_property.property_label == "Temperature"
        assert valid_property.property_value == "25°C"
        assert valid_property.is_usable == 1

    def test_general_property_base_schema_validation_errors(self, mock_db_session):
        """Test GeneralPropertyBase schema validation errors"""
        # Test missing required fields
        with pytest.raises(ValidationError):
            GeneralPropertyBase(
                property_key="temperature"
                # Missing required fields: referrer_id, property_type, property_label, property_value
            )
        
        # Test invalid property_type
        with pytest.raises(ValidationError):
            GeneralPropertyBase(
                referrer_id=1,
                property_type="invalid_type",  # Not in allowed literals
                property_key="temperature",
                property_label="Temperature",
                property_value="25°C"
            )

    def test_general_property_base_default_values(self, mock_db_session):
        """Test GeneralPropertyBase default values"""
        # Test with default values
        property_with_defaults = GeneralPropertyBase(
            referrer_id=1,
            property_type="pipeline",
            property_key="pressure",
            property_label="Pressure",
            property_value="1013 hPa"
            # tags and is_usable should use defaults
        )
        
        assert property_with_defaults.tags == ""  # Default value
        assert property_with_defaults.is_usable == 1  # Default value

    def test_general_property_update_schema_validation(self, mock_db_session):
        """Test GeneralPropertyUpdate schema validation"""
        # Test valid partial update
        valid_update = GeneralPropertyUpdate(
            property_label="Updated Temperature",
            property_value="30°C"
        )
        
        assert valid_update.property_label == "Updated Temperature"
        assert valid_update.property_value == "30°C"
        assert valid_update.referrer_id is None  # Optional field
        assert valid_update.property_type is None  # Optional field

    def test_general_property_response_schema(self, mock_db_session):
        """Test GeneralPropertyResponse schema"""
        # Test valid property response
        property_response = GeneralPropertyResponse(
            id=1,
            referrer_id=1,
            property_type="application",
            property_key="version",
            property_label="Version",
            property_value="1.0.0",
            tags="release",
            is_usable=1,
            created_at=1234567890
        )
        
        assert property_response.id == 1
        assert property_response.referrer_id == 1
        assert property_response.property_type == "application"
        assert property_response.property_key == "version"
        assert property_response.property_label == "Version"
        assert property_response.property_value == "1.0.0"
        assert property_response.tags == "release"
        assert property_response.is_usable == 1
        assert property_response.created_at == 1234567890

    def test_property_type_literals(self, mock_db_session):
        """Test property_type literal validation"""
        # Test all valid property types
        valid_types = ["machine", "pipeline", "application", "pipeline_input"]
        
        for prop_type in valid_types:
            valid_property = GeneralPropertyBase(
                referrer_id=1,
                property_type=prop_type,
                property_key="test_key",
                property_label="Test Label",
                property_value="test_value"
            )
            assert valid_property.property_type == prop_type

    def test_general_property_field_constraints(self, mock_db_session):
        """Test GeneralPropertyBase field constraints"""
        # Test negative referrer_id (should be allowed as int)
        property_negative_id = GeneralPropertyBase(
            referrer_id=-1,
            property_type="machine",
            property_key="test",
            property_label="Test",
            property_value="value"
        )
        assert property_negative_id.referrer_id == -1

    def test_general_property_optional_tags(self, mock_db_session):
        """Test GeneralPropertyBase with optional tags field"""
        # Test with tags
        property_with_tags = GeneralPropertyBase(
            referrer_id=1,
            property_type="pipeline",
            property_key="flow_rate",
            property_label="Flow Rate",
            property_value="100 L/min",
            tags="sensor,critical"
        )
        
        assert property_with_tags.tags == "sensor,critical"
        
        # Test without tags (should use default)
        property_without_tags = GeneralPropertyBase(
            referrer_id=1,
            property_type="pipeline",
            property_key="flow_rate",
            property_label="Flow Rate",
            property_value="100 L/min"
        )
        
        assert property_without_tags.tags == ""

    def test_general_property_update_all_fields(self, mock_db_session):
        """Test GeneralPropertyUpdate with all fields"""
        # Test updating all fields
        full_update = GeneralPropertyUpdate(
            referrer_id=2,
            property_type="application",
            property_label="Updated Label",
            property_key="updated_key",
            property_value="updated_value",
            tags="updated,tags",
            is_usable=0
        )
        
        assert full_update.referrer_id == 2
        assert full_update.property_type == "application"
        assert full_update.property_label == "Updated Label"
        assert full_update.property_key == "updated_key"
        assert full_update.property_value == "updated_value"
        assert full_update.tags == "updated,tags"
        assert full_update.is_usable == 0

    def test_general_property_update_partial_fields(self, mock_db_session):
        """Test GeneralPropertyUpdate with partial field updates"""
        # Test updating only some fields
        partial_updates = [
            GeneralPropertyUpdate(referrer_id=5),
            GeneralPropertyUpdate(property_label="New Label"),
            GeneralPropertyUpdate(is_usable=0),
            GeneralPropertyUpdate(tags="new,tags")
        ]
        
        for update in partial_updates:
            # All other fields should be None (optional)
            if update.referrer_id is not None:
                assert update.referrer_id == 5
            if update.property_label is not None:
                assert update.property_label == "New Label"
            if update.is_usable is not None:
                assert update.is_usable == 0
            if update.tags is not None:
                assert update.tags == "new,tags"

    def test_general_property_serialization(self, mock_db_session):
        """Test GeneralPropertyBase serialization"""
        property_data = GeneralPropertyBase(
            referrer_id=1,
            property_type="machine",
            property_key="temperature",
            property_label="Temperature",
            property_value="25°C",
            tags="sensor",
            is_usable=1
        )
        
        # Test dict conversion
        property_dict = property_data.dict()
        assert property_dict["referrer_id"] == 1
        assert property_dict["property_type"] == "machine"
        assert property_dict["property_key"] == "temperature"
        assert property_dict["property_label"] == "Temperature"
        assert property_dict["property_value"] == "25°C"
        assert property_dict["tags"] == "sensor"
        assert property_dict["is_usable"] == 1
        
        # Test JSON serialization
        property_json = property_data.json()
        assert "temperature" in property_json
        assert "machine" in property_json
        assert "25°C" in property_json
