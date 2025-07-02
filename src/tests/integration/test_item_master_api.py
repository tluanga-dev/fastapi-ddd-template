import pytest
from uuid import UUID, uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.item_master import ItemMaster
from src.domain.entities.category import Category
from src.domain.entities.brand import Brand
from src.domain.value_objects.item_type import ItemType
from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
from src.infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository


@pytest.mark.integration
class TestItemMasterAPI:
    """Integration tests for Item Master API endpoints."""
    
    @pytest.fixture
    async def setup_data(self, db_session: AsyncSession):
        """Set up test data."""
        # Create category
        category_repo = SQLAlchemyCategoryRepository(db_session)
        category = Category(
            category_name="Electronics",
            category_path="Electronics",
            category_level=1
        )
        created_category = await category_repo.create(category)
        
        # Create brand
        brand_repo = SQLAlchemyBrandRepository(db_session)
        brand = Brand(
            brand_name="TestBrand",
            brand_code="TB001"
        )
        created_brand = await brand_repo.create(brand)
        
        return created_category, created_brand
    
    @pytest.mark.asyncio
    async def test_create_item_master(self, async_client: AsyncClient, setup_data):
        """Test creating an item master."""
        category, brand = setup_data
        
        item_data = {
            "item_code": "ITEM001",
            "item_name": "Test Item",
            "category_id": str(category.id),
            "brand_id": str(brand.id),
            "item_type": "PRODUCT",
            "description": "Test item description",
            "is_serialized": True
        }
        
        response = await async_client.post("/api/v1/item-masters/", json=item_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["item_code"] == "ITEM001"
        assert data["item_name"] == "Test Item"
        assert data["category_id"] == str(category.id)
        assert data["brand_id"] == str(brand.id)
        assert data["item_type"] == "PRODUCT"
        assert data["description"] == "Test item description"
        assert data["is_serialized"] is True
        assert data["is_active"] is True
        assert "id" in data
        assert UUID(data["id"])  # Validate UUID format
    
    @pytest.mark.asyncio
    async def test_create_service_item(self, async_client: AsyncClient, setup_data):
        """Test creating a service item."""
        category, _ = await setup_data
        
        item_data = {
            "item_code": "SVC001",
            "item_name": "Test Service",
            "category_id": str(category.id),
            "item_type": "SERVICE",
            "is_serialized": False
        }
        
        response = await async_client.post("/api/v1/item-masters/", json=item_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["item_type"] == "SERVICE"
        assert data["is_serialized"] is False
    
    @pytest.mark.asyncio
    async def test_create_item_duplicate_code(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test creating item with duplicate code fails."""
        category, _ = await setup_data
        
        # Create first item
        repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="ITEM001",
            item_name="First Item",
            category_id=category.id
        )
        await repo.create(item)
        
        # Try to create duplicate
        item_data = {
            "item_code": "ITEM001",
            "item_name": "Duplicate Item",
            "category_id": str(category.id)
        }
        
        response = await async_client.post("/api/v1/item-masters/", json=item_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_bundle_serialized_fails(self, async_client: AsyncClient, setup_data):
        """Test creating serialized bundle fails."""
        category, _ = await setup_data
        
        item_data = {
            "item_code": "BUNDLE001",
            "item_name": "Test Bundle",
            "category_id": str(category.id),
            "item_type": "BUNDLE",
            "is_serialized": True
        }
        
        response = await async_client.post("/api/v1/item-masters/", json=item_data)
        assert response.status_code == 400
        assert "Bundle items cannot be serialized" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_item_master_by_id(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting item master by ID."""
        category, _ = await setup_data
        
        # Create item
        repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=category.id
        )
        created_item = await repo.create(item)
        
        # Get by ID
        response = await async_client.get(f"/api/v1/item-masters/{created_item.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(created_item.id)
        assert data["item_code"] == "ITEM001"
        assert data["item_name"] == "Test Item"
    
    @pytest.mark.asyncio
    async def test_get_item_not_found(self, async_client: AsyncClient):
        """Test getting non-existent item returns 404."""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await async_client.get(f"/api/v1/item-masters/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_item_by_code(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting item by code."""
        category, _ = await setup_data
        
        # Create item
        repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=category.id
        )
        await repo.create(item)
        
        # Get by code
        response = await async_client.get("/api/v1/item-masters/code/ITEM001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_code"] == "ITEM001"
        assert data["item_name"] == "Test Item"
    
    @pytest.mark.asyncio
    async def test_list_items(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test listing items with pagination."""
        category, brand = setup_data
        
        # Create multiple items
        repo = SQLAlchemyItemMasterRepository(db_session)
        for i in range(5):
            item = ItemMaster(
                item_code=f"ITEM{i:03d}",
                item_name=f"Item {i}",
                category_id=category.id,
                brand_id=brand.id if i < 3 else None
            )
            await repo.create(item)
        
        # List all items
        response = await async_client.get("/api/v1/item-masters/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        assert len(data["items"]) >= 5
        assert data["skip"] == 0
        assert data["limit"] == 100
        
        # Test pagination
        response = await async_client.get("/api/v1/item-masters/?skip=2&limit=2")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2
    
    @pytest.mark.asyncio
    async def test_list_items_with_filters(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test listing items with filters."""
        category, brand = setup_data
        
        # Create items
        repo = SQLAlchemyItemMasterRepository(db_session)
        
        product = ItemMaster(
            item_code="PROD001",
            item_name="Product Item",
            category_id=category.id,
            brand_id=brand.id,
            item_type=ItemType.PRODUCT,
            is_serialized=True
        )
        
        service = ItemMaster(
            item_code="SVC001",
            item_name="Service Item",
            category_id=category.id,
            item_type=ItemType.SERVICE
        )
        
        await repo.create(product)
        await repo.create(service)
        
        # Filter by item type
        response = await async_client.get("/api/v1/item-masters/?item_type=SERVICE")
        data = response.json()
        assert all(item["item_type"] == "SERVICE" for item in data["items"])
        
        # Filter by serialization
        response = await async_client.get("/api/v1/item-masters/?is_serialized=true")
        data = response.json()
        assert all(item["is_serialized"] is True for item in data["items"])
        
        # Filter by brand
        response = await async_client.get(f"/api/v1/item-masters/?brand_id={brand.id}")
        data = response.json()
        assert all(item["brand_id"] == str(brand.id) for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_search_items(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test searching items."""
        category, _ = await setup_data
        
        # Create items
        repo = SQLAlchemyItemMasterRepository(db_session)
        
        items = [
            ItemMaster(
                item_code="LAPTOP001",
                item_name="Dell Laptop",
                category_id=category.id,
                description="High-performance laptop"
            ),
            ItemMaster(
                item_code="DESKTOP001",
                item_name="HP Desktop",
                category_id=category.id,
                description="Business desktop computer"
            ),
            ItemMaster(
                item_code="TABLET001",
                item_name="iPad Pro",
                category_id=category.id,
                description="Professional tablet"
            )
        ]
        
        for item in items:
            await repo.create(item)
        
        # Search for "laptop"
        response = await async_client.get("/api/v1/item-masters/?search=laptop")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("laptop" in item["item_name"].lower() or 
                  "laptop" in item["description"].lower() 
                  for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_update_item_master(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test updating item master."""
        category, brand = setup_data
        
        # Create item
        repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Original Name",
            category_id=category.id
        )
        created_item = await repo.create(item)
        
        # Update item
        update_data = {
            "item_name": "Updated Name",
            "description": "Updated description",
            "brand_id": str(brand.id)
        }
        
        response = await async_client.put(
            f"/api/v1/item-masters/{created_item.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_name"] == "Updated Name"
        assert data["description"] == "Updated description"
        assert data["brand_id"] == str(brand.id)
    
    @pytest.mark.asyncio
    async def test_update_item_serialization(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test updating item serialization settings."""
        category, _ = await setup_data
        
        # Create non-serialized item
        repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=category.id,
            is_serialized=False
        )
        created_item = await repo.create(item)
        
        # Enable serialization
        response = await async_client.put(
            f"/api/v1/item-masters/{created_item.id}/serialization",
            json={"enable": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_serialized"] is True
        
        # Disable serialization
        response = await async_client.put(
            f"/api/v1/item-masters/{created_item.id}/serialization",
            json={"enable": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_serialized"] is False
    
    @pytest.mark.asyncio
    async def test_delete_item_master(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test soft deleting an item master."""
        category, _ = await setup_data
        
        # Create item
        repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="DELETE001",
            item_name="Delete Me",
            category_id=category.id
        )
        created_item = await repo.create(item)
        
        # Delete item
        response = await async_client.delete(f"/api/v1/item-masters/{created_item.id}")
        
        assert response.status_code == 204
        
        # Verify item is soft deleted
        deleted_item = await repo.get_by_id(created_item.id)
        assert deleted_item.is_active is False
    
    @pytest.mark.asyncio
    async def test_get_items_by_category(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting items by category."""
        category, _ = await setup_data
        
        # Create another category
        category_repo = SQLAlchemyCategoryRepository(db_session)
        category2 = Category(
            category_name="Furniture",
            category_path="Furniture",
            category_level=1
        )
        created_category2 = await category_repo.create(category2)
        
        # Create items
        repo = SQLAlchemyItemMasterRepository(db_session)
        
        for i in range(3):
            item = ItemMaster(
                item_code=f"ELEC{i:03d}",
                item_name=f"Electronic {i}",
                category_id=category.id
            )
            await repo.create(item)
        
        for i in range(2):
            item = ItemMaster(
                item_code=f"FURN{i:03d}",
                item_name=f"Furniture {i}",
                category_id=created_category2.id
            )
            await repo.create(item)
        
        # Get items by category
        response = await async_client.get(f"/api/v1/item-masters/category/{category.id}/items")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert all(item["category_id"] == str(category.id) for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_get_items_by_brand(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting items by brand."""
        category, brand = setup_data
        
        # Create items
        repo = SQLAlchemyItemMasterRepository(db_session)
        
        for i in range(3):
            item = ItemMaster(
                item_code=f"BRAND{i:03d}",
                item_name=f"Brand Item {i}",
                category_id=category.id,
                brand_id=brand.id
            )
            await repo.create(item)
        
        # Get items by brand
        response = await async_client.get(f"/api/v1/item-masters/brand/{brand.id}/items")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert all(item["brand_id"] == str(brand.id) for item in data["items"])