import json
import os
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

# All test methods now use test_client_admin fixture from conftest.py
# No need for module-level client initialization

# Mock successful response from Keycloak
MOCK_SUCCESS_RESPONSE = {
    "access_token": "mock_access_token",
    "token_type": "Bearer",
    "expires_in": 300,
    "refresh_token": "mock_refresh_token",
}

# Mock error response from Keycloak
MOCK_ERROR_RESPONSE = {
    "error": "invalid_grant",
    "error_description": "Invalid user credentials",
}


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to set up environment variables"""
    monkeypatch.setenv("KEYCLOAK_URL", "http://localhost:8080/auth")


@pytest.fixture
def valid_credentials():
    """Fixture for valid credentials"""
    return {"username": "testuser", "password": "testpass"}


@pytest.fixture
def invalid_credentials():
    """Fixture for invalid credentials"""
    return {"username": "wronguser", "password": "wrongpass"}


def test_signin_successful(test_client_admin, mock_env_vars, valid_credentials):
    """Test successful signin with valid credentials"""
    with patch("requests.post") as mock_post:
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        # Make request
        response = test_client_admin.post("/v1/auth/signin", json=valid_credentials)

        # Assert response
        assert response.status_code == 200  # nosec B101
        data = response.json()
        assert "access_token" in data  # nosec B101
        assert "token_type" in data  # nosec B101
        assert "expires_in" in data  # nosec B101
        assert "refresh_token" in data  # nosec B101
        assert data["token_type"] == "Bearer"  # nosec B101


def test_signin_invalid_credentials(
    test_client_admin, mock_env_vars, invalid_credentials
):
    """Test signin with invalid credentials"""
    with patch("requests.post") as mock_post:
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = MOCK_ERROR_RESPONSE
        mock_post.return_value = mock_response

        # Make request
        response = test_client_admin.post("/v1/auth/signin", json=invalid_credentials)

        # Assert response
        assert response.status_code == 401  # nosec B101
        assert "Invalid credentials" in response.json()["detail"]  # nosec B101


def test_signin_missing_credentials(test_client_admin):
    """Test signin with missing credentials"""
    # Test with missing username
    response = test_client_admin.post("/v1/auth/signin", json={"password": "testpass"})
    assert response.status_code == 422  # nosec B101

    # Test with missing password
    response = test_client_admin.post("/v1/auth/signin", json={"username": "testuser"})
    assert response.status_code == 422  # nosec B101


def test_signin_empty_credentials(test_client_admin):
    """Test signin with empty credentials"""
    print("\nTesting empty credentials:")
    response = test_client_admin.post(
        "/v1/auth/signin", json={"username": "", "password": ""}
    )
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == 422  # nosec B101


def test_signin_keycloak_server_error(
    test_client_admin, mock_env_vars, valid_credentials
):
    """Test signin when Keycloak server is down or returns 500"""
    with patch("requests.post") as mock_post:
        print("\nTesting Keycloak server error:")
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        print(f"Mock configured with status: {mock_response.status_code}")

        response = test_client_admin.post("/v1/auth/signin", json=valid_credentials)

        print(f"Actual calls to mock: {mock_post.call_args_list}")
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")

        assert response.status_code == 401  # nosec B101
        assert "Authentication failed" in response.json()["detail"]  # nosec B101


def test_signin_connection_error(test_client_admin, mock_env_vars, valid_credentials):
    """Test signin when connection to Keycloak fails"""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("Connection refused")

        # Make request
        response = test_client_admin.post("/v1/auth/signin", json=valid_credentials)

        # Assert response
        assert response.status_code == 401  # nosec B101
        assert "Authentication failed" in response.json()["detail"]  # nosec B101


def test_signin_invalid_json(test_client_admin):
    """Test signin with invalid JSON payload"""
    response = test_client_admin.post(
        "/v1/auth/signin",
        headers={"Content-Type": "application/json"},
        json={"invalid": "data"},
    )
    assert response.status_code == 422  # nosec B101


def test_signin_wrong_content_type(test_client_admin):
    """Test signin with wrong content type"""
    response = test_client_admin.post(
        "/v1/auth/signin",
        headers={"Content-Type": "text/plain"},
        data="username=test&password=test",
    )
    assert response.status_code == 422  # nosec B101


def test_signin_method_not_allowed(test_client_admin):
    """Test using wrong HTTP method"""
    response = test_client_admin.get("/v1/auth/signin")
    assert response.status_code == 405  # nosec B101


def test_signin_missing_env_var(test_client_admin):
    """Test signin when KEYCLOAK_URL environment variable is missing"""
    with patch.dict(os.environ, clear=True):
        response = test_client_admin.post(
            "/v1/auth/signin", json={"username": "testuser", "password": "testpass"}
        )
        assert response.status_code == 401  # nosec B101
        assert "Authentication failed" in response.json()["detail"]  # nosec B101
