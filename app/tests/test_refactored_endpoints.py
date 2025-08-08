import logging
import time
from unittest.mock import Mock, patch

import pytest

from app.models.application import Application as ApplicationModel
from app.models.pipeline import Pipeline as PipelineModel
from app.models.pipeline_input import PipelineInput as PipelineInputModel
from app.models.pipeline_session import PipelineSession as PipelineSessionModel
from app.schemas.application import Application, ApplicationCreate
from app.schemas.pipeline import Pipeline, PipelineCreate
from app.schemas.pipeline_input import PipelineInputBase, PipelineInputResponse
from app.schemas.pipeline_session import PipelineSession, PipelineSessionCreate

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use shared test configuration from conftest.py

# All test methods now use test_client_admin fixture from conftest.py
# No need for module-level client initialization


class TestRefactoredApplicationEndpoints:
    """Test cases for refactored Application endpoints"""

    def test_create_application_success(self, test_client_admin):
        """Test POST /v1/application/new - Success case"""
        app_data = {"name": "Test Application", "is_usable": 1}

        response = test_client_admin.post("/v1/application/new", json=app_data)

        assert response.status_code == 201  # nosec B101
        data = response.json()
        assert data["name"] == "Test Application"  # nosec B101
        assert data["is_usable"] == 1  # nosec B101
        assert "id" in data  # nosec B101
        assert "created_at" in data  # nosec B101

    def test_create_application_duplicate_name(self, test_client_admin):
        """Test POST /v1/application/new - Duplicate name"""
        app_data = {"name": "Duplicate App", "is_usable": 1}

        # Create first application
        response1 = test_client_admin.post("/v1/application/new", json=app_data)
        assert response1.status_code == 201  # nosec B101

        # Try to create duplicate
        response2 = test_client_admin.post("/v1/application/new", json=app_data)
        assert response2.status_code == 400  # nosec B101
        assert "already exists" in response2.json()["detail"]  # nosec B101

    def test_get_all_applications_empty(self, test_client_admin):
        """Test GET /v1/application/all - Empty list"""
        response = test_client_admin.get("/v1/application/all")

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert isinstance(data, list)  # nosec B101
        assert len(data) == 0  # nosec B101

    def test_get_all_applications_with_data(self, test_client_admin):
        """Test GET /v1/application/all - With data"""
        # Create test applications
        app1 = {"name": "App 1", "is_usable": 1}
        app2 = {"name": "App 2", "is_usable": 1}

        test_client_admin.post("/v1/application/new", json=app1)
        test_client_admin.post("/v1/application/new", json=app2)

        response = test_client_admin.get("/v1/application/all")

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert len(data) == 2  # nosec B101
        assert data[0]["name"] in ["App 1", "App 2"]  # nosec B101
        assert data[1]["name"] in ["App 1", "App 2"]  # nosec B101

    def test_get_application_by_id_success(self, test_client_admin):
        """Test GET /v1/application/{id} - Success"""
        # Create test application
        app_data = {"name": "Test App", "is_usable": 1}
        create_response = test_client_admin.post("/v1/application/new", json=app_data)
        app_id = create_response.json()["id"]

        response = test_client_admin.get(f"/v1/application/{app_id}")

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert data["id"] == app_id  # nosec B101
        assert data["name"] == "Test App"  # nosec B101

    def test_get_application_not_found(self, test_client_admin):
        """Test GET /v1/application/{id} - Not found"""
        response = test_client_admin.get("/v1/application/999")

        assert response.status_code == 404  # nosec B101
        assert "not found" in response.json()["detail"].lower()  # nosec B101

    def test_update_application_success(self, test_client_admin):
        """Test PATCH /v1/application/{id} - Success"""
        # Create test application
        app_data = {"name": "Original Name", "is_usable": 1}
        create_response = test_client_admin.post("/v1/application/new", json=app_data)
        app_id = create_response.json()["id"]

        # Update application
        update_data = {"name": "Updated Name", "is_usable": 1}
        response = test_client_admin.patch(
            f"/v1/application/{app_id}", json=update_data
        )

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert data["name"] == "Updated Name"  # nosec B101
        assert data["id"] == app_id  # nosec B101

    def test_update_application_not_found(self, test_client_admin):
        """Test PATCH /v1/application/{id} - Not found"""
        update_data = {"name": "Updated Name", "is_usable": 1}
        response = test_client_admin.patch("/v1/application/999", json=update_data)

        assert response.status_code == 404  # nosec B101

    def test_delete_application_success(self, test_client_admin):
        """Test DELETE /v1/application/{id} - Success (soft delete)"""
        # Create test application
        app_data = {"name": "To Delete", "is_usable": 1}
        create_response = test_client_admin.post("/v1/application/new", json=app_data)
        app_id = create_response.json()["id"]

        # Delete application
        response = test_client_admin.delete(f"/v1/application/{app_id}")

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert data["id"] == app_id  # nosec B101
        assert data["is_usable"] == 0  # nosec B101 # Soft delete

    def test_delete_application_not_found(self, test_client_admin):
        """Test DELETE /v1/application/{id} - Not found"""
        response = test_client_admin.delete("/v1/application/999")

        assert response.status_code == 404  # nosec B101


