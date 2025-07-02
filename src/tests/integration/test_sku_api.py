import pytest
from uuid import UUID, uuid4
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.sku import SKU
from src.domain.entities.item_master import ItemMaster
from src.domain.entities.category import Category
from src.domain.entities.brand import Brand
from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
from src.infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository


@pytest.mark.integration
class TestSKUAPI:
    """Integration tests for SKU API endpoints."""
    
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
        
        # Create item master
        item_repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Laptop",
            category_id=created_category.id,
            brand_id=created_brand.id,
            is_serialized=True
        )
        created_item = await item_repo.create(item)
        
        return created_item
    
    @pytest.mark.asyncio
    async def test_create_sku(self, async_client: AsyncClient, setup_data):
        """Test creating a SKU."""
        item = await setup_data
        
        sku_data = {
            "sku_code": "SKU001",
            "sku_name": "Laptop Model A",
            "item_id": str(item.id),
            "barcode": "1234567890123",
            "model_number": "LP-001",
            "weight": "2.5",
            "dimensions": {"length": "30", "width": "20", "height": "2"},
            "is_rentable": True,
            "is_saleable": True,
            "min_rental_days": 3,
            "max_rental_days": 30,
            "rental_base_price": "25.00",
            "sale_base_price": "1000.00"
        }
        
        response = await async_client.post("/api/v1/skus/", json=sku_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["sku_code"] == "SKU001"
        assert data["sku_name"] == "Laptop Model A"
        assert data["item_id"] == str(item.id)
        assert data["barcode"] == "1234567890123"
        assert data["model_number"] == "LP-001"
        assert float(data["weight"]) == 2.5
        assert data["dimensions"]["length"] == "30"
        assert data["is_rentable"] is True
        assert data["is_saleable"] is True
        assert data["min_rental_days"] == 3
        assert data["max_rental_days"] == 30
        assert float(data["rental_base_price"]) == 25.00
        assert float(data["sale_base_price"]) == 1000.00
        assert data["is_active"] is True
        assert "id" in data
        assert UUID(data["id"])  # Validate UUID format
    
    @pytest.mark.asyncio
    async def test_create_minimal_sku(self, async_client: AsyncClient, setup_data):
        """Test creating SKU with minimal fields."""
        item = await setup_data
        
        sku_data = {
            "sku_code": "SKU002",
            "sku_name": "Basic SKU",
            "item_id": str(item.id)
        }
        
        response = await async_client.post("/api/v1/skus/", json=sku_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["sku_code"] == "SKU002"
        assert data["is_rentable"] is False
        assert data["is_saleable"] is True
        assert data["min_rental_days"] == 1
    
    @pytest.mark.asyncio
    async def test_create_sku_duplicate_code(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test creating SKU with duplicate code fails."""
        item = await setup_data
        
        # Create first SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="SKU001",
            sku_name="First SKU",
            item_id=item.id
        )
        await repo.create(sku)
        
        # Try to create duplicate
        sku_data = {
            "sku_code": "SKU001",
            "sku_name": "Duplicate SKU",
            "item_id": str(item.id)
        }
        
        response = await async_client.post("/api/v1/skus/", json=sku_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_sku_duplicate_barcode(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test creating SKU with duplicate barcode fails."""
        item = await setup_data
        
        # Create first SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="SKU001",
            sku_name="First SKU",
            item_id=item.id,
            barcode="1234567890123"
        )
        await repo.create(sku)
        
        # Try to create with duplicate barcode
        sku_data = {
            "sku_code": "SKU002",
            "sku_name": "Different SKU",
            "item_id": str(item.id),
            "barcode": "1234567890123"
        }
        
        response = await async_client.post("/api/v1/skus/", json=sku_data)
        assert response.status_code == 400
        assert "barcode" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_sku_invalid_item(self, async_client: AsyncClient):
        """Test creating SKU with invalid item ID fails."""
        fake_item_id = "550e8400-e29b-41d4-a716-446655440000"
        
        sku_data = {
            "sku_code": "SKU001",
            "sku_name": "Test SKU",
            "item_id": fake_item_id
        }
        
        response = await async_client.post("/api/v1/skus/", json=sku_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_sku_validation(self, async_client: AsyncClient, setup_data):
        """Test SKU creation validation."""
        item = await setup_data
        
        # Test neither rentable nor saleable
        sku_data = {
            "sku_code": "SKU001",
            "sku_name": "Invalid SKU",
            "item_id": str(item.id),
            "is_rentable": False,
            "is_saleable": False
        }
        
        response = await async_client.post("/api/v1/skus/", json=sku_data)
        assert response.status_code == 422  # Pydantic validation error
    
    @pytest.mark.asyncio
    async def test_get_sku_by_id(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting SKU by ID."""
        item = await setup_data
        
        # Create SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=item.id,
            barcode="1234567890123"
        )
        created_sku = await repo.create(sku)
        
        # Get by ID
        response = await async_client.get(f"/api/v1/skus/{created_sku.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(created_sku.id)
        assert data["sku_code"] == "SKU001"
        assert data["sku_name"] == "Test SKU"
        assert data["barcode"] == "1234567890123"
    
    @pytest.mark.asyncio
    async def test_get_sku_not_found(self, async_client: AsyncClient):
        """Test getting non-existent SKU returns 404."""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await async_client.get(f"/api/v1/skus/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_sku_by_code(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting SKU by code."""
        item = await setup_data
        
        # Create SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=item.id
        )
        await repo.create(sku)
        
        # Get by code
        response = await async_client.get("/api/v1/skus/code/SKU001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["sku_code"] == "SKU001"
        assert data["sku_name"] == "Test SKU"
    
    @pytest.mark.asyncio
    async def test_get_sku_by_barcode(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting SKU by barcode."""
        item = await setup_data
        
        # Create SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=item.id,
            barcode="9876543210987"
        )
        await repo.create(sku)
        
        # Get by barcode
        response = await async_client.get("/api/v1/skus/barcode/9876543210987")
        
        assert response.status_code == 200
        data = response.json()
        assert data["barcode"] == "9876543210987"
    
    @pytest.mark.asyncio
    async def test_list_skus(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test listing SKUs with pagination."""
        item = await setup_data
        
        # Create multiple SKUs
        repo = SQLAlchemySKURepository(db_session)
        for i in range(5):
            sku = SKU(
                sku_code=f"SKU{i:03d}",
                sku_name=f"SKU {i}",
                item_id=item.id,
                is_rentable=i < 3,
                is_saleable=True
            )
            await repo.create(sku)
        
        # List all SKUs
        response = await async_client.get("/api/v1/skus/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        assert len(data["items"]) >= 5
        assert data["skip"] == 0
        assert data["limit"] == 100
        
        # Test pagination
        response = await async_client.get("/api/v1/skus/?skip=2&limit=2")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2
    
    @pytest.mark.asyncio
    async def test_list_skus_with_filters(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test listing SKUs with filters."""
        item = await setup_data
        
        # Create SKUs
        repo = SQLAlchemySKURepository(db_session)
        
        rentable_sku = SKU(
            sku_code="RENT001",
            sku_name="Rentable SKU",
            item_id=item.id,
            is_rentable=True,
            is_saleable=False
        )
        
        saleable_sku = SKU(
            sku_code="SALE001",
            sku_name="Saleable SKU",
            item_id=item.id,
            is_rentable=False,
            is_saleable=True
        )
        
        await repo.create(rentable_sku)
        await repo.create(saleable_sku)
        
        # Filter by rentable
        response = await async_client.get("/api/v1/skus/?is_rentable=true")
        data = response.json()
        assert all(item["is_rentable"] is True for item in data["items"])
        
        # Filter by saleable
        response = await async_client.get("/api/v1/skus/?is_saleable=true")
        data = response.json()
        assert all(item["is_saleable"] is True for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_search_skus(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test searching SKUs."""
        item = await setup_data
        
        # Create SKUs
        repo = SQLAlchemySKURepository(db_session)
        
        skus = [
            SKU(
                sku_code="LAP001RED",
                sku_name="Laptop Red Edition",
                item_id=item.id,
                model_number="LP-RED-001"
            ),
            SKU(
                sku_code="LAP001BLU",
                sku_name="Laptop Blue Edition",
                item_id=item.id,
                model_number="LP-BLU-001"
            ),
            SKU(
                sku_code="ACC001",
                sku_name="Laptop Bag",
                item_id=item.id,
                barcode="BAG123456"
            )
        ]
        
        for sku in skus:
            await repo.create(sku)
        
        # Search for "red"
        response = await async_client.get("/api/v1/skus/?search=red")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("red" in item["sku_name"].lower() or 
                  "red" in item["sku_code"].lower() or
                  ("model_number" in item and item["model_number"] and "red" in item["model_number"].lower())
                  for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_update_sku(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test updating SKU."""
        item = await setup_data
        
        # Create SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="SKU001",
            sku_name="Original Name",
            item_id=item.id
        )
        created_sku = await repo.create(sku)
        
        # Update SKU
        update_data = {
            "sku_name": "Updated Name",
            "barcode": "9999999999999",
            "model_number": "NEW-MODEL",
            "weight": "3.5",
            "dimensions": {"length": "35", "width": "25", "height": "3"}
        }
        
        response = await async_client.put(
            f"/api/v1/skus/{created_sku.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["sku_name"] == "Updated Name"
        assert data["barcode"] == "9999999999999"
        assert data["model_number"] == "NEW-MODEL"
        assert float(data["weight"]) == 3.5
        assert data["dimensions"]["length"] == "35"
    
    @pytest.mark.asyncio
    async def test_update_sku_rental_settings(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test updating SKU rental settings."""
        item = await setup_data
        
        # Create SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=item.id,
            is_rentable=False
        )
        created_sku = await repo.create(sku)
        
        # Enable rental
        rental_data = {
            "is_rentable": True,
            "min_rental_days": 7,
            "max_rental_days": 60,
            "rental_base_price": "30.00"
        }
        
        response = await async_client.put(
            f"/api/v1/skus/{created_sku.id}/rental",
            json=rental_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_rentable"] is True
        assert data["min_rental_days"] == 7
        assert data["max_rental_days"] == 60
        assert float(data["rental_base_price"]) == 30.00
    
    @pytest.mark.asyncio
    async def test_update_sku_sale_settings(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test updating SKU sale settings."""
        item = await setup_data
        
        # Create SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=item.id,
            is_rentable=True,  # Must be rentable if we disable sale
            is_saleable=True
        )
        created_sku = await repo.create(sku)
        
        # Update sale settings
        sale_data = {
            "is_saleable": False,
            "sale_base_price": "1500.00"
        }
        
        response = await async_client.put(
            f"/api/v1/skus/{created_sku.id}/sale",
            json=sale_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_saleable"] is False
    
    @pytest.mark.asyncio
    async def test_delete_sku(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test soft deleting a SKU."""
        item = await setup_data
        
        # Create SKU
        repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="DELETE001",
            sku_name="Delete Me",
            item_id=item.id
        )
        created_sku = await repo.create(sku)
        
        # Delete SKU
        response = await async_client.delete(f"/api/v1/skus/{created_sku.id}")
        
        assert response.status_code == 204
        
        # Verify SKU is soft deleted
        deleted_sku = await repo.get_by_id(created_sku.id)
        assert deleted_sku.is_active is False
    
    @pytest.mark.asyncio
    async def test_get_skus_by_item(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting SKUs by item."""
        item = await setup_data
        
        # Create another item
        item_repo = SQLAlchemyItemMasterRepository(db_session)
        item2 = ItemMaster(
            item_code="ITEM002",
            item_name="Another Item",
            category_id=item.category_id
        )
        created_item2 = await item_repo.create(item2)
        
        # Create SKUs
        sku_repo = SQLAlchemySKURepository(db_session)
        
        for i in range(3):
            sku = SKU(
                sku_code=f"ITEM1SKU{i:03d}",
                sku_name=f"Item 1 SKU {i}",
                item_id=item.id
            )
            await sku_repo.create(sku)
        
        for i in range(2):
            sku = SKU(
                sku_code=f"ITEM2SKU{i:03d}",
                sku_name=f"Item 2 SKU {i}",
                item_id=created_item2.id
            )
            await sku_repo.create(sku)
        
        # Get SKUs by item
        response = await async_client.get(f"/api/v1/skus/item/{item.id}/skus")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert all(sku["item_id"] == str(item.id) for sku in data["items"])
    
    @pytest.mark.asyncio
    async def test_get_rentable_skus(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting all rentable SKUs."""
        item = await setup_data
        
        # Create SKUs
        repo = SQLAlchemySKURepository(db_session)
        
        for i in range(3):
            sku = SKU(
                sku_code=f"RENT{i:03d}",
                sku_name=f"Rentable {i}",
                item_id=item.id,
                is_rentable=True,
                rental_base_price=Decimal("20.00")
            )
            await repo.create(sku)
        
        # Get rentable SKUs
        response = await async_client.get("/api/v1/skus/rentable/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert all(sku["is_rentable"] is True for sku in data["items"])
    
    @pytest.mark.asyncio
    async def test_get_saleable_skus(self, async_client: AsyncClient, db_session: AsyncSession, setup_data):
        """Test getting all saleable SKUs."""
        item = await setup_data
        
        # Create SKUs
        repo = SQLAlchemySKURepository(db_session)
        
        for i in range(3):
            sku = SKU(
                sku_code=f"SALE{i:03d}",
                sku_name=f"Saleable {i}",
                item_id=item.id,
                is_saleable=True,
                sale_base_price=Decimal("500.00")
            )
            await repo.create(sku)
        
        # Get saleable SKUs
        response = await async_client.get("/api/v1/skus/saleable/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert all(sku["is_saleable"] is True for sku in data["items"])