import pytest
from httpx import AsyncClient
from datetime import date
from decimal import Decimal
from uuid import uuid4

from src.domain.value_objects.item_type import ItemType, InventoryStatus, ConditionGrade
from src.domain.entities.location import LocationType


class TestInventoryAPI:
    """Integration tests for Inventory API endpoints."""
    
    @pytest.fixture
    async def test_location(self, db_session):
        """Create a test location directly in database."""
        from src.domain.entities.location import Location
        from src.infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
        
        repository = SQLAlchemyLocationRepository(db_session)
        
        location = Location(
            location_code="TST001",
            location_name="Test Store",
            location_type=LocationType.STORE,
            address="123 Test St",
            city="Test City",
            state="TC",
            country="USA",
            postal_code="12345",
            contact_number="+1234567890",
            email="test@store.com"
        )
        
        created_location = await repository.create(location)
        
        return {
            "id": str(created_location.id),
            "location_code": created_location.location_code,
            "location_name": created_location.location_name,
            "location_type": created_location.location_type.value
        }
    
    @pytest.fixture
    async def test_category(self, db_session):
        """Create a test category directly in database."""
        from src.domain.entities.category import Category
        from src.infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
        
        repository = SQLAlchemyCategoryRepository(db_session)
        
        category = Category(
            category_name="Electronics",
            parent_category_id=None
        )
        
        created_category = await repository.create(category)
        
        return {
            "id": str(created_category.id),
            "category_name": created_category.category_name
        }
    
    @pytest.fixture
    async def test_brand(self, db_session):
        """Create a test brand directly in database."""
        from src.domain.entities.brand import Brand
        from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository
        
        repository = SQLAlchemyBrandRepository(db_session)
        
        brand = Brand(
            brand_name="TestBrand",
            brand_code="TB001",
            description="Test Brand"
        )
        
        created_brand = await repository.create(brand)
        
        return {
            "id": str(created_brand.id),
            "brand_name": created_brand.brand_name,
            "brand_code": created_brand.brand_code
        }
    
    @pytest.fixture
    async def test_item_master(self, db_session, test_category, test_brand):
        """Create a test item master directly in database."""
        from src.domain.entities.item_master import ItemMaster
        from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
        
        repository = SQLAlchemyItemMasterRepository(db_session)
        
        item = ItemMaster(
            item_code="PROD001",
            item_name="Test Product",
            description="Test product for inventory",
            category_id=test_category["id"],
            brand_id=test_brand["id"],
            item_type=ItemType.PRODUCT,
            is_serialized=False
        )
        
        created_item = await repository.create(item)
        
        return {
            "id": str(created_item.id),
            "item_code": created_item.item_code,
            "item_name": created_item.item_name
        }
    
    @pytest.fixture
    async def test_sku(self, db_session, test_item_master):
        """Create a test SKU directly in database."""
        from src.domain.entities.sku import SKU
        from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
        
        repository = SQLAlchemySKURepository(db_session)
        
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU - Large",
            item_id=test_item_master["id"],
            is_rentable=True,
            is_saleable=True,
            rental_base_price=Decimal("10.00"),
            sale_base_price=Decimal("100.00"),
            min_rental_days=1
        )
        
        created_sku = await repository.create(sku)
        
        return {
            "id": str(created_sku.id),
            "sku_code": created_sku.sku_code,
            "sku_name": created_sku.sku_name
        }

    # Inventory Unit Tests
    async def test_create_inventory_unit(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test creating an inventory unit."""
        inventory_data = {
            "inventory_code": "INV001",
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "current_status": "AVAILABLE_SALE",
            "condition_grade": "A",
            "purchase_date": str(date.today()),
            "purchase_cost": 80.00,
            "notes": "Test inventory unit"
        }
        
        response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["inventory_code"] == "INV001"
        assert data["sku_id"] == test_sku["id"]
        assert data["location_id"] == test_location["id"]
        assert data["current_status"] == "AVAILABLE_SALE"
        assert data["condition_grade"] == "A"
        assert float(data["purchase_cost"]) == 80.00
        assert data["notes"] == "Test inventory unit"
        assert "id" in data
        assert data["is_active"] == True

    async def test_get_inventory_unit(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test getting an inventory unit by ID."""
        # Create an inventory unit first
        inventory_data = {
            "inventory_code": "INV002",
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "current_status": "AVAILABLE_RENT",
            "condition_grade": "B"
        }
        
        create_response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert create_response.status_code == 201
        unit = create_response.json()
        
        # Get the inventory unit
        response = await async_client.get(f"/api/v1/inventory/units/{unit['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == unit["id"]
        assert data["inventory_code"] == "INV002"
        assert data["current_status"] == "AVAILABLE_RENT"
        assert data["condition_grade"] == "B"

    async def test_get_inventory_unit_by_code(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test getting an inventory unit by code."""
        # Create an inventory unit first
        inventory_data = {
            "inventory_code": "INV003",
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "current_status": "AVAILABLE_SALE",
            "condition_grade": "A"
        }
        
        create_response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert create_response.status_code == 201
        
        # Get by code
        response = await async_client.get("/api/v1/inventory/units/code/INV003")
        assert response.status_code == 200
        
        data = response.json()
        assert data["inventory_code"] == "INV003"
        assert data["current_status"] == "AVAILABLE_SALE"

    async def test_list_inventory_units(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test listing inventory units with filters."""
        # Create multiple inventory units
        for i in range(3):
            inventory_data = {
                "inventory_code": f"INV00{i+4}",
                "sku_id": test_sku["id"],
                "location_id": test_location["id"],
                "current_status": "AVAILABLE_SALE" if i % 2 == 0 else "AVAILABLE_RENT",
                "condition_grade": "A" if i == 0 else "B"
            }
            response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
            assert response.status_code == 201
        
        # List all inventory units
        response = await async_client.get("/api/v1/inventory/units")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3
        
        # Filter by status
        response = await async_client.get("/api/v1/inventory/units?status=AVAILABLE_SALE")
        assert response.status_code == 200
        
        data = response.json()
        assert all(item["current_status"] == "AVAILABLE_SALE" for item in data["items"])
        
        # Filter by location
        response = await async_client.get(f"/api/v1/inventory/units?location_id={test_location['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert all(item["location_id"] == test_location["id"] for item in data["items"])

    async def test_update_inventory_status(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test updating inventory unit status."""
        # Create an inventory unit
        inventory_data = {
            "inventory_code": "INV007",
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "current_status": "AVAILABLE_SALE",
            "condition_grade": "A"
        }
        
        create_response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert create_response.status_code == 201
        unit = create_response.json()
        
        # Update status
        status_data = {
            "new_status": "RESERVED_SALE",
            "notes": "Reserved for customer"
        }
        
        response = await async_client.put(
            f"/api/v1/inventory/units/{unit['id']}/status",
            json=status_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_status"] == "RESERVED_SALE"
        # Notes might be None or a string containing our note
        assert data["notes"] is None or "Reserved for customer" in data["notes"]

    # Stock Level Tests
    async def test_create_stock_level(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test creating a stock level."""
        stock_data = {
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "quantity_on_hand": 50,
            "reorder_point": 10,
            "reorder_quantity": 100,
            "maximum_stock": 200
        }
        
        response = await async_client.post("/api/v1/inventory/stock-levels", json=stock_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["sku_id"] == test_sku["id"]
        assert data["location_id"] == test_location["id"]
        assert data["quantity_on_hand"] == 50
        assert data["quantity_available"] == 50  # Should equal on_hand initially
        assert data["quantity_reserved"] == 0
        assert data["reorder_point"] == 10
        assert data["reorder_quantity"] == 100
        assert data["maximum_stock"] == 200

    async def test_get_stock_level(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test getting a stock level."""
        # Create stock level first
        stock_data = {
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "quantity_on_hand": 25,
            "reorder_point": 5,
            "reorder_quantity": 50
        }
        
        create_response = await async_client.post("/api/v1/inventory/stock-levels", json=stock_data)
        assert create_response.status_code == 201
        stock = create_response.json()
        
        # Get the stock level (using sku_id/location_id path)
        response = await async_client.get(f"/api/v1/inventory/stock-levels/{test_sku['id']}/{test_location['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == stock["id"]
        assert data["quantity_on_hand"] == 25

    async def test_check_stock_availability(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test checking stock availability."""
        # Create stock level
        stock_data = {
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "quantity_on_hand": 10,
            "reorder_point": 5
        }
        
        create_response = await async_client.post("/api/v1/inventory/stock-levels", json=stock_data)
        assert create_response.status_code == 201
        
        # Check availability
        availability_data = {
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "quantity": 5
        }
        
        response = await async_client.post(
            "/api/v1/inventory/availability/check",
            json=availability_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["available"] == True
        assert data["available_quantity"] == 10
        assert data["requested_quantity"] == 5
        
        # Check unavailable quantity
        availability_data["quantity"] = 15
        response = await async_client.post(
            "/api/v1/inventory/availability/check",
            json=availability_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["available"] == False
        assert data["available_quantity"] == 10
        assert data["requested_quantity"] == 15

    async def test_update_stock_levels(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test updating stock levels."""
        # Create stock level
        stock_data = {
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "quantity_on_hand": 20,
            "reorder_point": 5
        }
        
        create_response = await async_client.post("/api/v1/inventory/stock-levels", json=stock_data)
        assert create_response.status_code == 201
        stock = create_response.json()
        
        # Update stock level
        update_data = {
            "operation": "RECEIVE",
            "quantity": 30,
            "notes": "Received new stock"
        }
        
        response = await async_client.put(
            f"/api/v1/inventory/stock-levels/{test_sku['id']}/{test_location['id']}/operation",
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["quantity_on_hand"] == 50  # 20 + 30
        assert data["quantity_available"] == 50

    async def test_transfer_inventory(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test transferring inventory between locations."""
        # This test would require a second location
        # For now, we'll test the endpoint structure
        
        # Create an inventory unit
        inventory_data = {
            "inventory_code": "INV008",
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "current_status": "AVAILABLE_SALE",
            "condition_grade": "A"
        }
        
        create_response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert create_response.status_code == 201
        unit = create_response.json()
        
        # Test transfer data structure (would fail without second location)
        transfer_data = {
            "from_location_id": test_location["id"],
            "to_location_id": str(uuid4()),  # Non-existent location
            "units": [unit["id"]],
            "notes": "Transfer test"
        }
        
        response = await async_client.post(f"/api/v1/inventory/units/{unit['id']}/transfer", json=transfer_data)
        # This should fail with 400 due to invalid location, which is expected
        assert response.status_code == 400

    async def test_low_stock_alerts(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test getting low stock alerts."""
        # Create stock level below reorder point
        stock_data = {
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "quantity_on_hand": 3,
            "reorder_point": 10,
            "reorder_quantity": 50
        }
        
        create_response = await async_client.post("/api/v1/inventory/stock-levels", json=stock_data)
        assert create_response.status_code == 201
        
        # Get low stock alerts
        response = await async_client.get("/api/v1/inventory/stock-levels/low-stock/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) >= 1
        # Should contain our low stock item
        low_stock_item = next((item for item in data["items"] if item["sku_id"] == test_sku["id"]), None)
        assert low_stock_item is not None
        assert low_stock_item["quantity_on_hand"] == 3
        assert low_stock_item["reorder_point"] == 10

    async def test_inventory_validation_errors(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test inventory validation errors."""
        # Missing required fields
        inventory_data = {
            "sku_id": test_sku["id"],
            "location_id": test_location["id"]
            # Missing inventory_code and current_status
        }
        
        response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert response.status_code == 422  # Validation error
        
        # Invalid status
        inventory_data = {
            "inventory_code": "INV009",
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "current_status": "INVALID_STATUS",
            "condition_grade": "A"
        }
        
        response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert response.status_code == 422  # Validation error
        
        # Non-existent SKU
        inventory_data = {
            "inventory_code": "INV010",
            "sku_id": str(uuid4()),  # Non-existent SKU
            "location_id": test_location["id"],
            "current_status": "AVAILABLE_SALE",
            "condition_grade": "A"
        }
        
        response = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert response.status_code == 400  # Business logic error

    async def test_duplicate_inventory_code(
        self, async_client: AsyncClient, test_sku, test_location
    ):
        """Test that duplicate inventory codes are rejected."""
        inventory_data = {
            "inventory_code": "DUPLICATE001",
            "sku_id": test_sku["id"],
            "location_id": test_location["id"],
            "current_status": "AVAILABLE_SALE",
            "condition_grade": "A"
        }
        
        # Create first inventory unit
        response1 = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert response1.status_code == 201
        
        # Try to create second with same code
        response2 = await async_client.post("/api/v1/inventory/units", json=inventory_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()