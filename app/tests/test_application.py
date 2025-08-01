import logging
import time
from datetime import datetime
from typing import Optional

import pytest
from pydantic import BaseModel, ValidationError, validator
from sqlalchemy.orm import Session

from app.models.application import Application as ApplicationModel
from app.schemas.application import ApplicationCreate

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Test functions now use shared fixtures from conftest.py


def test_create_application_success(test_client_admin, sample_application_data):
    """Test successful application creation"""
    logger.info("Testing application creation")
    logger.debug(f"Request data: {sample_application_data}")

    response = test_client_admin.post("/v1/application/", json=sample_application_data)
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")

    assert response.status_code == 201  # nosec B101
    data = response.json()
    assert data["name"] == sample_application_data["name"]  # nosec B101
    assert data["is_usable"] == 1  # nosec B101
    assert "id" in data  # nosec B101
    assert "created_at" in data  # nosec B101


def test_create_application_empty_name(test_client_admin):
    """Test application creation with empty name"""
    with pytest.raises(ValidationError):
        ApplicationCreate(name="", is_usable=1)

    response = test_client_admin.post(
        "/v1/application/", json={"name": "", "is_usable": 1}
    )
    assert response.status_code == 422  # nosec B101
    assert (
        "Value error, Name cannot be empty" in response.json()["detail"][0]["msg"]
    )  # nosec B101


def test_create_application_missing_name(test_client_admin):
    """Test application creation with missing name"""
    response = test_client_admin.post("/v1/application/", json={"is_usable": 1})
    assert response.status_code == 422  # nosec B101


def test_create_application_very_long_name(test_client_admin):
    """Test application creation with name exceeding max length"""
    long_name = "x" * 256
    with pytest.raises(ValidationError):
        ApplicationCreate(name=long_name, is_usable=1)

    response = test_client_admin.post(
        "/v1/application/", json={"name": long_name, "is_usable": 1}
    )
    assert response.status_code == 422  # nosec B101
    assert (
        "Value error, Name cannot exceed 255 characters"  # nosec B101
        in response.json()["detail"][0]["msg"]  # nosec B101
    )


def test_get_all_applications_empty(test_client_admin):
    """Test getting all applications when none exist"""
    response = test_client_admin.get("/v1/application/all")
    assert response.status_code == 200  # nosec B101
    assert response.json() == []  # nosec B101


def test_get_all_applications_with_data(
    test_client_admin, db_session, sample_application_data
):
    """Test getting all applications with existing data"""
    # Create multiple applications
    apps = []
    for i in range(3):
        app = ApplicationModel(
            name=f"Test App {i}", created_at=int(time.time()), is_usable=1
        )
        apps.append(app)

    db_session.bulk_save_objects(apps)
    db_session.commit()

    response = test_client_admin.get("/v1/application/all")
    assert response.status_code == 200  # nosec B101
    data = response.json()
    assert len(data) == 3  # nosec B101
    assert all(app["is_usable"] == 1 for app in data)  # nosec B101


