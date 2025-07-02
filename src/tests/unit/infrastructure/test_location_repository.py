import pytest
from unittest.mock import MagicMock, Mock
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from src.infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
from src.infrastructure.models.location_model import LocationModel
from src.domain.entities.location import Location, LocationType


class TestLocationRepository:
    """Test SQLAlchemy Location Repository implementation."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock(spec=Session)
        # Mock query chain
        session.query.return_value.filter.return_value.first.return_value = None
        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
        session.query.return_value.filter.return_value.count.return_value = 0
        return session
    
    @pytest.fixture
    def repository(self, mock_db_session):
        """Create repository with mock session."""
        return SQLAlchemyLocationRepository(mock_db_session)
    
    def create_mock_location_model(self, **kwargs):
        """Helper to create a mock LocationModel."""
        model = MagicMock(spec=LocationModel)
        model.id = kwargs.get('id', uuid4())
        model.location_code = kwargs.get('location_code', 'LOC001')
        model.location_name = kwargs.get('location_name', 'Test Store')
        model.location_type = kwargs.get('location_type', LocationType.STORE)
        model.address = kwargs.get('address', '123 Main St')
        model.city = kwargs.get('city', 'New York')
        model.state = kwargs.get('state', 'NY')
        model.country = kwargs.get('country', 'USA')
        model.postal_code = kwargs.get('postal_code', None)
        model.contact_number = kwargs.get('contact_number', None)
        model.email = kwargs.get('email', None)
        model.manager_user_id = kwargs.get('manager_user_id', None)
        model.created_at = kwargs.get('created_at', datetime.utcnow())
        model.updated_at = kwargs.get('updated_at', datetime.utcnow())
        model.created_by = kwargs.get('created_by', None)
        model.updated_by = kwargs.get('updated_by', None)
        model.is_active = kwargs.get('is_active', True)
        
        # Mock to_entity method
        model.to_entity.return_value = Location(
            id=model.id,
            location_code=model.location_code,
            location_name=model.location_name,
            location_type=model.location_type,
            address=model.address,
            city=model.city,
            state=model.state,
            country=model.country,
            postal_code=model.postal_code,
            contact_number=model.contact_number,
            email=model.email,
            manager_user_id=model.manager_user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            is_active=model.is_active
        )
        
        return model
    
    @pytest.mark.asyncio
    async def test_create_location(self, repository, mock_db_session):
        """Test creating a new location."""
        # Arrange
        location = Location(
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        
        mock_model = self.create_mock_location_model()
        LocationModel.from_entity = MagicMock(return_value=mock_model)
        
        # Act
        result = await repository.create(location)
        
        # Assert
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result.location_code == "LOC001"
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_db_session):
        """Test getting location by ID when found."""
        # Arrange
        location_id = uuid4()
        mock_model = self.create_mock_location_model(id=location_id)
        
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_model
        
        # Act
        result = await repository.get_by_id(location_id)
        
        # Assert
        assert result is not None
        assert result.id == location_id
        mock_query.filter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_db_session):
        """Test getting location by ID when not found."""
        # Arrange
        location_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = await repository.get_by_id(location_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_code_found(self, repository, mock_db_session):
        """Test getting location by code when found."""
        # Arrange
        mock_model = self.create_mock_location_model(location_code="LOC001")
        
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_model
        
        # Act
        result = await repository.get_by_code("LOC001")
        
        # Assert
        assert result is not None
        assert result.location_code == "LOC001"
    
    @pytest.mark.asyncio
    async def test_list_with_filters(self, repository, mock_db_session):
        """Test listing locations with filters."""
        # Arrange
        mock_models = [
            self.create_mock_location_model(location_code=f"LOC00{i}")
            for i in range(1, 4)
        ]
        
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_models
        
        # Act
        result = await repository.list(
            skip=0,
            limit=10,
            location_type=LocationType.STORE,
            city="New York",
            state="NY",
            is_active=True
        )
        
        # Assert
        assert len(result) == 3
        mock_query.filter.assert_called()
        mock_query.offset.assert_called_with(0)
        mock_query.limit.assert_called_with(10)
    
    @pytest.mark.asyncio
    async def test_update_location(self, repository, mock_db_session):
        """Test updating an existing location."""
        # Arrange
        location_id = uuid4()
        location = Location(
            id=location_id,
            location_code="LOC001",
            location_name="Updated Store",
            location_type=LocationType.STORE,
            address="456 New St",
            city="New York",
            state="NY",
            country="USA"
        )
        
        mock_model = self.create_mock_location_model(id=location_id)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_model
        
        # Act
        result = await repository.update(location)
        
        # Assert
        assert mock_model.location_name == "Updated Store"
        assert mock_model.address == "456 New St"
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_location_not_found(self, repository, mock_db_session):
        """Test updating non-existent location fails."""
        # Arrange
        location = Location(
            id=uuid4(),
            location_code="LOC001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Location with ID .* not found"):
            await repository.update(location)
    
    @pytest.mark.asyncio
    async def test_delete_location(self, repository, mock_db_session):
        """Test soft deleting a location."""
        # Arrange
        location_id = uuid4()
        mock_model = self.create_mock_location_model(id=location_id)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_model
        
        # Act
        result = await repository.delete(location_id)
        
        # Assert
        assert result is True
        assert mock_model.is_active is False
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_location_not_found(self, repository, mock_db_session):
        """Test deleting non-existent location returns False."""
        # Arrange
        location_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = await repository.delete(location_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_count_with_filters(self, repository, mock_db_session):
        """Test counting locations with filters."""
        # Arrange
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        
        # Act
        result = await repository.count(
            location_type=LocationType.STORE,
            city="New York"
        )
        
        # Assert
        assert result == 5
        mock_query.filter.assert_called()
        mock_query.count.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_manager(self, repository, mock_db_session):
        """Test getting locations by manager."""
        # Arrange
        manager_id = uuid4()
        mock_models = [
            self.create_mock_location_model(manager_user_id=manager_id)
            for _ in range(2)
        ]
        
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_models
        
        # Act
        result = await repository.get_by_manager(manager_id)
        
        # Assert
        assert len(result) == 2
        mock_query.filter.assert_called()
    
    @pytest.mark.asyncio
    async def test_exists_by_code_true(self, repository, mock_db_session):
        """Test checking if location exists by code - exists."""
        # Arrange
        mock_model = self.create_mock_location_model()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_model
        
        # Act
        result = await repository.exists_by_code("LOC001")
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_by_code_false(self, repository, mock_db_session):
        """Test checking if location exists by code - doesn't exist."""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = await repository.exists_by_code("LOC999")
        
        # Assert
        assert result is False