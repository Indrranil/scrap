from unittest.mock import Mock, patch, MagicMock
import time

import pytest
from pydantic import ValidationError

from app.models.pipeline import Pipeline as PipelineModel
from app.schemas.pipeline import PipelineBase, PipelineCreate, Pipeline


class TestPipelineService:
    """Test cases for Pipeline Service layer focusing on validation and core logic"""

    def test_pipeline_base_schema_validation_success(self, mock_db_session):
        """Test successful PipelineBase schema validation"""
        # Test valid pipeline data
        valid_pipeline = PipelineBase(
            name="Test Pipeline",
            is_running=0,
            application_id=1,
            is_usable=1
        )
        
        assert valid_pipeline.name == "Test Pipeline"
        assert valid_pipeline.is_running == 0
        assert valid_pipeline.application_id == 1
        assert valid_pipeline.is_usable == 1

    def test_pipeline_base_schema_validation_errors(self, mock_db_session):
        """Test PipelineBase schema validation errors"""
        # Test missing required fields
        with pytest.raises(ValidationError):
            PipelineBase(
                name="Test Pipeline"
                # Missing required fields: application_id, is_usable
            )

    def test_pipeline_base_default_values(self, mock_db_session):
        """Test PipelineBase default values"""
        # Test with default is_running value
        pipeline_with_defaults = PipelineBase(
            name="Test Pipeline",
            application_id=1,
            is_usable=1
            # is_running should use default value of 0
        )
        
        assert pipeline_with_defaults.is_running == 0  # Default value

    def test_pipeline_create_schema(self, mock_db_session):
        """Test PipelineCreate schema"""
        # Test valid pipeline create data
        valid_create = PipelineCreate(
            name="New Pipeline",
            is_running=1,
            application_id=2,
            is_usable=1
        )
        
        assert valid_create.name == "New Pipeline"
        assert valid_create.is_running == 1
        assert valid_create.application_id == 2
        assert valid_create.is_usable == 1

    def test_pipeline_response_schema(self, mock_db_session):
        """Test Pipeline response schema"""
        # Test valid pipeline response
        pipeline_response = Pipeline(
            id=1,
            name="Response Pipeline",
            is_running=0,
            application_id=1,
            is_usable=1,
            created_at=1234567890
        )
        
        assert pipeline_response.id == 1
        assert pipeline_response.name == "Response Pipeline"
        assert pipeline_response.is_running == 0
        assert pipeline_response.application_id == 1
        assert pipeline_response.is_usable == 1
        assert pipeline_response.created_at == 1234567890

    def test_pipeline_field_constraints(self, mock_db_session):
        """Test Pipeline field constraints"""
        # Test negative application_id (should be allowed as int)
        pipeline_negative_id = PipelineBase(
            name="Test Pipeline",
            application_id=-1,
            is_usable=1
        )
        assert pipeline_negative_id.application_id == -1
        
        # Test different is_running values
        for running_value in [0, 1]:
            pipeline = PipelineBase(
                name="Test Pipeline",
                is_running=running_value,
                application_id=1,
                is_usable=1
            )
            assert pipeline.is_running == running_value

    def test_pipeline_name_validation(self, mock_db_session):
        """Test pipeline name validation"""
        # Test empty name (allowed by schema)
        empty_name_pipeline = PipelineBase(
            name="",
            application_id=1,
            is_usable=1
        )
        assert empty_name_pipeline.name == ""
        assert empty_name_pipeline.application_id == 1
        
        # Test valid names with special characters
        valid_names = [
            "Pipeline-1",
            "Pipeline_Test",
            "Pipeline 123",
            "Test.Pipeline"
        ]
        
        for name in valid_names:
            pipeline = PipelineBase(
                name=name,
                application_id=1,
                is_usable=1
            )
            assert pipeline.name == name

    def test_pipeline_is_usable_values(self, mock_db_session):
        """Test pipeline is_usable field values"""
        # Test different is_usable values
        for usable_value in [0, 1]:
            pipeline = PipelineBase(
                name="Test Pipeline",
                application_id=1,
                is_usable=usable_value
            )
            assert pipeline.is_usable == usable_value

    def test_pipeline_serialization(self, mock_db_session):
        """Test Pipeline serialization"""
        pipeline_data = PipelineBase(
            name="Serialization Test",
            is_running=1,
            application_id=5,
            is_usable=1
        )
        
        # Test dict conversion
        pipeline_dict = pipeline_data.dict()
        assert pipeline_dict["name"] == "Serialization Test"
        assert pipeline_dict["is_running"] == 1
        assert pipeline_dict["application_id"] == 5
        assert pipeline_dict["is_usable"] == 1
        
        # Test JSON serialization
        pipeline_json = pipeline_data.json()
        assert "Serialization Test" in pipeline_json
        assert "5" in pipeline_json

    def test_pipeline_field_types(self, mock_db_session):
        """Test Pipeline field type validation"""
        # Test string conversion for numeric fields
        pipeline = PipelineBase(
            name="Type Test",
            is_running="1",  # String that can be converted to int
            application_id="123",  # String that can be converted to int
            is_usable="0"  # String that can be converted to int
        )
        
        assert pipeline.is_running == 1
        assert pipeline.application_id == 123
        assert pipeline.is_usable == 0
