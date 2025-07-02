import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
import json

from src.domain.entities.location import LocationType
from src.infrastructure.models.location_model import LocationModel
from src.infrastructure.models.user import UserModel


class TestLocationAPI:
    """Integration tests for Location API endpoints."""
    
    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create a test user for manager assignment."""
        user = UserModel(
            id=uuid4(),
            name="Manager One",
            email="manager1@example.com",
            hashed_password="hashed",
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        return user
    
    @pytest.fixture
    async def test_location(self, db_session: AsyncSession, test_user):
        """Create a test location."""
        location = LocationModel(
            id=uuid4(),
            location_code="TEST001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA",
            postal_code="12345",
            contact_number="+12125551234",
            email="test@example.com",
            manager_user_id=test_user.id,
            is_active=True
        )
        db_session.add(location)
        await db_session.commit()
        return location
    
    @pytest.mark.asyncio
    async def test_create_location(self, async_client: AsyncClient):
        """Test creating a new location."""
        payload = {
            "location_code": "LOC001",
            "location_name": "New Store",
            "location_type": "STORE",
            "address": "456 Main St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001",
            "contact_number": "+12125551234",
            "email": "newstore@example.com"
        }
        
        response = await async_client.post("/api/v1/locations/", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["location_code"] == "LOC001"
        assert data["location_name"] == "New Store"
        assert data["location_type"] == "STORE"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_location_duplicate_code(self, async_client: AsyncClient, test_location):
        """Test creating location with duplicate code fails."""
        payload = {
            "location_code": test_location.location_code,
            "location_name": "Duplicate Store",
            "location_type": "STORE",
            "address": "789 Broadway",
            "city": "New York",
            "state": "NY",
            "country": "USA"
        }
        
        response = await async_client.post("/api/v1/locations/", json=payload)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_location_invalid_type(self, async_client: AsyncClient):
        """Test creating location with invalid type fails."""
        payload = {
            "location_code": "LOC002",
            "location_name": "Invalid Type Store",
            "location_type": "INVALID",
            "address": "123 Test St",
            "city": "Test City",
            "state": "TC",
            "country": "USA"
        }
        
        response = await async_client.post("/api/v1/locations/", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_get_location_by_id(self, async_client: AsyncClient, test_location):
        """Test getting location by ID."""
        response = await async_client.get(f"/api/v1/locations/{test_location.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_location.id)
        assert data["location_code"] == test_location.location_code
        assert data["location_name"] == test_location.location_name
    
    @pytest.mark.asyncio
    async def test_get_location_not_found(self, async_client: AsyncClient):
        """Test getting non-existent location."""
        fake_id = uuid4()
        response = await async_client.get(f"/api/v1/locations/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_location_by_code(self, async_client: AsyncClient, test_location):
        """Test getting location by code."""
        response = await async_client.get(f"/api/v1/locations/code/{test_location.location_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["location_code"] == test_location.location_code
        assert data["id"] == str(test_location.id)
    
    @pytest.mark.asyncio
    async def test_list_locations(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing locations with pagination."""
        # Create multiple locations
        for i in range(5):
            location = LocationModel(
                location_code=f"LIST{i:03d}",
                location_name=f"Store {i}",
                location_type=LocationType.STORE,
                address=f"{i} Test St",
                city="Test City",
                state="TC",
                country="USA",
                is_active=True
            )
            db_session.add(location)
        await db_session.commit()
        
        response = await async_client.get("/api/v1/locations/?skip=0&limit=3")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 3
        assert data["skip"] == 0
        assert data["limit"] == 3
    
    @pytest.mark.asyncio
    async def test_list_locations_with_filters(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing locations with type filter."""
        # Create locations with different types
        store = LocationModel(
            location_code="STORE001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Store St",
            city="New York",
            state="NY",
            country="USA"
        )
        warehouse = LocationModel(
            location_code="WARE001",
            location_name="Test Warehouse",
            location_type=LocationType.WAREHOUSE,
            address="456 Warehouse Rd",
            city="New York",
            state="NY",
            country="USA"
        )
        db_session.add_all([store, warehouse])
        await db_session.commit()
        
        # Filter by STORE type
        response = await async_client.get("/api/v1/locations/?location_type=STORE")
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["location_type"] == "STORE" for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_update_location(self, async_client: AsyncClient, test_location):
        """Test updating a location."""
        payload = {
            "location_name": "Updated Store Name",
            "address": "789 Updated St",
            "contact_number": "+19175551234"
        }
        
        response = await async_client.put(f"/api/v1/locations/{test_location.id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["location_name"] == "Updated Store Name"
        assert data["address"] == "789 Updated St"
        assert data["contact_number"] == "+19175551234"
        # Unchanged fields should remain the same
        assert data["location_code"] == test_location.location_code
        assert data["city"] == test_location.city
    
    @pytest.mark.asyncio
    async def test_deactivate_location(self, async_client: AsyncClient, test_location):
        """Test deactivating a location."""
        assert test_location.is_active is True
        
        response = await async_client.post(f"/api/v1/locations/{test_location.id}/deactivate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_activate_location(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test activating an inactive location."""
        # Create inactive location
        inactive_location = LocationModel(
            location_code="INACTIVE001",
            location_name="Inactive Store",
            location_type=LocationType.STORE,
            address="999 Inactive St",
            city="Test City",
            state="TC",
            country="USA",
            is_active=False
        )
        db_session.add(inactive_location)
        await db_session.commit()
        
        await db_session.refresh(inactive_location)
        response = await async_client.post(f"/api/v1/locations/{inactive_location.id}/activate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_delete_location(self, async_client: AsyncClient, test_location):
        """Test soft deleting a location."""
        response = await async_client.delete(f"/api/v1/locations/{test_location.id}")
        
        assert response.status_code == 204
        
        # Verify location is soft deleted (inactive)
        get_response = await async_client.get(f"/api/v1/locations/{test_location.id}")
        assert get_response.status_code == 404  # Should not find inactive locations
    
    @pytest.mark.asyncio
    async def test_assign_manager(self, async_client: AsyncClient, test_location, test_user):
        """Test assigning a manager to a location."""
        # Create another user to assign
        new_manager_id = uuid4()
        
        payload = {
            "manager_user_id": str(new_manager_id)
        }
        
        response = await async_client.post(
            f"/api/v1/locations/{test_location.id}/assign-manager",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["manager_user_id"] == str(new_manager_id)
    
    @pytest.mark.asyncio
    async def test_remove_manager(self, async_client: AsyncClient, test_location):
        """Test removing manager from a location."""
        assert test_location.manager_user_id is not None
        
        response = await async_client.post(f"/api/v1/locations/{test_location.id}/remove-manager")
        
        assert response.status_code == 200
        data = response.json()
        assert data["manager_user_id"] is None
    
    @pytest.mark.asyncio
    async def test_get_locations_by_manager(self, async_client: AsyncClient, db_session: AsyncSession, test_user):
        """Test getting all locations managed by a user."""
        # Create multiple locations for the manager
        for i in range(3):
            location = LocationModel(
                location_code=f"MANLOC{i:03d}",
                location_name=f"Manager Store {i}",
                location_type=LocationType.STORE,
                address=f"{i} Manager St",
                city="Test City",
                state="TC",
                country="USA",
                manager_user_id=test_user.id,
                is_active=True
            )
            db_session.add(location)
        await db_session.commit()
        
        response = await async_client.get(f"/api/v1/locations/manager/{test_user.id}/locations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least the 3 we created
        assert all(loc["manager_user_id"] == str(test_user.id) for loc in data)
    
    @pytest.mark.asyncio
    async def test_create_location_minimal_fields(self, async_client: AsyncClient):
        """Test creating location with only required fields."""
        payload = {
            "location_code": "MIN001",
            "location_name": "Minimal Store",
            "location_type": "WAREHOUSE",
            "address": "123 Min St",
            "city": "Min City",
            "state": "MC",
            "country": "USA"
        }
        
        response = await async_client.post("/api/v1/locations/", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["location_code"] == "MIN001"
        assert data["postal_code"] is None
        assert data["contact_number"] is None
        assert data["email"] is None
        assert data["manager_user_id"] is None