class TestRefactoredPipelineEndpoints:
    """Test cases for refactored Pipeline endpoints"""

    def test_create_pipeline_success(self, test_client_admin, test_db):
        """Test POST /v1/pipeline/new - Success case"""
        # First create an application
        app_data = {"name": "Test App", "is_usable": 1}
        app_response = test_client_admin.post("/v1/application/new", json=app_data)
        app_id = app_response.json()["id"]

        pipeline_data = {
            "name": "Test Pipeline",
            "is_running": False,
            "application_id": app_id,
            "is_usable": 1,
        }

        response = test_client_admin.post("/v1/pipeline/new", json=pipeline_data)

        assert response.status_code == 201  # nosec B101
        data = response.json()
        assert data["name"] == "Test Pipeline"  # nosec B101
        assert data["application_id"] == app_id  # nosec B101
        assert "id" in data  # nosec B101
        assert "created_at" in data  # nosec B101

    def test_get_all_pipelines(self, test_client_admin, test_db):
        """Test GET /v1/pipeline/all"""
        response = test_client_admin.get("/v1/pipeline/all")

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert "total" in data  # nosec B101
        assert "items" in data  # nosec B101
        assert isinstance(data["items"], list)  # nosec B101

    def test_update_pipeline_success(self, test_client_admin, test_db):
        """Test PATCH /v1/pipeline/{id} - Success"""
        # First create an application
        app_data = {"name": "Test App", "is_usable": 1}
        app_response = test_client_admin.post("/v1/application/new", json=app_data)
        app_id = app_response.json()["id"]

        pipeline_data = {
            "name": "Original Pipeline",
            "is_running": False,
            "application_id": app_id,
            "is_usable": 1,
        }
        create_response = test_client_admin.post("/v1/pipeline/new", json=pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Update pipeline
        update_data = {
            "name": "Updated Pipeline",
            "is_running": True,
            "application_id": app_id,
            "is_usable": 1,
        }
        response = test_client_admin.patch(
            f"/v1/pipeline/{pipeline_id}", json=update_data
        )

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert data["name"] == "Updated Pipeline"  # nosec B101

    def test_delete_pipeline_success(self, test_client_admin, test_db):
        """Test DELETE /v1/pipeline/{id} - Success"""
        # First create an application
        app_data = {"name": "Test App", "is_usable": 1}
        app_response = test_client_admin.post("/v1/application/new", json=app_data)
        app_id = app_response.json()["id"]

        pipeline_data = {
            "name": "To Delete",
            "is_running": False,
            "application_id": app_id,
            "is_usable": 1,
        }
        create_response = test_client_admin.post("/v1/pipeline/new", json=pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Delete pipeline
        response = test_client_admin.delete(f"/v1/pipeline/{pipeline_id}")

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert data["is_usable"] == 0  # nosec B101 # Soft delete


class TestRefactoredPipelineInputEndpoints:
    """Test cases for refactored Pipeline Input endpoints"""

    def test_create_pipeline_input_success(self, test_client_admin, test_db):
        """Test POST /v1/pipeline-input/new - Success case"""
        input_data = {
            "name": "Test Input",
            "input_type": "image",
            "is_usable": 1,
        }

        response = test_client_admin.post("/v1/pipeline-input/new", json=input_data)

        assert response.status_code == 201  # nosec B101
        data = response.json()
        assert data["name"] == "Test Input"  # nosec B101
        assert data["is_usable"] == 1  # nosec B101
        assert "id" in data  # nosec B101
        assert "created_at" in data  # nosec B101

    def test_get_all_pipeline_inputs(self, test_client_admin, test_db):
        """Test GET /v1/pipeline-input/all"""
        # Create test inputs
        input1 = {"name": "Input 1", "input_type": "image", "is_usable": 1}
        input2 = {"name": "Input 2", "input_type": "text", "is_usable": 1}
        test_client_admin.post("/v1/pipeline-input/new", json=input1)
        test_client_admin.post("/v1/pipeline-input/new", json=input2)

        response = test_client_admin.get("/v1/pipeline-input/all")

        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert isinstance(data, list)  # nosec B101
        assert len(data) == 2  # nosec B101

    def test_get_pipeline_input_by_id(self, test_client_admin, test_db):
        """Test GET /v1/pipeline-input/{id}"""
        input_data = {
            "name": "Test Input",
            "input_type": "image",
            "is_usable": 1,
        }
        create_response = test_client_admin.post(
            "/v1/pipeline-input/new", json=input_data
        )
        input_id = create_response.json()["id"]

        response = test_client_admin.get(f"/v1/pipeline-input/{input_id}")

        assert response.status_code == 200  # nosec B101


class TestRefactoredPipelineSessionEndpoints:
    """Test cases for refactored Pipeline Session endpoints with authentication"""

    def test_create_pipeline_session_success(self, test_client_admin, test_db):
        """Test POST /v1/pipeline-session/new - Success with auth"""
        # Create dependencies
        app_data = {"name": "Test App", "is_usable": 1}
        app_response = test_client_admin.post("/v1/application/new", json=app_data)
        app_id = app_response.json()["id"]

        pipeline_data = {
            "name": "Test Pipeline",
            "is_running": False,
            "application_id": app_id,
            "is_usable": 1,
        }
        pipeline_response = test_client_admin.post(
            "/v1/pipeline/new", json=pipeline_data
        )
        pipeline_id = pipeline_response.json()["id"]

        input_data = {"name": "Test Input", "input_type": "image", "is_usable": 1}
        input_response = test_client_admin.post(
            "/v1/pipeline-input/new", json=input_data
        )
        input_id = input_response.json()["id"]

        # Create pipeline session
        session_data = {
            "pipeline_id": pipeline_id,
            "pipeline_input_id": input_id,
            "name": "Test Session",
        }

        response = test_client_admin.post("/v1/pipeline-session/new", json=session_data)

        assert response.status_code == 201  # nosec B101
        data = response.json()
        assert data["name"] == "Test Session"  # nosec B101
        assert data["pipeline_id"] == pipeline_id  # nosec B101
        assert data["created_by"] == "413"  # nosec B101 # Should be string, not int
        assert "id" in data  # nosec B101
        assert "created_at" in data  # nosec B101

    def test_create_pipeline_session_created_by_type(self, test_client_admin, test_db):
        """Test that created_by is properly set as string"""
        session_data = {"pipeline_id": 1, "name": "Type Test Session"}

        response = test_client_admin.post("/v1/pipeline-session/new", json=session_data)

        assert response.status_code == 201  # nosec B101
        data = response.json()
        assert isinstance(data["created_by"], str)  # nosec B101 # Must be string
        assert data["created_by"] == "413"  # nosec B101 # User ID as string

    def test_get_all_pipeline_sessions(self, test_client_admin, test_db):
        """Test GET /v1/pipeline-session/all"""
        response = test_client_admin.get("/v1/pipeline-session/all")

        assert response.status_code == 200  # nosec B101
        # The response format may vary based on your implementation


class TestServiceIntegration:
    """Integration tests to verify service layer works with endpoints"""

    def test_application_service_integration(self, test_client_admin, test_db):
        """Test that application service integrates properly with endpoints"""
        # Test the full flow: create -> get -> update -> delete

        # Create
        create_data = {"name": "Integration Test App", "is_usable": 1}
        create_response = test_client_admin.post(
            "/v1/application/new", json=create_data
        )
        assert create_response.status_code == 201  # nosec B101
        app_id = create_response.json()["id"]

        # Get
        get_response = test_client_admin.get(f"/v1/application/{app_id}")
        assert get_response.status_code == 200  # nosec B101
        assert get_response.json()["name"] == "Integration Test App"  # nosec B101

        # Update
        update_data = {"name": "Updated Integration App", "is_usable": 1}
        update_response = test_client_admin.patch(
            f"/v1/application/{app_id}", json=update_data
        )
        assert update_response.status_code == 200  # nosec B101
        assert update_response.json()["name"] == "Updated Integration App"  # nosec B101

        # Delete (soft)
        delete_response = test_client_admin.delete(f"/v1/application/{app_id}")
        assert delete_response.status_code == 200  # nosec B101
        assert delete_response.json()["is_usable"] == 0  # nosec B101

        # Verify it's not in active list
        all_response = test_client_admin.get("/v1/application/all")
        active_apps = [app for app in all_response.json() if app["is_usable"] == 1]
        app_names = [app["name"] for app in active_apps]
        assert "Updated Integration App" not in app_names  # nosec B101

    def test_error_handling_consistency(self, test_client_admin, test_db):
        """Test that error handling is consistent across refactored endpoints"""
        # Test 404 errors
        endpoints_404 = [
            "/v1/application/999",
            "/v1/pipeline/999",
            "/v1/pipeline-input/999",
        ]

        for endpoint in endpoints_404:
            response = test_client_admin.get(endpoint)
            assert response.status_code == 404  # nosec B101
            assert "not found" in response.json()["detail"].lower()  # nosec B101

    def test_validation_consistency(self, test_client_admin, test_db):
        """Test that validation is consistent across refactored endpoints"""
        # Test invalid data
        invalid_data = {"name": "", "is_usable": 1}  # Empty name

        endpoints = ["/v1/application/new", "/v1/pipeline-input/new"]

        for endpoint in endpoints:
            response = test_client_admin.post(endpoint, json=invalid_data)
            # Should return validation error (422 or 400)
            assert response.status_code in [400, 422]  # nosec B101
