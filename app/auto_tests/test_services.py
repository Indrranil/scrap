import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.application import Application as ApplicationModel
from app.models.pipeline import Pipeline as PipelineModel
from app.models.pipeline_input import PipelineInput as PipelineInputModel
from app.models.pipeline_session import PipelineSession as PipelineSessionModel
from app.schemas.application import ApplicationCreate
from app.schemas.pipeline import PipelineCreate
from app.schemas.pipeline_input import PipelineInputBase
from app.schemas.pipeline_session import PipelineSessionCreate
from app.services.application import application_service
from app.services.pipeline import pipeline_service
from app.services.pipeline_input import pipeline_input_service
from app.services.pipeline_session import pipeline_session_service


class TestApplicationService:
    """Test cases for ApplicationService"""

    def test_create_application_success(self):
        """Test successful application creation"""
        # Mock database session
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Mock application data
        app_data = ApplicationCreate(name="Test App", is_usable=1)

        # Mock the duplicate name check
        with patch("app.services.application.check_duplicate_name", return_value=False):
            result = application_service.create(mock_db, obj_in=app_data)

            # Verify database operations were called
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

            # Verify the result has expected attributes
            assert hasattr(result, "name")  # nosec B101
            assert hasattr(result, "created_at")  # nosec B101
            assert hasattr(result, "is_usable")  # nosec B101

    def test_create_application_duplicate_name(self):
        """Test application creation with duplicate name"""
        mock_db = Mock(spec=Session)
        app_data = ApplicationCreate(name="Duplicate App", is_usable=1)

        # Mock duplicate name check to return True
        with patch("app.services.application.check_duplicate_name", return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                application_service.create(mock_db, obj_in=app_data)

            assert exc_info.value.status_code == 400  # nosec B101
            assert "already exists" in exc_info.value.detail  # nosec B101

    def test_get_application_success(self):
        """Test successful application retrieval"""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = ApplicationModel(id=1, name="Test App")

        result = application_service.get(mock_db, id=1)

        assert result is not None  # nosec B101
        assert result.id == 1  # nosec B101
        assert result.name == "Test App"  # nosec B101

    def test_get_application_not_found(self):
        """Test application retrieval when not found"""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = application_service.get(mock_db, id=999)

        assert result is None  # nosec B101

    def test_get_all_applications(self):
        """Test getting all applications"""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            ApplicationModel(id=1, name="App 1"),
            ApplicationModel(id=2, name="App 2"),
        ]

        result = application_service.get_all(mock_db)

        assert len(result) == 2  # nosec B101
        assert result[0].name == "App 1"  # nosec B101
        assert result[1].name == "App 2"  # nosec B101

    def test_update_application_success(self):
        """Test successful application update"""
        mock_db = Mock(spec=Session)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        existing_app = ApplicationModel(id=1, name="Old Name")
        update_data = ApplicationCreate(name="New Name", is_usable=1)

        result = application_service.update(
            mock_db, db_obj=existing_app, obj_in=update_data
        )

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result.name == "New Name"  # nosec B101

    def test_remove_application_success(self):
        """Test successful application soft delete"""
        mock_db = Mock(spec=Session)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Mock get method to return an application
        with patch.object(
            application_service,
            "get",
            return_value=ApplicationModel(id=1, name="Test App"),
        ):
            result = application_service.remove(mock_db, id=1)

            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
            assert result.is_usable == 0  # nosec B101

    def test_remove_application_not_found(self):
        """Test application soft delete when not found"""
        mock_db = Mock(spec=Session)

        # Mock get method to return None
        with patch.object(application_service, "get", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                application_service.remove(mock_db, id=999)

            assert exc_info.value.status_code == 404  # nosec B101


class TestPipelineService:
    """Test cases for PipelineService"""

    def test_create_pipeline_success(self):
        """Test successful pipeline creation"""
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        pipeline_data = PipelineCreate(
            name="Test Pipeline", is_running=False, application_id=1, is_usable=1
        )

        result = pipeline_service.create(mock_db, obj_in=pipeline_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert hasattr(result, "name")  # nosec B101
        assert hasattr(result, "created_at")  # nosec B101

    def test_get_pipeline_success(self):
        """Test successful pipeline retrieval"""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = PipelineModel(id=1, name="Test Pipeline")

        result = pipeline_service.get(mock_db, id=1)

        assert result is not None  # nosec B101
        assert result.id == 1  # nosec B101
        assert result.name == "Test Pipeline"  # nosec B101


class TestPipelineInputService:
    """Test cases for PipelineInputService"""

    def test_create_pipeline_input_success(self):
        """Test successful pipeline input creation"""
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        input_data = PipelineInputBase(name="Test Input", is_usable=1)

        result = pipeline_input_service.create(mock_db, obj_in=input_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert hasattr(result, "name")  # nosec B101
        assert hasattr(result, "created_at")  # nosec B101

    def test_get_all_pipeline_inputs(self):
        """Test getting all pipeline inputs"""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [
            PipelineInputModel(id=1, name="Input 1"),
            PipelineInputModel(id=2, name="Input 2"),
        ]

        result = pipeline_input_service.get_all(mock_db)

        assert len(result) == 2  # nosec B101
        assert result[0].name == "Input 1"  # nosec B101
        assert result[1].name == "Input 2"  # nosec B101


class TestPipelineSessionService:
    """Test cases for PipelineSessionService"""

    def test_create_with_user_success(self):
        """Test successful pipeline session creation with user"""
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        session_data = PipelineSessionCreate(
            pipeline_id=1, pipeline_input_id=1, name="Test Session"
        )

        result = pipeline_session_service.create_with_user(
            mock_db, obj_in=session_data, user_id=123
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert hasattr(result, "name")  # nosec B101
        assert hasattr(result, "created_at")  # nosec B101
        assert hasattr(result, "created_by")  # nosec B101

    # def test_create_with_user_string_conversion(self):
    #     """Test that user_id is properly converted to string"""
    #     mock_db = Mock(spec=Session)
    #     mock_db.add = Mock()
    #     mock_db.commit = Mock()
    #     mock_db.refresh = Mock()

    #     session_data = PipelineSessionCreate(
    #         pipeline_id=1,
    #         name="Test Session"
    #     )

    #     # Mock the model creation to capture the arguments
    #     with patch('app.services.pipeline_session.PipelineSessionModel') as mock_model:
    #         mock_instance = Mock()
    #         mock_model.return_value = mock_instance

    #         pipeline_session_service.create_with_user(
    #             mock_db,
    #             obj_in=session_data,
    #             user_id=123
    #         )

    #         # Verify that the model was called and created_by was set
    #         mock_model.assert_called_once()
    #         if mock_model.call_args and mock_model.call_args[1]:
    #             call_args = mock_model.call_args[1]  # Get keyword arguments
    #             assert "created_by" in call_args
    #             assert call_args["created_by"] == "123"  # Should be string
    #             assert isinstance(call_args["created_by"], str)
    #         else:
    #             # Alternative check: verify the service method was called successfully
    #             mock_db.add.assert_called_once()
    #             mock_db.commit.assert_called_once()

    def test_get_pipeline_session_success(self):
        """Test successful pipeline session retrieval"""
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = PipelineSessionModel(id=1, name="Test Session")

        result = pipeline_session_service.get(mock_db, id=1)

        assert result is not None  # nosec B101
        assert result.id == 1  # nosec B101
        assert result.name == "Test Session"  # nosec B101


class TestCRUDBaseGeneric:
    """Test cases for the generic CRUD base functionality"""

    def test_get_or_404_success(self):
        """Test get_or_404 when record exists"""
        mock_db = Mock(spec=Session)

        # Mock get method to return a record
        with patch.object(
            application_service, "get", return_value=ApplicationModel(id=1, name="Test")
        ):
            result = application_service.get_or_404(mock_db, id=1)
            assert result is not None  # nosec B101
            assert result.id == 1  # nosec B101

    def test_get_or_404_not_found(self):
        """Test get_or_404 when record doesn't exist"""
        mock_db = Mock(spec=Session)

        # Mock get method to return None
        with patch.object(application_service, "get", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                application_service.get_or_404(mock_db, id=999)

            assert exc_info.value.status_code == 404  # nosec B101
            assert "not found" in exc_info.value.detail.lower()  # nosec B101
