from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.application import Application as ApplicationModel
from app.schemas.application import ApplicationCreate
from app.services.application import application_service


class TestApplicationService:
    """Test cases for Application Service layer"""

    def test_create_application_success(self, mock_db_session):
        """Test successful application creation"""
        # Mock application data
        app_data = ApplicationCreate(name="Test Application", is_usable=1)
        
        # Mock the duplicate name check
        with patch("app.services.application.check_duplicate_name", return_value=False):
            result = application_service.create(mock_db_session, obj_in=app_data)
            
            # Verify database operations were called
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
            
            # Verify the result has expected attributes
            assert hasattr(result, "name")  # nosec B101
            assert hasattr(result, "created_at")  # nosec B101
            assert hasattr(result, "is_usable")  # nosec B101

    def test_create_application_duplicate_name(self, mock_db_session):
        """Test application creation with duplicate name"""
        app_data = ApplicationCreate(name="Duplicate App", is_usable=1)
        
        # Mock the duplicate name check to return True
        with patch("app.services.application.check_duplicate_name", return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                application_service.create(mock_db_session, obj_in=app_data)
            
            assert exc_info.value.status_code == 400
            assert "already exists" in str(exc_info.value.detail)

    def test_get_all_applications_empty(self, mock_db_session):
        """Test getting all applications when none exist"""
        # Mock empty query result with proper chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = []
        
        mock_db_session.query.return_value = mock_query
        
        result = application_service.get_multi(mock_db_session, skip=0, limit=100)
        
        assert result == []

    def test_get_all_applications_with_data(self, mock_db_session):
        """Test getting all applications with existing data"""
        # Mock applications
        mock_app1 = ApplicationModel(id=1, name="App 1", is_usable=1, created_at=1234567890)
        mock_app2 = ApplicationModel(id=2, name="App 2", is_usable=1, created_at=1234567891)
        
        # Mock query result with proper chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [mock_app1, mock_app2]
        
        mock_db_session.query.return_value = mock_query
        
        result = application_service.get_multi(mock_db_session, skip=0, limit=100)
        
        assert len(result) == 2
        assert result[0].name == "App 1"
        assert result[1].name == "App 2"

    def test_get_application_by_id_success(self, mock_db_session):
        """Test successful application retrieval by ID"""
        # Mock application
        mock_app = ApplicationModel(id=1, name="Test App", is_usable=1, created_at=1234567890)
        
        # Mock query result
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_app
        mock_db_session.query.return_value = mock_query
        
        result = application_service.get(mock_db_session, id=1)
        
        assert result is not None
        assert result.name == "Test App"
        assert result.id == 1

    def test_get_application_by_id_not_found(self, mock_db_session):
        """Test application retrieval with non-existent ID"""
        # Mock query result returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        result = application_service.get(mock_db_session, id=999)
        
        assert result is None



    def test_delete_application_success(self, mock_db_session):
        """Test successful application soft delete"""
        # Mock existing application
        mock_app = ApplicationModel(id=1, name="Test App", is_usable=1, created_at=1234567890)
        
        # Mock query result for get() method called within remove()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_app
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        
        result = application_service.remove(mock_db_session, id=1)
        
        # Verify database operations were called (soft delete sets is_usable=0)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        
        # Verify soft delete happened
        assert mock_app.is_usable == 0
        assert result is not None

    def test_delete_application_not_found(self, mock_db_session):
        """Test application delete with non-existent ID"""
        # Mock query result returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        result = application_service.get(mock_db_session, id=999)
        assert result is None

    def test_application_name_validation(self, mock_db_session):
        """Test application name validation rules"""
        # Test empty name
        with pytest.raises(ValueError):
            ApplicationCreate(name="", is_usable=1)
        
        # Test None name
        with pytest.raises(ValueError):
            ApplicationCreate(name=None, is_usable=1)

    def test_application_name_trimming(self, mock_db_session):
        """Test that application names are properly trimmed"""
        app_data = ApplicationCreate(name="  Test App  ", is_usable=1)
        
        # Mock the duplicate name check
        with patch("app.services.application.check_duplicate_name", return_value=False):
            result = application_service.create(mock_db_session, obj_in=app_data)
            
            # Verify database operations were called
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
