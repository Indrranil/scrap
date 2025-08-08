from unittest.mock import Mock, patch, MagicMock
import time

import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from app.models.pipeline_input import PipelineInput as PipelineInputModel
from app.schemas.pipeline_input import PipelineInputBase, PipelineInputResponse


class TestPipelineInputService:
    """Test cases for Pipeline Input Service layer focusing on validation and core logic"""

    def test_pipeline_input_base_schema_validation_success(self, mock_db_session):
        """Test successful PipelineInputBase schema validation"""
        # Test valid pipeline input data
        valid_input = PipelineInputBase(
            name="Test Input"
        )
        
        assert valid_input.name == "Test Input"
        assert valid_input.is_usable == 1  # Default value

    def test_pipeline_input_base_required_fields(self, mock_db_session):
        """Test PipelineInputBase required fields validation"""
        # Test missing required name field
        with pytest.raises(ValidationError) as exc_info:
            PipelineInputBase(
                description="Test Description"
                # Missing required field: name
            )
        
        # Verify the validation error is about the missing name field
        error_details = str(exc_info.value)
        assert "name" in error_details.lower()

    def test_pipeline_input_base_optional_fields(self, mock_db_session):
        """Test PipelineInputBase with optional fields"""
        # Test with only required field
        minimal_input = PipelineInputBase(
            name="Minimal Input"
        )
        
        assert minimal_input.name == "Minimal Input"
        assert minimal_input.is_usable == 1  # Default value

    def test_pipeline_input_create_schema(self, mock_db_session):
        """Test PipelineInputBase schema for creation"""
        # Test valid pipeline input create data
        valid_create = PipelineInputBase(
            name="Create Input"
        )
        
        assert valid_create.name == "Create Input"
        assert valid_create.is_usable == 1  # Default value

    def test_pipeline_input_response_schema(self, mock_db_session):
        """Test PipelineInputResponse response schema"""
        # Test valid pipeline input response
        input_response = PipelineInputResponse(
            id=1,
            name="Response Input",
            created_at=1234567890,
            is_usable=1
        )
        
        assert input_response.id == 1
        assert input_response.name == "Response Input"
        assert input_response.created_at == 1234567890
        assert input_response.is_usable == 1

    def test_pipeline_input_name_validation(self, mock_db_session):
        """Test pipeline input name field validation"""
        # Test empty string name (allowed by schema)
        empty_input = PipelineInputBase(name="")
        assert empty_input.name == ""
        
        # Test whitespace-only name (allowed by schema)
        whitespace_input = PipelineInputBase(name="   ")
        assert whitespace_input.name == "   "
        
        # Test valid name with spaces
        valid_input = PipelineInputBase(name="Valid Input Name")
        assert valid_input.name == "Valid Input Name"

    def test_pipeline_input_is_usable_validation(self, mock_db_session):
        """Test pipeline input is_usable field validation"""
        # Test default is_usable value
        input_default = PipelineInputBase(
            name="Test Input"
        )
        assert input_default.is_usable == 1
        
        # Test explicit is_usable value
        input_explicit = PipelineInputBase(
            name="Test Input",
            is_usable=0
        )
        assert input_explicit.is_usable == 0
        
        # Test is_usable type coercion
        input_coerced = PipelineInputBase(
            name="Test Input",
            is_usable=True
        )
        assert input_coerced.is_usable == 1

    def test_pipeline_input_unicode_support(self, mock_db_session):
        """Test pipeline input unicode character support"""
        # Test unicode characters in name
        unicode_input = PipelineInputBase(
            name="测试输入 🚀"
        )
        
        assert unicode_input.name == "测试输入 🚀"
        assert unicode_input.is_usable == 1

    def test_pipeline_input_type_validation(self, mock_db_session):
        """Test pipeline input type validation"""
        # Test that name must be a string (no automatic coercion)
        with pytest.raises(ValidationError):
            PipelineInputBase(name=12345)
        
        # Test valid string name
        valid_input = PipelineInputBase(name="12345")
        assert valid_input.name == "12345"
        assert isinstance(valid_input.name, str)

    def test_pipeline_input_edge_cases(self, mock_db_session):
        """Test pipeline input edge cases"""
        # Test very long name
        long_name = "A" * 255
        input_long_name = PipelineInputBase(name=long_name)
        assert input_long_name.name == long_name
        
        # Test name with special characters
        special_name = "Input-Name_123!@#$%^&*()"
        input_special = PipelineInputBase(name=special_name)
        assert input_special.name == special_name

    def test_pipeline_input_serialization(self, mock_db_session):
        """Test PipelineInput serialization"""
        input_data = PipelineInputBase(
            name="Serialization Test"
        )
        
        # Test dict conversion
        input_dict = input_data.dict()
        assert input_dict["name"] == "Serialization Test"
        assert input_dict["is_usable"] == 1
        
        # Test JSON serialization
        input_json = input_data.json()
        assert "Serialization Test" in input_json
        assert "is_usable" in input_json

    def test_pipeline_input_defaults(self, mock_db_session):
        """Test PipelineInputResponse default values"""
        # Test PipelineInputResponse with defaults
        input_with_defaults = PipelineInputResponse(
            id=1,
            name="Default Test",
            created_at=int(time.time())
        )
        
        assert input_with_defaults.id == 1
        assert input_with_defaults.name == "Default Test"
        assert input_with_defaults.is_usable == 1  # Default value
        assert isinstance(input_with_defaults.created_at, int)

    def test_pipeline_input_model_fields(self, mock_db_session):
        """Test PipelineInputResponse model field presence"""
        # Test that all expected fields are present in the response schema
        input_response = PipelineInputResponse(
            id=1,
            name="Field Test",
            created_at=1234567890,
            is_usable=1
        )
        
        # Verify all expected fields are accessible
        assert hasattr(input_response, 'id')
        assert hasattr(input_response, 'name')
        assert hasattr(input_response, 'created_at')
        assert hasattr(input_response, 'is_usable')
