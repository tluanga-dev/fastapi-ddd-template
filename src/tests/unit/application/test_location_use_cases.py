import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from src.application.use_cases.location_use_cases import LocationUseCases
from src.domain.entities.location import Location, LocationType
from src.domain.repositories.location_repository import LocationRepository


class TestLocationUseCases:
    """Test Location use cases."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock location repository."""
        return AsyncMock(spec=LocationRepository)
    
    @pytest.fixture
    def use_cases(self, mock_repository):
        """Create location use cases with mock repository."""
        return LocationUseCases(mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_location_success(self, use_cases, mock_repository):
        """Test successfully creating a location."""
        # Arrange
        mock_repository.exists_by_code.return_value = False
        mock_repository.create.return_value = Location(
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        
        # Act
        result = await use_cases.create_location(
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            created_by="user123"
        )
        
        # Assert
        assert result.location_code == "LOC001"
        assert result.location_name == "Test Store"
        mock_repository.exists_by_code.assert_called_once_with("LOC001")
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_location_duplicate_code(self, use_cases, mock_repository):
        """Test creating location with existing code fails."""
        # Arrange
        mock_repository.exists_by_code.return_value = True
        
        # Act & Assert
        with pytest.raises(ValueError, match="Location with code LOC001 already exists"):
            await use_cases.create_location(
                location_code="LOC001",
                location_name="Test Store",
                location_type=LocationType.STORE,
                address="123 Main St",
                city="New York",
                state="NY",
                country="USA"
            )
        
        mock_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_location_success(self, use_cases, mock_repository):
        """Test successfully getting a location by ID."""
        # Arrange
        location_id = uuid4()
        mock_location = Location(
            id=location_id,
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        mock_repository.get_by_id.return_value = mock_location
        
        # Act
        result = await use_cases.get_location(location_id)
        
        # Assert
        assert result == mock_location
        mock_repository.get_by_id.assert_called_once_with(location_id)
    
    @pytest.mark.asyncio
    async def test_get_location_not_found(self, use_cases, mock_repository):
        """Test getting non-existent location fails."""
        # Arrange
        location_id = uuid4()
        mock_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"Location with ID {location_id} not found"):
            await use_cases.get_location(location_id)
    
    @pytest.mark.asyncio
    async def test_get_location_by_code_success(self, use_cases, mock_repository):
        """Test successfully getting a location by code."""
        # Arrange
        mock_location = Location(
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        mock_repository.get_by_code.return_value = mock_location
        
        # Act
        result = await use_cases.get_location_by_code("LOC001")
        
        # Assert
        assert result == mock_location
        mock_repository.get_by_code.assert_called_once_with("LOC001")
    
    @pytest.mark.asyncio
    async def test_list_locations(self, use_cases, mock_repository):
        """Test listing locations with pagination."""
        # Arrange
        mock_locations = [
            Location(
                location_code=f"LOC00{i}",
                location_name=f"Store {i}",
                location_type=LocationType.STORE,
                address=f"{i} Main St",
                city="New York",
                state="NY",
                country="USA"
            )
            for i in range(1, 4)
        ]
        mock_repository.list.return_value = mock_locations
        mock_repository.count.return_value = 10
        
        # Act
        locations, total = await use_cases.list_locations(
            skip=0,
            limit=3,
            location_type=LocationType.STORE,
            city="New York"
        )
        
        # Assert
        assert len(locations) == 3
        assert total == 10
        mock_repository.list.assert_called_once_with(
            skip=0,
            limit=3,
            location_type=LocationType.STORE,
            city="New York",
            state=None,
            is_active=True
        )
    
    @pytest.mark.asyncio
    async def test_update_location_details(self, use_cases, mock_repository):
        """Test updating location details."""
        # Arrange
        location_id = uuid4()
        existing_location = Location(
            id=location_id,
            location_code="LOC001",
            location_name="Old Store",
            location_type=LocationType.STORE,
            address="123 Old St",
            city="Old City",
            state="OC",
            country="USA"
        )
        mock_repository.get_by_id.return_value = existing_location
        mock_repository.update.return_value = existing_location
        
        # Act
        result = await use_cases.update_location(
            location_id=location_id,
            location_name="New Store",
            address="456 New St",
            city="New City",
            updated_by="user123"
        )
        
        # Assert
        assert result.location_name == "New Store"
        assert result.address == "456 New St"
        assert result.city == "New City"
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_location_contact_info(self, use_cases, mock_repository):
        """Test updating location contact information."""
        # Arrange
        location_id = uuid4()
        existing_location = Location(
            id=location_id,
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        mock_repository.get_by_id.return_value = existing_location
        mock_repository.update.return_value = existing_location
        
        # Act
        result = await use_cases.update_location(
            location_id=location_id,
            contact_number="+12125551234",
            email="store@example.com",
            updated_by="user123"
        )
        
        # Assert
        assert result.contact_number == "+12125551234"
        assert result.email == "store@example.com"
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_location(self, use_cases, mock_repository):
        """Test deactivating a location."""
        # Arrange
        location_id = uuid4()
        active_location = Location(
            id=location_id,
            location_code="LOC001",
            location_name="Active Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            is_active=True
        )
        mock_repository.get_by_id.return_value = active_location
        mock_repository.update.return_value = active_location
        
        # Act
        result = await use_cases.deactivate_location(location_id, updated_by="admin")
        
        # Assert
        assert result.is_active is False
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_activate_location(self, use_cases, mock_repository):
        """Test activating a location."""
        # Arrange
        location_id = uuid4()
        inactive_location = Location(
            id=location_id,
            location_code="LOC001",
            location_name="Inactive Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            is_active=False
        )
        mock_repository.get_by_id.return_value = inactive_location
        mock_repository.update.return_value = inactive_location
        
        # Act
        result = await use_cases.activate_location(location_id, updated_by="admin")
        
        # Assert
        assert result.is_active is True
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_location(self, use_cases, mock_repository):
        """Test soft deleting a location."""
        # Arrange
        location_id = uuid4()
        mock_repository.delete.return_value = True
        
        # Act
        result = await use_cases.delete_location(location_id)
        
        # Assert
        assert result is True
        mock_repository.delete.assert_called_once_with(location_id)
    
    @pytest.mark.asyncio
    async def test_get_locations_by_manager(self, use_cases, mock_repository):
        """Test getting locations by manager."""
        # Arrange
        manager_id = uuid4()
        mock_locations = [
            Location(
                location_code="LOC001",
                location_name="Store 1",
                location_type=LocationType.STORE,
                address="123 Main St",
                city="New York",
                state="NY",
                country="USA",
                manager_user_id=manager_id
            ),
            Location(
                location_code="LOC002",
                location_name="Store 2",
                location_type=LocationType.STORE,
                address="456 Broadway",
                city="New York",
                state="NY",
                country="USA",
                manager_user_id=manager_id
            )
        ]
        mock_repository.get_by_manager.return_value = mock_locations
        
        # Act
        result = await use_cases.get_locations_by_manager(manager_id)
        
        # Assert
        assert len(result) == 2
        assert all(loc.manager_user_id == manager_id for loc in result)
        mock_repository.get_by_manager.assert_called_once_with(manager_id)
    
    @pytest.mark.asyncio
    async def test_assign_manager_to_location(self, use_cases, mock_repository):
        """Test assigning a manager to a location."""
        # Arrange
        location_id = uuid4()
        manager_id = uuid4()
        location = Location(
            id=location_id,
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        mock_repository.get_by_id.return_value = location
        mock_repository.update.return_value = location
        
        # Act
        result = await use_cases.assign_manager_to_location(
            location_id,
            manager_id,
            updated_by="admin"
        )
        
        # Assert
        assert result.manager_user_id == manager_id
        mock_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_manager_from_location(self, use_cases, mock_repository):
        """Test removing manager from a location."""
        # Arrange
        location_id = uuid4()
        manager_id = uuid4()
        location = Location(
            id=location_id,
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            manager_user_id=manager_id
        )
        mock_repository.get_by_id.return_value = location
        mock_repository.update.return_value = location
        
        # Act
        result = await use_cases.remove_manager_from_location(
            location_id,
            updated_by="admin"
        )
        
        # Assert
        assert result.manager_user_id is None
        mock_repository.update.assert_called_once()