def test_get_application_by_id_success(
    test_client_admin, db_session, sample_application_data
):
    """Test getting a specific application by ID"""
    # Create an application
    app = ApplicationModel(
        name=sample_application_data["name"], created_at=int(time.time()), is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    response = test_client_admin.get(f"/v1/application/{app.id}")
    assert response.status_code == 200  # nosec B101
    data = response.json()
    assert data["name"] == sample_application_data["name"]  # nosec B101
    assert data["id"] == app.id  # nosec B101


def test_get_application_not_found(test_client_admin):
    """Test getting non-existent application"""
    response = test_client_admin.get("/v1/application/999")
    assert response.status_code == 404  # nosec B101
    assert "not found" in response.json()["detail"]  # nosec B101


def test_update_application_success(
    test_client_admin, db_session, sample_application_data
):
    """Test successful application update"""
    # Create an application
    app = ApplicationModel(
        name=sample_application_data["name"], created_at=int(time.time()), is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    # Update the application
    update_data = {"name": "Updated App Name", "is_usable": 1}
    response = test_client_admin.patch(f"/v1/application/{app.id}", json=update_data)

    assert response.status_code == 200  # nosec B101
    data = response.json()
    assert data["name"] == "Updated App Name"  # nosec B101
    assert data["id"] == app.id  # nosec B101


def test_update_application_not_found(test_client_admin):
    """Test updating non-existent application"""
    update_data = {"name": "Updated App Name", "is_usable": 1}
    response = test_client_admin.patch("/v1/application/999", json=update_data)
    assert response.status_code == 404  # nosec B101


def test_update_application_invalid_data(
    test_client_admin, db_session, sample_application_data
):
    """Test updating application with invalid data"""
    # Create an application
    app = ApplicationModel(
        name=sample_application_data["name"], created_at=int(time.time()), is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    # Try to update with empty name
    update_data = {"name": "", "is_usable": 1}
    response = test_client_admin.patch(f"/v1/application/{app.id}", json=update_data)
    assert response.status_code == 422  # nosec B101
    assert (
        "Value error, Name cannot be empty" in response.json()["detail"][0]["msg"]
    )  # nosec B101


def test_delete_application_success(
    test_client_admin, db_session, sample_application_data
):
    """Test successful application deletion (soft delete)"""
    # Create an application
    app = ApplicationModel(
        name=sample_application_data["name"], created_at=int(time.time()), is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    response = test_client_admin.delete(f"/v1/application/{app.id}")
    assert response.status_code == 200  # nosec B101

    # Verify soft delete
    db_session.expire_all()
    deleted_app = db_session.query(ApplicationModel).filter_by(id=app.id).first()
    assert deleted_app.is_usable == 0  # nosec B101


def test_delete_application_not_found(test_client_admin):
    """Test deleting non-existent application"""
    response = test_client_admin.delete("/v1/application/999")
    assert response.status_code == 404  # nosec B101


def test_delete_already_deleted_application(
    test_client_admin, db_session, sample_application_data
):
    """Test deleting an already deleted application"""
    # Create a deleted application
    app = ApplicationModel(
        name=sample_application_data["name"],
        created_at=int(time.time()),
        is_usable=0,  # Already deleted
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    response = test_client_admin.delete(f"/v1/application/{app.id}")
    assert response.status_code == 404  # nosec B101


def test_concurrent_updates(test_client_admin, db_session, sample_application_data):
    """Test handling concurrent updates to the same application"""
    # Create an application
    app = ApplicationModel(
        name=sample_application_data["name"], created_at=int(time.time()), is_usable=1
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)

    # Simulate concurrent updates
    update_data_1 = {"name": "Update 1", "is_usable": 1}
    update_data_2 = {"name": "Update 2", "is_usable": 1}

    response1 = test_client_admin.patch(f"/v1/application/{app.id}", json=update_data_1)
    response2 = test_client_admin.patch(f"/v1/application/{app.id}", json=update_data_2)

    assert response1.status_code == 200  # nosec B101
    assert response2.status_code == 200  # nosec B101

    # Verify final state
    final_response = test_client_admin.get(f"/v1/application/{app.id}")
    assert final_response.json()["name"] == "Update 2"  # nosec B101


def test_application_name_uniqueness(
    test_client_admin, db_session, sample_application_data
):
    """Test handling duplicate application names"""
    # Create first application
    app1 = ApplicationModel(
        name=sample_application_data["name"], created_at=int(time.time()), is_usable=1
    )
    db_session.add(app1)
    db_session.commit()
    db_session.refresh(app1)

    # Try to create second application with same name
    response = test_client_admin.post("/v1/application/", json=sample_application_data)
    assert response.status_code == 400  # nosec B101
    assert (
        "Application with this name already exists" in response.json()["detail"]
    )  # nosec B101


# Add a helper function to check for duplicate names
def check_duplicate_name(
    db: Session, name: str, exclude_id: Optional[int] = None
) -> bool:
    """Check if an application with the given name already exists"""
    query = db.query(ApplicationModel).filter(
        ApplicationModel.name == name, ApplicationModel.is_usable == 1
    )
    if exclude_id:
        query = query.filter(ApplicationModel.id != exclude_id)
    return db.query(query.exists()).scalar()
