import pytest
from uuid import UUID
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.domain.entities.brand import Brand
from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository


@pytest.mark.integration
class TestBrandAPI:
    """Integration tests for Brand API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_brand(self, async_client: AsyncClient):
        """Test creating a new brand."""
        brand_data = {
            "brand_name": "Nike",
            "brand_code": "NIKE-001",
            "description": "Athletic footwear and apparel"
        }
        
        response = await async_client.post("/api/v1/brands/", json=brand_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["brand_name"] == "Nike"
        assert data["brand_code"] == "NIKE-001"
        assert data["description"] == "Athletic footwear and apparel"
        assert data["is_active"] is True
        assert "id" in data
        assert UUID(data["id"])  # Validate UUID format
    
    @pytest.mark.asyncio
    async def test_create_brand_minimal(self, async_client: AsyncClient):
        """Test creating a brand with minimal data."""
        brand_data = {
            "brand_name": "Adidas"
        }
        
        response = await async_client.post("/api/v1/brands/", json=brand_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["brand_name"] == "Adidas"
        assert data["brand_code"] is None
        assert data["description"] is None
    
    @pytest.mark.asyncio
    async def test_create_brand_duplicate_name(self, async_client: AsyncClient):
        """Test creating a brand with duplicate name fails."""
        # Create first brand
        brand_data = {"brand_name": "Nike"}
        response = await async_client.post("/api/v1/brands/", json=brand_data)
        assert response.status_code == 201
        
        # Try to create duplicate
        response = await async_client.post("/api/v1/brands/", json=brand_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_brand_duplicate_code(self, async_client: AsyncClient):
        """Test creating a brand with duplicate code fails."""
        # Create first brand
        brand_data = {"brand_name": "Nike", "brand_code": "NIKE-001"}
        response = await async_client.post("/api/v1/brands/", json=brand_data)
        assert response.status_code == 201
        
        # Try to create duplicate code
        brand_data2 = {"brand_name": "Nike Inc", "brand_code": "NIKE-001"}
        response = await async_client.post("/api/v1/brands/", json=brand_data2)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_brand_invalid_data(self, async_client: AsyncClient):
        """Test creating a brand with invalid data."""
        # Empty name
        response = await async_client.post("/api/v1/brands/", json={"brand_name": ""})
        assert response.status_code == 422
        
        # Invalid code format
        response = await async_client.post("/api/v1/brands/", json={
            "brand_name": "Nike",
            "brand_code": "NIKE@001"
        })
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_brand_by_id(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting a brand by ID."""
        # Create brand
        brand = Brand(brand_name="Nike", brand_code="NIKE-001")
        repo = SQLAlchemyBrandRepository(db_session)
        created_brand = await repo.create(brand)
        
        # Get by ID
        response = await async_client.get(f"/api/v1/brands/{created_brand.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(created_brand.id)
        assert data["brand_name"] == "Nike"
        assert data["brand_code"] == "NIKE-001"
    
    @pytest.mark.asyncio
    async def test_get_brand_not_found(self, async_client: AsyncClient):
        """Test getting non-existent brand returns 404."""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await async_client.get(f"/api/v1/brands/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_brand_by_name(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting a brand by name."""
        # Create brand
        brand = Brand(brand_name="Nike Sports")
        repo = SQLAlchemyBrandRepository(db_session)
        await repo.create(brand)
        
        # Get by name
        response = await async_client.get("/api/v1/brands/by-name/Nike Sports")
        
        assert response.status_code == 200
        data = response.json()
        assert data["brand_name"] == "Nike Sports"
    
    @pytest.mark.asyncio
    async def test_get_brand_by_code(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting a brand by code."""
        # Create brand
        brand = Brand(brand_name="Nike", brand_code="NIKE-001")
        repo = SQLAlchemyBrandRepository(db_session)
        await repo.create(brand)
        
        # Get by code (case-insensitive)
        response = await async_client.get("/api/v1/brands/by-code/nike-001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["brand_code"] == "NIKE-001"
    
    @pytest.mark.asyncio
    async def test_list_brands(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing brands with pagination."""
        # Create multiple brands
        repo = SQLAlchemyBrandRepository(db_session)
        brands = [
            Brand(brand_name="Nike", brand_code="NIKE"),
            Brand(brand_name="Adidas", brand_code="ADIDAS"),
            Brand(brand_name="Puma", brand_code="PUMA"),
            Brand(brand_name="Reebok", brand_code="REEBOK"),
            Brand(brand_name="Under Armour", brand_code="UA")
        ]
        
        for brand in brands:
            await repo.create(brand)
        
        # List all brands
        response = await async_client.get("/api/v1/brands/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        assert len(data["items"]) >= 5
        assert data["skip"] == 0
        assert data["limit"] == 100
        
        # Test pagination
        response = await async_client.get("/api/v1/brands/?skip=2&limit=2")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2
    
    @pytest.mark.asyncio
    async def test_list_brands_with_search(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing brands with search."""
        # Create brands
        repo = SQLAlchemyBrandRepository(db_session)
        brands = [
            Brand(brand_name="Nike Sports", description="Athletic gear"),
            Brand(brand_name="Nike Pro", description="Professional equipment"),
            Brand(brand_name="Adidas", description="Sports apparel")
        ]
        
        for brand in brands:
            await repo.create(brand)
        
        # Search for "Nike"
        response = await async_client.get("/api/v1/brands/?search=Nike")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all("Nike" in item["brand_name"] for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_list_brands_inactive(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing inactive brands."""
        # Create brands
        repo = SQLAlchemyBrandRepository(db_session)
        active_brand = Brand(brand_name="Active Brand")
        inactive_brand = Brand(brand_name="Inactive Brand", is_active=False)
        
        await repo.create(active_brand)
        await repo.create(inactive_brand)
        
        # List only active brands (default)
        response = await async_client.get("/api/v1/brands/")
        data = response.json()
        assert all(item["is_active"] for item in data["items"])
        
        # List only inactive brands
        response = await async_client.get("/api/v1/brands/?is_active=false")
        data = response.json()
        assert all(not item["is_active"] for item in data["items"])
        
        # List all brands (no is_active filter)
        # When is_active is None, it still defaults to True in the endpoint
        # So we just verify that the active brand is listed
        response = await async_client.get("/api/v1/brands/")
        data = response.json()
        assert data["total"] >= 1
        assert any(item["brand_name"] == "Active Brand" for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_update_brand(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test updating a brand."""
        # Create brand
        brand = Brand(brand_name="Nike", brand_code="NIKE-001")
        repo = SQLAlchemyBrandRepository(db_session)
        created_brand = await repo.create(brand)
        
        # Update brand
        update_data = {
            "brand_name": "Nike Inc.",
            "brand_code": "NIKE-002",
            "description": "Updated description"
        }
        
        response = await async_client.put(
            f"/api/v1/brands/{created_brand.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["brand_name"] == "Nike Inc."
        assert data["brand_code"] == "NIKE-002"
        assert data["description"] == "Updated description"
    
    @pytest.mark.asyncio
    async def test_update_brand_partial(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test partial update of a brand."""
        # Create brand
        brand = Brand(
            brand_name="Nike",
            brand_code="NIKE-001",
            description="Original description"
        )
        repo = SQLAlchemyBrandRepository(db_session)
        created_brand = await repo.create(brand)
        
        # Update only name
        update_data = {"brand_name": "Nike Corporation"}
        
        response = await async_client.put(
            f"/api/v1/brands/{created_brand.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["brand_name"] == "Nike Corporation"
        assert data["brand_code"] == "NIKE-001"  # Unchanged
        assert data["description"] == "Original description"  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_brand_duplicate_name(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test updating brand with duplicate name fails."""
        # Create two brands
        repo = SQLAlchemyBrandRepository(db_session)
        brand1 = await repo.create(Brand(brand_name="Nike"))
        brand2 = await repo.create(Brand(brand_name="Adidas"))
        
        # Try to update brand2 with brand1's name
        update_data = {"brand_name": "Nike"}
        
        response = await async_client.put(
            f"/api/v1/brands/{brand2.id}",
            json=update_data
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_delete_brand(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test deleting (deactivating) a brand."""
        # Create brand
        brand = Brand(brand_name="Nike")
        repo = SQLAlchemyBrandRepository(db_session)
        created_brand = await repo.create(brand)
        
        # Delete brand
        response = await async_client.delete(f"/api/v1/brands/{created_brand.id}")
        
        assert response.status_code == 204
        
        # Verify brand is deactivated
        deactivated_brand = await repo.get_by_id(created_brand.id)
        assert deactivated_brand.is_active is False
    
    @pytest.mark.asyncio
    async def test_delete_brand_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent brand returns 404."""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await async_client.delete(f"/api/v1/brands/{fake_id}")
        
        assert response.status_code == 404