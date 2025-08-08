from unittest.mock import Mock, patch, MagicMock
import time

import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from app.models.pipeline_session import PipelineSession as PipelineSessionModel
from app.schemas.pipeline_session import PipelineSessionBase, PipelineSessionCreate, PipelineSession, Pagination, Sort, Limit


class TestPipelineSessionService:
    """Test cases for Pipeline Session Service layer focusing on validation and core logic"""

    def test_pipeline_session_base_schema_validation_success(self, mock_db_session):
        """Test successful PipelineSessionBase schema validation"""
        # Test valid pipeline session data
        valid_session = PipelineSessionBase(
            pipeline_id=1,
            pipeline_input_id=2,
            name="Test Session",
            created_by="test_user",
            ended_at=1234567890
        )
        
        assert valid_session.pipeline_id == 1
        assert valid_session.pipeline_input_id == 2
        assert valid_session.name == "Test Session"
        assert valid_session.created_by == "test_user"
        assert valid_session.ended_at == 1234567890

    def test_pipeline_session_base_schema_validation_errors(self, mock_db_session):
        """Test PipelineSessionBase schema validation errors"""
        # Test missing required pipeline_id field
        with pytest.raises(ValidationError):
            PipelineSessionBase(
                pipeline_input_id=2,
                name="Test Session"
                # Missing required field: pipeline_id
            )

    def test_pipeline_session_base_optional_fields(self, mock_db_session):
        """Test PipelineSessionBase with optional fields"""
        # Test with only required field
        minimal_session = PipelineSessionBase(
            pipeline_id=1
            # All other fields are optional
        )
        
        assert minimal_session.pipeline_id == 1
        assert minimal_session.pipeline_input_id is None
        assert minimal_session.name is None
        assert minimal_session.created_by is None
        assert minimal_session.ended_at is None

    def test_pipeline_session_create_schema(self, mock_db_session):
        """Test PipelineSessionCreate schema"""
        # Test valid pipeline session create data
        valid_create = PipelineSessionCreate(
            pipeline_id=1,
            pipeline_input_id=2,
            name="Create Session",
            created_by="create_user"
        )
        
        assert valid_create.pipeline_id == 1
        assert valid_create.pipeline_input_id == 2
        assert valid_create.name == "Create Session"
        assert valid_create.created_by == "create_user"

    def test_pipeline_session_response_schema(self, mock_db_session):
        """Test PipelineSession response schema"""
        # Test valid pipeline session response
        session_response = PipelineSession(
            id=1,
            pipeline_id=1,
            pipeline_input_id=2,
            name="Response Session",
            created_by="response_user",
            ended_at=1234567890,
            created_at=1234567800,
            is_usable=1
        )
        
        assert session_response.id == 1
        assert session_response.pipeline_id == 1
        assert session_response.pipeline_input_id == 2
        assert session_response.name == "Response Session"
        assert session_response.created_by == "response_user"
        assert session_response.ended_at == 1234567890
        assert session_response.created_at == 1234567800
        assert session_response.is_usable == 1

    def test_pagination_schema_validation(self, mock_db_session):
        """Test Pagination schema validation"""
        # Test valid pagination
        valid_pagination = Pagination(page=1)
        assert valid_pagination.page == 1
        
        # Test default pagination
        default_pagination = Pagination()
        assert default_pagination.page == 1
        
        # Test invalid pagination (page < 1)
        with pytest.raises(HTTPException) as exc_info:
            Pagination(page=0)
        assert exc_info.value.status_code == 400
        assert "invalid page" in str(exc_info.value.detail)

    def test_sort_schema_validation(self, mock_db_session):
        """Test Sort schema validation"""
        # Test valid sort values
        ascending_sort = Sort(sort=0)
        assert ascending_sort.sort == 0
        
        descending_sort = Sort(sort=1)
        assert descending_sort.sort == 1
        
        # Test default sort
        default_sort = Sort()
        assert default_sort.sort == 0

    def test_limit_schema_validation(self, mock_db_session):
        """Test Limit schema validation"""
        # Test valid limit values
        no_limit = Limit(limit=-1)
        assert no_limit.limit == -1
        
        limited = Limit(limit=10)
        assert limited.limit == 10
        
        # Test default limit
        default_limit = Limit()
        assert default_limit.limit == -1

    def test_pipeline_session_created_by_types(self, mock_db_session):
        """Test pipeline session created_by field type validation"""
        # Test string created_by
        session_string = PipelineSessionBase(
            pipeline_id=1,
            created_by="string_user"
        )
        assert session_string.created_by == "string_user"
        
        # Test integer created_by
        session_int = PipelineSessionBase(
            pipeline_id=1,
            created_by=123
        )
        assert session_int.created_by == 123

    def test_pipeline_session_serialization(self, mock_db_session):
        """Test PipelineSession serialization"""
        session_data = PipelineSessionBase(
            pipeline_id=1,
            pipeline_input_id=2,
            name="Serialization Test",
            created_by="test_user",
            ended_at=1234567890
        )
        
        # Test dict conversion
        session_dict = session_data.dict()
        assert session_dict["pipeline_id"] == 1
        assert session_dict["pipeline_input_id"] == 2
        assert session_dict["name"] == "Serialization Test"
        assert session_dict["created_by"] == "test_user"
        assert session_dict["ended_at"] == 1234567890
        
        # Test JSON serialization
        session_json = session_data.json()
        assert "Serialization Test" in session_json
        assert "test_user" in session_json
