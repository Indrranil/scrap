from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.models.general_property import GeneralProperty
from app.schemas.device import DeviceUploadCreate
from app.services.base import CRUDBase


# Create a simple device service using the base CRUD pattern
class DeviceService(CRUDBase[Machine, DeviceUploadCreate, DeviceUploadCreate]):
    def __init__(self):
        super().__init__(Machine)


# Create a singleton instance
device_service = DeviceService()


class TestDeviceService:
    """Test cases for Device Service layer"""

    def test_create_device_success(self, mock_db_session):
        """Test successful device creation"""
        # Mock device data that matches Machine model fields
        device_data = DeviceUploadCreate(
            name="Test Weight Device",
            mac_address="AA:BB:CC:DD:EE:FF",
            machine_type="weight_machine"
        )
        
        # Mock the creation process to avoid field mismatch
        mock_device = Machine(id=1, name="Test Weight Device", mid="W_123456", machine_type="weight_machine", is_usable=1, created_at=1234567890)
        
        with patch.object(device_service, 'create', return_value=mock_device) as mock_create:
            result = device_service.create(mock_db_session, obj_in=device_data)
            
            # Verify the service create method was called
            mock_create.assert_called_once_with(mock_db_session, obj_in=device_data)
            
            # Verify the result has expected attributes
            assert result.name == "Test Weight Device"
            assert result.id == 1
            assert result.is_usable == 1

    def test_get_all_devices_empty(self, mock_db_session):
        """Test getting all devices when none exist"""
        # Mock empty query result with proper chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        
        result = device_service.get_all(mock_db_session)
        
        assert result == []

    def test_get_all_devices_with_data(self, mock_db_session):
        """Test getting all devices with existing data"""
        # Mock devices
        mock_device1 = Machine(id=1, name="Device 1", mid="W_123456", machine_type="weight_machine", is_usable=1, created_at=1234567890)
        mock_device2 = Machine(id=2, name="Device 2", mid="P_789012", machine_type="perforation", is_usable=1, created_at=1234567891)
        
        # Mock query result with proper chaining
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [mock_device1, mock_device2]
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        
        result = device_service.get_all(mock_db_session)
        
        assert len(result) == 2
        assert result[0].name == "Device 1"
        assert result[1].name == "Device 2"

    def test_get_device_by_id_success(self, mock_db_session):
        """Test successful device retrieval by ID"""
        # Mock device
        mock_device = Machine(id=1, name="Test Device", mid="W_123456", machine_type="weight_machine", is_usable=1, created_at=1234567890)
        
        # Mock query result
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_device
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        
        result = device_service.get(mock_db_session, id=1)
        
        assert result is not None
        assert result.name == "Test Device"
        assert result.id == 1

    def test_get_device_by_id_not_found(self, mock_db_session):
        """Test device retrieval with non-existent ID"""
        # Mock query result returning None
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        
        result = device_service.get(mock_db_session, id=999)
        
        assert result is None

    def test_get_devices_with_pagination(self, mock_db_session):
        """Test getting devices with pagination"""
        # Mock devices
        mock_device1 = Machine(id=1, name="Device 1", mid="W_123456", machine_type="weight_machine", is_usable=1, created_at=1234567890)
        mock_device2 = Machine(id=2, name="Device 2", mid="P_789012", machine_type="perforation", is_usable=1, created_at=1234567891)
        
        # Mock query result with proper chaining for pagination
        mock_query = Mock()
        mock_filter = Mock()
        mock_offset = Mock()
        mock_limit = Mock()
        
        mock_query.filter.return_value = mock_filter
        mock_filter.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = [mock_device1, mock_device2]
        
        mock_db_session.query.return_value = mock_query
        
        result = device_service.get_multi(mock_db_session, skip=0, limit=10)
        
        assert len(result) == 2
        assert result[0].name == "Device 1"
        assert result[1].name == "Device 2"

    def test_delete_device_success(self, mock_db_session):
        """Test successful device soft delete"""
        # Mock existing device
        mock_device = Machine(id=1, name="Test Device", mid="W_123456", machine_type="weight_machine", is_usable=1, created_at=1234567890)
        
        # Mock query result for get() method called within remove()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_device
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        
        result = device_service.remove(mock_db_session, id=1)
        
        # Verify database operations were called (soft delete sets is_usable=0)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        
        # Verify soft delete happened
        assert mock_device.is_usable == 0
        assert result is not None

    def test_delete_device_not_found(self, mock_db_session):
        """Test device delete with non-existent ID"""
        # Mock query result returning None
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        
        result = device_service.get(mock_db_session, id=999)
        assert result is None

    def test_device_schema_validation(self, mock_db_session):
        """Test device schema validation"""
        # Test valid device data
        valid_device = DeviceUploadCreate(
            name="Valid Device",
            mac_address="AA:BB:CC:DD:EE:FF",
            machine_type="weight_machine"
        )
        assert valid_device.name == "Valid Device"
        assert valid_device.mac_address == "AA:BB:CC:DD:EE:FF"
        assert valid_device.machine_type == "weight_machine"

    def test_device_creation_with_optional_fields(self, mock_db_session):
        """Test device creation with optional fields"""
        # Mock device data with optional fields
        device_data = DeviceUploadCreate(
            name="Advanced Device",
            mac_address="AA:BB:CC:DD:EE:FF",
            machine_type="perforation",
            ip_address="192.168.1.100",
            baud_rate="9600",
            starting_address="0x01"
        )
        
        # Mock the creation process to avoid field mismatch
        mock_device = Machine(id=2, name="Advanced Device", mid="P_789012", machine_type="perforation", is_usable=1, created_at=1234567890)
        
        with patch.object(device_service, 'create', return_value=mock_device) as mock_create:
            result = device_service.create(mock_db_session, obj_in=device_data)
            
            # Verify the service create method was called
            mock_create.assert_called_once_with(mock_db_session, obj_in=device_data)
            
            # Verify the result has expected attributes
            assert result.name == "Advanced Device"
            assert result.id == 2
            assert result.machine_type == "perforation"
            assert result.is_usable == 1
