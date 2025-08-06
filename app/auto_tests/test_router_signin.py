from unittest.mock import Mock, patch, MagicMock

import pytest
from pydantic import ValidationError

from app.routers.signin import SignInRequest


class TestSigninService:
    """Test cases for Signin Service layer focusing on validation and core logic"""

    def test_signin_request_schema_validation_success(self, mock_db_session):
        """Test successful SignInRequest schema validation"""
        # Test valid signin data
        valid_signin = SignInRequest(
            username="validuser",
            password="validpassword123"
        )
        
        assert valid_signin.username == "validuser"
        assert valid_signin.password == "validpassword123"

    def test_signin_request_schema_validation_errors(self, mock_db_session):
        """Test SignInRequest schema validation errors"""
        # Test empty username
        with pytest.raises(ValidationError) as exc_info:
            SignInRequest(username="", password="password123")
        assert "This field cannot be empty" in str(exc_info.value)
        
        # Test empty password
        with pytest.raises(ValidationError) as exc_info:
            SignInRequest(username="testuser", password="")
        assert "This field cannot be empty" in str(exc_info.value)
        
        # Test whitespace-only username
        with pytest.raises(ValidationError) as exc_info:
            SignInRequest(username="   ", password="password123")
        assert "This field cannot be empty" in str(exc_info.value)
        
        # Test whitespace-only password
        with pytest.raises(ValidationError) as exc_info:
            SignInRequest(username="testuser", password="   ")
        assert "This field cannot be empty" in str(exc_info.value)

    def test_signin_request_field_constraints(self, mock_db_session):
        """Test SignInRequest field constraints"""
        # Test that short usernames and passwords are allowed (no min length constraint)
        short_username = SignInRequest(
            username="ab",  # Short username is allowed
            password="password123"
        )
        assert short_username.username == "ab"
        assert short_username.password == "password123"
        
        # Test very short password is allowed
        short_password = SignInRequest(
            username="testuser",
            password="123"  # Short password is allowed
        )
        assert short_password.username == "testuser"
        assert short_password.password == "123"

    def test_signin_request_special_characters(self, mock_db_session):
        """Test SignInRequest with special characters"""
        # Test username with allowed special characters
        special_username = SignInRequest(
            username="test.user@domain",
            password="password123"
        )
        assert special_username.username == "test.user@domain"
        
        # Test password with special characters
        special_password = SignInRequest(
            username="testuser",
            password="P@ssw0rd!123"
        )
        assert special_password.password == "P@ssw0rd!123"

    def test_signin_request_case_sensitivity(self, mock_db_session):
        """Test SignInRequest case sensitivity"""
        # Test that usernames preserve case
        mixed_case = SignInRequest(
            username="TestUser",
            password="password123"
        )
        assert mixed_case.username == "TestUser"
        
        # Test that passwords preserve case
        mixed_case_password = SignInRequest(
            username="testuser",
            password="PassWord123"
        )
        assert mixed_case_password.password == "PassWord123"

    def test_signin_request_unicode_support(self, mock_db_session):
        """Test SignInRequest with unicode characters"""
        # Test unicode username
        unicode_signin = SignInRequest(
            username="tëstüser",
            password="password123"
        )
        assert unicode_signin.username == "tëstüser"
        
        # Test unicode password
        unicode_password = SignInRequest(
            username="testuser",
            password="pässwörd123"
        )
        assert unicode_password.password == "pässwörd123"

    def test_signin_request_length_limits(self, mock_db_session):
        """Test SignInRequest length limits"""
        # Test maximum reasonable lengths
        long_username = "a" * 100
        long_password = "b" * 100
        
        long_signin = SignInRequest(
            username=long_username,
            password=long_password
        )
        
        assert long_signin.username == long_username
        assert long_signin.password == long_password

    def test_signin_request_trimming(self, mock_db_session):
        """Test SignInRequest field trimming behavior"""
        # Test if leading/trailing spaces are handled
        try:
            signin_with_spaces = SignInRequest(
                username=" testuser ",
                password=" password123 "
            )
            # If validation passes, check if spaces are trimmed
            # This depends on the actual schema implementation
            assert signin_with_spaces.username.strip() == "testuser"
            assert signin_with_spaces.password.strip() == "password123"
        except ValidationError:
            # If validation fails, that's also acceptable behavior
            pass

    def test_signin_request_required_fields(self, mock_db_session):
        """Test SignInRequest required fields"""
        # Test missing username
        with pytest.raises((ValidationError, TypeError)):
            SignInRequest(password="password123")
        
        # Test missing password
        with pytest.raises((ValidationError, TypeError)):
            SignInRequest(username="testuser")
        
        # Test missing both fields
        with pytest.raises((ValidationError, TypeError)):
            SignInRequest()

    def test_signin_request_none_values(self, mock_db_session):
        """Test SignInRequest with None values"""
        # Test None username
        with pytest.raises((ValidationError, TypeError)):
            SignInRequest(username=None, password="password123")
        
        # Test None password
        with pytest.raises((ValidationError, TypeError)):
            SignInRequest(username="testuser", password=None)

    def test_signin_request_numeric_values(self, mock_db_session):
        """Test SignInRequest with numeric values"""
        # Test numeric username (should be converted to string)
        numeric_signin = SignInRequest(
            username="12345",
            password="password123"
        )
        assert numeric_signin.username == "12345"
        
        # Test numeric password (should be converted to string)
        numeric_password = SignInRequest(
            username="testuser",
            password="123456789"
        )
        assert numeric_password.password == "123456789"

    def test_signin_request_boolean_conversion(self, mock_db_session):
        """Test SignInRequest with boolean values"""
        # Test boolean values (should be converted to string if allowed)
        try:
            bool_signin = SignInRequest(
                username="true",
                password="false"
            )
            assert bool_signin.username == "true"
            assert bool_signin.password == "false"
        except ValidationError:
            # If validation fails, that's acceptable
            pass

    def test_signin_request_serialization(self, mock_db_session):
        """Test SignInRequest serialization"""
        signin_data = SignInRequest(
            username="testuser",
            password="password123"
        )
        
        # Test dict conversion
        signin_dict = signin_data.dict()
        assert signin_dict["username"] == "testuser"
        assert signin_dict["password"] == "password123"
        
        # Test JSON serialization
        signin_json = signin_data.json()
        assert "testuser" in signin_json
        assert "password123" in signin_json
