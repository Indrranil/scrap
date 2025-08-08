from unittest.mock import Mock, patch, MagicMock

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserUpdate, UserResponse


class TestUsersService:
    """Test cases for Users Service layer focusing on validation and core logic"""

    def test_user_create_schema_validation_success(self, mock_db_session):
        """Test successful UserCreate schema validation"""
        # Test valid user data
        valid_user = UserCreate(
            username="validuser",
            email="valid@example.com",
            firstName="Valid",
            lastName="User",
            password="validpassword123",
            roles=["app_user"]
        )
        
        assert valid_user.username == "validuser"
        assert valid_user.email == "valid@example.com"
        assert valid_user.firstName == "Valid"
        assert valid_user.lastName == "User"
        assert valid_user.password == "validpassword123"
        assert valid_user.roles == ["app_user"]

    def test_user_create_schema_validation_errors(self, mock_db_session):
        """Test UserCreate schema validation errors"""
        # Test invalid email
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="invalid-email",
                firstName="Test",
                lastName="User",
                password="password123"
            )
        
        # Test short username
        with pytest.raises(ValidationError):
            UserCreate(
                username="ab",  # Too short (min 3)
                email="test@example.com",
                firstName="Test",
                lastName="User",
                password="password123"
            )
        
        # Test short password
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                firstName="Test",
                lastName="User",
                password="short"  # Too short (min 8)
            )
        
        # Test short firstName
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                firstName="T",  # Too short (min 2)
                lastName="User",
                password="password123"
            )

    def test_user_update_schema_validation(self, mock_db_session):
        """Test UserUpdate schema validation"""
        # Test valid partial update
        valid_update = UserUpdate(
            firstName="Updated",
            lastName="Name"
        )
        
        assert valid_update.firstName == "Updated"
        assert valid_update.lastName == "Name"
        assert valid_update.username is None  # Optional field
        assert valid_update.email is None  # Optional field
        assert valid_update.password is None  # Optional field

    def test_user_response_schema(self, mock_db_session):
        """Test UserResponse schema"""
        # Test valid user response
        user_response = UserResponse(
            id="user-123",
            username="testuser",
            firstName="Test",
            lastName="User",
            email="test@example.com",
            enabled=True
        )
        
        assert user_response.id == "user-123"
        assert user_response.username == "testuser"
        assert user_response.firstName == "Test"
        assert user_response.lastName == "User"
        assert user_response.email == "test@example.com"
        assert user_response.enabled is True

    def test_user_create_with_optional_roles(self, mock_db_session):
        """Test UserCreate with optional roles field"""
        # Test with roles
        user_with_roles = UserCreate(
            username="testuser",
            email="test@example.com",
            firstName="Test",
            lastName="User",
            password="password123",
            roles=["admin", "user"]
        )
        
        assert user_with_roles.roles == ["admin", "user"]
        
        # Test without roles (should default to empty list)
        user_without_roles = UserCreate(
            username="testuser2",
            email="test2@example.com",
            firstName="Test",
            lastName="User",
            password="password123"
        )
        
        assert user_without_roles.roles == []

    def test_user_create_field_constraints(self, mock_db_session):
        """Test UserCreate field constraints"""
        # Test maximum length constraints
        with pytest.raises(ValidationError):
            UserCreate(
                username="a" * 51,  # Too long (max 50)
                email="test@example.com",
                firstName="Test",
                lastName="User",
                password="password123"
            )
        
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                firstName="a" * 51,  # Too long (max 50)
                lastName="User",
                password="password123"
            )

    def test_user_update_optional_fields(self, mock_db_session):
        """Test UserUpdate with various optional field combinations"""
        # Test updating only username
        update_username = UserUpdate(username="newusername")
        assert update_username.username == "newusername"
        assert update_username.email is None
        
        # Test updating only email
        update_email = UserUpdate(email="new@example.com")
        assert update_email.email == "new@example.com"
        assert update_email.username is None
        
        # Test updating multiple fields
        update_multiple = UserUpdate(
            firstName="New",
            lastName="Name",
            email="updated@example.com"
        )
        assert update_multiple.firstName == "New"
        assert update_multiple.lastName == "Name"
        assert update_multiple.email == "updated@example.com"
        assert update_multiple.username is None

    def test_user_response_optional_fields(self, mock_db_session):
        """Test UserResponse with optional fields"""
        # Test with minimal required fields
        minimal_response = UserResponse(
            id="user-123",
            username="testuser"
        )
        
        assert minimal_response.id == "user-123"
        assert minimal_response.username == "testuser"
        assert minimal_response.firstName == ""  # Default value
        assert minimal_response.lastName == ""  # Default value
        assert minimal_response.email == ""  # Default value
        assert minimal_response.enabled is True  # Default value

    def test_user_email_validation(self, mock_db_session):
        """Test email validation in UserCreate"""
        # Test various invalid email formats
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            ""
        ]
        
        for invalid_email in invalid_emails:
            with pytest.raises(ValidationError):
                UserCreate(
                    username="testuser",
                    email=invalid_email,
                    firstName="Test",
                    lastName="User",
                    password="password123"
                )
        
        # Test valid email formats
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org",
            "123@example.com"
        ]
        
        for valid_email in valid_emails:
            user = UserCreate(
                username="testuser",
                email=valid_email,
                firstName="Test",
                lastName="User",
                password="password123"
            )
            assert user.email == valid_email

    def test_user_roles_list_validation(self, mock_db_session):
        """Test roles list validation"""
        # Test with valid roles list
        user_with_roles = UserCreate(
            username="testuser",
            email="test@example.com",
            firstName="Test",
            lastName="User",
            password="password123",
            roles=["admin", "user", "moderator"]
        )
        
        assert len(user_with_roles.roles) == 3
        assert "admin" in user_with_roles.roles
        assert "user" in user_with_roles.roles
        assert "moderator" in user_with_roles.roles
        
        # Test with empty roles list
        user_empty_roles = UserCreate(
            username="testuser",
            email="test@example.com",
            firstName="Test",
            lastName="User",
            password="password123",
            roles=[]
        )
        
        assert user_empty_roles.roles == []
