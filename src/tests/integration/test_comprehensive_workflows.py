import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient

from src.domain.entities.customer import Customer
from src.domain.entities.location import Location, LocationType
from src.domain.entities.category import Category
from src.domain.entities.brand import Brand
from src.domain.entities.item_master import ItemMaster
from src.domain.entities.sku import SKU
from src.domain.entities.inventory_unit import InventoryUnit
from src.domain.entities.stock_level import StockLevel

from src.domain.value_objects.customer_type import CustomerType
from src.domain.value_objects.item_type import ItemType, ConditionGrade, InventoryStatus

from src.infrastructure.repositories.customer_repository import SQLAlchemyCustomerRepository
from src.infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
from src.infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository
from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
from src.infrastructure.repositories.inventory_unit_repository import SQLAlchemyInventoryUnitRepository
from src.infrastructure.repositories.stock_level_repository import SQLAlchemyStockLevelRepository


@pytest.mark.integration
class TestComprehensiveWorkflows:
    """Comprehensive integration tests covering complete business workflows."""
    
    @pytest.fixture
    async def setup_complete_test_data(self, db_session):
        """Set up complete test data for comprehensive testing."""
        
        # Create repositories
        customer_repo = SQLAlchemyCustomerRepository(db_session)
        location_repo = SQLAlchemyLocationRepository(db_session)
        category_repo = SQLAlchemyCategoryRepository(db_session)
        brand_repo = SQLAlchemyBrandRepository(db_session)
        item_repo = SQLAlchemyItemMasterRepository(db_session)
        sku_repo = SQLAlchemySKURepository(db_session)
        inventory_repo = SQLAlchemyInventoryUnitRepository(db_session)
        stock_repo = SQLAlchemyStockLevelRepository(db_session)
        
        # 1. Create Customers
        individual_customer = Customer(
            customer_code="CUST_IND_001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        individual_customer = await customer_repo.create(individual_customer)
        
        business_customer = Customer(
            customer_code="CUST_BUS_001",
            customer_type=CustomerType.BUSINESS,
            business_name="Tech Solutions Inc",
            first_name="Jane",
            last_name="Smith"
        )
        business_customer = await customer_repo.create(business_customer)
        
        # 2. Create Locations
        main_store = Location(
            location_code="STORE_001",
            location_name="Main Store",
            location_type=LocationType.STORE,
            address="123 Main Street",
            city="Downtown",
            state="CA",
            country="USA",
            postal_code="12345"
        )
        main_store = await location_repo.create(main_store)
        
        warehouse = Location(
            location_code="WAREHOUSE_001",
            location_name="Central Warehouse",
            location_type=LocationType.WAREHOUSE,
            address="456 Industrial Blvd",
            city="Industrial Park",
            state="CA",
            country="USA",
            postal_code="54321"
        )
        warehouse = await location_repo.create(warehouse)
        
        # 3. Create Category Hierarchy
        root_category = Category(
            category_name="Electronics"
        )
        root_category = await category_repo.create(root_category)
        
        computers_category = Category(
            category_name="Computers",
            parent_category_id=root_category.id,
            category_level=2
        )
        computers_category = await category_repo.create(computers_category)
        
        laptops_category = Category(
            category_name="Laptops",
            parent_category_id=computers_category.id,
            category_level=3
        )
        laptops_category = await category_repo.create(laptops_category)
        
        # 4. Create Brands
        apple_brand = Brand(
            brand_name="Apple Inc.",
            brand_code="APPLE",
            description="Premium technology products"
        )
        apple_brand = await brand_repo.create(apple_brand)
        
        dell_brand = Brand(
            brand_name="Dell Technologies",
            brand_code="DELL",
            description="Enterprise computing solutions"
        )
        dell_brand = await brand_repo.create(dell_brand)
        
        # 5. Create Item Masters
        macbook_item = ItemMaster(
            item_code="MACBOOK_PRO_13",
            item_name="MacBook Pro 13-inch",
            item_type=ItemType.PRODUCT,
            category_id=laptops_category.id,
            brand_id=apple_brand.id,
            description="Apple MacBook Pro 13-inch laptop",
            is_serialized=True
        )
        macbook_item = await item_repo.create(macbook_item)
        
        dell_laptop_item = ItemMaster(
            item_code="DELL_LATITUDE_7420",
            item_name="Dell Latitude 7420",
            item_type=ItemType.PRODUCT,
            category_id=laptops_category.id,
            brand_id=dell_brand.id,
            description="Dell Latitude 7420 business laptop",
            is_serialized=True
        )
        dell_laptop_item = await item_repo.create(dell_laptop_item)
        
        # 6. Create SKUs
        macbook_sku = SKU(
            sku_code="MACBOOK_PRO_13_NEW",
            sku_name="MacBook Pro 13-inch New",
            item_id=macbook_item.id,
            is_rentable=True,
            is_saleable=True,
            rental_base_price=Decimal("75.00"),
            sale_base_price=Decimal("1899.00")
        )
        macbook_sku = await sku_repo.create(macbook_sku)
        
        dell_sku = SKU(
            sku_code="DELL_LAT_7420_NEW",
            sku_name="Dell Latitude 7420 New",
            item_id=dell_laptop_item.id,
            is_rentable=True,
            is_saleable=True,
            rental_base_price=Decimal("50.00"),
            sale_base_price=Decimal("1299.00")
        )
        dell_sku = await sku_repo.create(dell_sku)
        
        # 7. Create Inventory Units
        inventory_units = []
        for i in range(5):
            # MacBook units
            macbook_unit = InventoryUnit(
                inventory_code=f"INV_MACBOOK_{i+1:03d}",
                sku_id=macbook_sku.id,
                location_id=main_store.id,
                serial_number=f"MACBOOK_{i+1:03d}",
                condition_grade=ConditionGrade.A,
                current_status=InventoryStatus.AVAILABLE_RENT
            )
            macbook_unit = await inventory_repo.create(macbook_unit)
            inventory_units.append(macbook_unit)
            
            # Dell units
            dell_unit = InventoryUnit(
                inventory_code=f"INV_DELL_{i+1:03d}",
                sku_id=dell_sku.id,
                location_id=warehouse.id,
                serial_number=f"DELL_{i+1:03d}",
                condition_grade=ConditionGrade.A,
                current_status=InventoryStatus.AVAILABLE_SALE
            )
            dell_unit = await inventory_repo.create(dell_unit)
            inventory_units.append(dell_unit)
        
        # 8. Create Stock Levels
        macbook_stock = StockLevel(
            sku_id=macbook_sku.id,
            location_id=main_store.id,
            quantity_on_hand=5,
            quantity_available=5,
            quantity_reserved=0,
            quantity_in_transit=0,
            reorder_point=2,
            maximum_stock=10
        )
        macbook_stock = await stock_repo.create(macbook_stock)
        
        dell_stock = StockLevel(
            sku_id=dell_sku.id,
            location_id=warehouse.id,
            quantity_on_hand=5,
            quantity_available=5,
            quantity_reserved=0,
            quantity_in_transit=0,
            reorder_point=3,
            maximum_stock=15
        )
        dell_stock = await stock_repo.create(dell_stock)
        
        return {
            'customers': {
                'individual': individual_customer,
                'business': business_customer
            },
            'locations': {
                'store': main_store,
                'warehouse': warehouse
            },
            'categories': {
                'root': root_category,
                'computers': computers_category,
                'laptops': laptops_category
            },
            'brands': {
                'apple': apple_brand,
                'dell': dell_brand
            },
            'items': {
                'macbook': macbook_item,
                'dell_laptop': dell_laptop_item
            },
            'skus': {
                'macbook': macbook_sku,
                'dell': dell_sku
            },
            'inventory_units': inventory_units,
            'stock_levels': {
                'macbook': macbook_stock,
                'dell': dell_stock
            }
        }
    
    async def test_complete_customer_lifecycle(self, async_client: AsyncClient, setup_complete_test_data):
        """Test complete customer management lifecycle."""
        test_data = setup_complete_test_data
        
        # 1. Create a new customer via API
        new_customer_data = {
            "customer_code": "API_CUST_001",
            "customer_type": "INDIVIDUAL",
            "first_name": "API",
            "last_name": "Customer",
            "tax_id": "123-45-6789"
        }
        
        response = await async_client.post("/api/v1/customers/", json=new_customer_data)
        assert response.status_code == 201
        created_customer = response.json()
        
        # 2. Retrieve customer
        response = await async_client.get(f"/api/v1/customers/{created_customer['id']}")
        assert response.status_code == 200
        retrieved_customer = response.json()
        assert retrieved_customer["customer_code"] == "API_CUST_001"
        
        # 3. Update customer
        update_data = {
            "first_name": "Updated",
            "last_name": "Customer"
        }
        response = await async_client.put(f"/api/v1/customers/{created_customer['id']}", json=update_data)
        assert response.status_code == 200
        updated_customer = response.json()
        assert updated_customer["first_name"] == "Updated"
        
        # 4. List customers
        response = await async_client.get("/api/v1/customers/")
        assert response.status_code == 200
        customers_list = response.json()
        assert customers_list["total"] >= 3  # 2 from setup + 1 created
        
        # 5. Search customers
        response = await async_client.get("/api/v1/customers/?search=API")
        assert response.status_code == 200
        search_results = response.json()
        assert len(search_results["items"]) >= 1
    
    async def test_complete_inventory_workflow(self, async_client: AsyncClient, setup_complete_test_data):
        """Test complete inventory management workflow."""
        test_data = setup_complete_test_data
        
        # 1. Check inventory availability
        macbook_sku_id = str(test_data['skus']['macbook'].id)
        response = await async_client.post("/api/v1/inventory/availability/check", json={"sku_id": macbook_sku_id, "quantity": 2, "for_sale": False})
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        assert response.status_code == 200
        availability = response.json()
        assert availability["available"] is True
        assert availability["available_quantity"] >= 2
        
        # 2. Reserve inventory
        reserve_data = {
            "operation": "reserve",
            "quantity": 2,
            "reason": "Customer rental"
        }
        location_id = str(test_data['locations']['store'].id)
        response = await async_client.put(f"/api/v1/inventory/stock-levels/{macbook_sku_id}/{location_id}/operation", json=reserve_data)
        assert response.status_code == 200
        reservation = response.json()
        
        # 3. Check stock levels after reservation
        response = await async_client.get(f"/api/v1/inventory/stock-levels?sku_id={macbook_sku_id}")
        assert response.status_code == 200
        stock_levels = response.json()
        store_stock = next((s for s in stock_levels["items"] if s["location_id"] == str(test_data['locations']['store'].id)), None)
        assert store_stock is not None
        assert store_stock["quantity_reserved"] == 2
        
        # 4. Update inventory status
        macbook_units = [unit for unit in test_data['inventory_units'] if unit.sku_id == test_data['skus']['macbook'].id]
        unit_id = str(macbook_units[0].id)
        
        status_update = {
            "status": "RENTED",
            "updated_by": "test_user",
            "notes": "Rented to customer"
        }
        response = await async_client.put(f"/api/v1/inventory/units/{unit_id}/status", json=status_update)
        assert response.status_code == 200
        updated_unit = response.json()
        assert updated_unit["status"] == "RENTED"
        
        # 5. Transfer inventory between locations
        transfer_data = {
            "from_location_id": str(test_data['locations']['warehouse'].id),
            "to_location_id": str(test_data['locations']['store'].id),
            "sku_id": str(test_data['skus']['dell'].id),
            "quantity": 1,
            "transfer_reason": "Store restocking",
            "transferred_by": "test_user"
        }
        response = await async_client.post("/api/v1/inventory/units/transfer/by-sku", json=transfer_data)
        assert response.status_code == 200
        transfer_result = response.json()
        assert len(transfer_result) > 0  # Should have transferred units
    
    async def test_category_hierarchy_operations(self, async_client: AsyncClient, setup_complete_test_data):
        """Test category hierarchy management."""
        test_data = setup_complete_test_data
        
        # 1. Create new subcategory
        new_category_data = {
            "category_name": "Gaming Laptops",
            "parent_category_id": str(test_data['categories']['laptops'].id)
        }
        response = await async_client.post("/api/v1/categories/", json=new_category_data)
        assert response.status_code == 201
        created_category = response.json()
        
        # 2. Get category hierarchy
        root_id = str(test_data['categories']['root'].id)
        response = await async_client.get(f"/api/v1/categories/tree/?root_id={root_id}")
        assert response.status_code == 200
        hierarchy = response.json()
        assert isinstance(hierarchy, list)
        
        # 3. Get category path
        laptops_id = str(test_data['categories']['laptops'].id)
        response = await async_client.get(f"/api/v1/categories/{laptops_id}/breadcrumb")
        assert response.status_code == 200
        path = response.json()
        assert len(path["items"]) == 3  # root -> computers -> laptops
        
        # 4. List categories by parent (children of root category)
        root_id = str(test_data['categories']['root'].id)
        response = await async_client.get(f"/api/v1/categories/?parent_id={root_id}")
        assert response.status_code == 200
        level_categories = response.json()
        computers_category = next((c for c in level_categories["items"] if c["category_name"] == "Computers"), None)
        assert computers_category is not None
    
    async def test_brand_and_item_integration(self, async_client: AsyncClient, setup_complete_test_data):
        """Test brand and item master integration."""
        test_data = setup_complete_test_data
        
        # 1. Create new brand
        new_brand_data = {
            "brand_code": "LENOVO",
            "brand_name": "Lenovo Group",
            "description": "Innovative technology solutions",
            "website": "https://www.lenovo.com",
            "country_of_origin": "China"
        }
        response = await async_client.post("/api/v1/brands/", json=new_brand_data)
        assert response.status_code == 201
        created_brand = response.json()
        
        # 2. Create item master for new brand
        new_item_data = {
            "item_code": "THINKPAD_X1",
            "item_name": "ThinkPad X1 Carbon",
            "item_type": "PRODUCT",
            "category_id": str(test_data['categories']['laptops'].id),
            "brand_id": created_brand["id"],
            "description": "Ultra-lightweight business laptop",
            "specifications": {
                "processor": "Intel Core i7",
                "memory": "16GB RAM",
                "storage": "512GB SSD"
            }
        }
        response = await async_client.post("/api/v1/item-masters/", json=new_item_data)
        assert response.status_code == 201
        created_item = response.json()
        
        # 3. Create SKU for new item
        new_sku_data = {
            "sku_code": "THINKPAD_X1_NEW",
            "sku_name": "ThinkPad X1 Carbon New",
            "item_id": created_item["id"],
            "is_rentable": True,
            "is_saleable": True,
            "rental_base_price": 60.00,
            "sale_base_price": 1599.00,
            "weight": 1.13,
            "dimensions": {
                "length": 32.3,
                "width": 21.7,
                "height": 1.47
            }
        }
        response = await async_client.post("/api/v1/skus/", json=new_sku_data)
        assert response.status_code == 201
        created_sku = response.json()
        
        # 4. List items by brand
        response = await async_client.get(f"/api/v1/item-masters/?brand_id={created_brand['id']}")
        assert response.status_code == 200
        brand_items = response.json()
        assert brand_items["total"] >= 1
        
        # 5. List SKUs by item
        response = await async_client.get(f"/api/v1/skus/?item_master_id={created_item['id']}")
        assert response.status_code == 200
        item_skus = response.json()
        assert item_skus["total"] >= 1
    
    async def test_location_operations(self, async_client: AsyncClient, setup_complete_test_data):
        """Test location management operations."""
        test_data = setup_complete_test_data
        
        # 1. Create new location
        new_location_data = {
            "location_code": "OUTLET_001",
            "location_name": "Outlet Store",
            "location_type": "STORE",
            "address": "789 Outlet Plaza",
            "city": "Suburban",
            "state": "CA",
            "country": "USA",
            "postal_code": "67890",
            "contact_number": "+1-555-0123",
            "email": "outlet@example.com"
        }
        response = await async_client.post("/api/v1/locations/", json=new_location_data)
        assert response.status_code == 201
        created_location = response.json()
        
        # 2. List locations by type
        response = await async_client.get("/api/v1/locations/?location_type=STORE")
        assert response.status_code == 200
        store_locations = response.json()
        assert store_locations["total"] >= 2  # main_store + created outlet
        
        # 3. Update location
        update_data = {
            "email": "updated@example.com",
            "contact_number": "+1-555-9999"
        }
        response = await async_client.put(f"/api/v1/locations/{created_location['id']}", json=update_data)
        assert response.status_code == 200
        updated_location = response.json()
        assert updated_location["email"] == "updated@example.com"
        
        # 4. Search locations
        response = await async_client.get("/api/v1/locations/?search=Outlet")
        assert response.status_code == 200
        search_results = response.json()
        assert search_results["total"] >= 1
    
    async def test_cross_domain_data_integrity(self, async_client: AsyncClient, setup_complete_test_data):
        """Test data integrity across domains."""
        test_data = setup_complete_test_data
        
        # 1. Verify item-category relationship
        macbook_item_id = str(test_data['items']['macbook'].id)
        response = await async_client.get(f"/api/v1/item-masters/{macbook_item_id}")
        assert response.status_code == 200
        item_data = response.json()
        assert item_data["category_id"] == str(test_data['categories']['laptops'].id)
        
        # 2. Verify SKU-item relationship
        macbook_sku_id = str(test_data['skus']['macbook'].id)
        response = await async_client.get(f"/api/v1/skus/{macbook_sku_id}")
        assert response.status_code == 200
        sku_data = response.json()
        assert sku_data["item_master_id"] == macbook_item_id
        
        # 3. Verify inventory-SKU-location relationships
        macbook_units = [unit for unit in test_data['inventory_units'] if unit.sku_id == test_data['skus']['macbook'].id]
        unit_id = str(macbook_units[0].id)
        response = await async_client.get(f"/api/v1/inventory/units/{unit_id}")
        assert response.status_code == 200
        inventory_data = response.json()
        assert inventory_data["sku_id"] == macbook_sku_id
        assert inventory_data["location_id"] == str(test_data['locations']['store'].id)
        
        # 4. Verify stock level aggregation
        response = await async_client.get(f"/api/v1/inventory/stock-levels?sku_id={macbook_sku_id}")
        assert response.status_code == 200
        stock_data = response.json()
        store_stock = next((s for s in stock_data if s["location_id"] == str(test_data['locations']['store'].id)), None)
        assert store_stock is not None
        assert store_stock["quantity_on_hand"] == 5
    
    async def test_business_workflow_scenarios(self, async_client: AsyncClient, setup_complete_test_data):
        """Test realistic business workflow scenarios."""
        test_data = setup_complete_test_data
        
        # Scenario 1: New customer wants to rent a laptop
        
        # 1. Customer searches for available laptops
        response = await async_client.get("/api/v1/inventory/units?status=AVAILABLE_RENT")
        assert response.status_code == 200
        available_units = response.json()
        assert available_units["total"] > 0
        
        # 2. Check specific laptop availability
        macbook_sku_id = str(test_data['skus']['macbook'].id)
        response = await async_client.post("/api/v1/inventory/availability/check", json={"sku_id": macbook_sku_id, "quantity": 1, "for_sale": False})
        assert response.status_code == 200
        availability = response.json()
        assert availability["available"] is True
        
        # 3. Reserve the laptop
        reserve_data = {
            "operation": "reserve",
            "quantity": 1,
            "reason": "Customer rental reservation"
        }
        location_id = str(test_data['locations']['store'].id)
        response = await async_client.put(f"/api/v1/inventory/stock-levels/{macbook_sku_id}/{location_id}/operation", json=reserve_data)
        assert response.status_code == 200
        
        # Scenario 2: Store manager checks low stock items
        
        # 4. Get low stock alerts
        response = await async_client.get("/api/v1/inventory/stock-levels/low-stock/alerts")
        assert response.status_code == 200
        low_stock_items = response.json()
        # Should have items that are at or below reorder point
        
        # 5. Transfer items from warehouse to store
        dell_sku_id = str(test_data['skus']['dell'].id)
        transfer_data = {
            "from_location_id": str(test_data['locations']['warehouse'].id),
            "to_location_id": str(test_data['locations']['store'].id),
            "sku_id": dell_sku_id,
            "quantity": 2,
            "transfer_reason": "Restocking store inventory",
            "transferred_by": "store_manager"
        }
        response = await async_client.post("/api/v1/inventory/units/transfer/by-sku", json=transfer_data)
        assert response.status_code == 200
        
        # Scenario 3: Category manager reorganizes product hierarchy
        
        # 6. Create specialized category
        gaming_category_data = {
            "category_name": "Gaming Equipment",
            "parent_category_id": str(test_data['categories']['laptops'].id)
        }
        response = await async_client.post("/api/v1/categories/", json=gaming_category_data)
        assert response.status_code == 201
        gaming_category = response.json()
        
        # 7. Create gaming laptop item
        gaming_laptop_data = {
            "item_code": "ALIENWARE_M15",
            "item_name": "Alienware m15 R7",
            "item_type": "PRODUCT",
            "category_id": gaming_category["id"],
            "brand_id": str(test_data['brands']['dell'].id),
            "description": "High-performance gaming laptop"
        }
        response = await async_client.post("/api/v1/item-masters/", json=gaming_laptop_data)
        assert response.status_code == 201
        
        # 8. Verify category hierarchy integrity
        response = await async_client.get(f"/api/v1/categories/{gaming_category['id']}/breadcrumb")
        assert response.status_code == 200
        category_path = response.json()
        assert len(category_path["items"]) == 4  # root -> computers -> laptops -> gaming
    
    async def test_error_handling_and_validation(self, async_client: AsyncClient, setup_complete_test_data):
        """Test error handling and data validation across domains."""
        test_data = setup_complete_test_data
        
        # 1. Test duplicate customer code
        duplicate_customer = {
            "customer_code": "CUST_IND_001",  # Already exists
            "customer_type": "INDIVIDUAL",
            "first_name": "Duplicate",
            "last_name": "Customer"
        }
        response = await async_client.post("/api/v1/customers/", json=duplicate_customer)
        assert response.status_code == 400
        
        # 2. Test invalid category parent reference
        invalid_category = {
            "category_name": "Invalid Category",
            "parent_category_id": str(uuid4())  # Non-existent parent
        }
        response = await async_client.post("/api/v1/categories/", json=invalid_category)
        assert response.status_code == 400
        
        # 3. Test invalid inventory reservation (insufficient stock)
        macbook_sku_id = str(test_data['skus']['macbook'].id)
        over_reserve_data = {
            "operation": "reserve",
            "quantity": 100,  # More than available
            "reason": "Test over-reservation"
        }
        location_id = str(test_data['locations']['store'].id)
        response = await async_client.put(f"/api/v1/inventory/stock-levels/{macbook_sku_id}/{location_id}/operation", json=over_reserve_data)
        assert response.status_code == 400
        
        # 4. Test invalid SKU creation (non-existent item)
        invalid_sku = {
            "sku_code": "INVALID_SKU",
            "sku_name": "Invalid SKU",
            "item_id": str(uuid4()),  # Non-existent item
            "is_rentable": True,
            "rental_base_price": 50.00
        }
        response = await async_client.post("/api/v1/skus/", json=invalid_sku)
        assert response.status_code == 400
        
        # 5. Test accessing non-existent resources
        response = await async_client.get(f"/api/v1/customers/{uuid4()}")
        assert response.status_code == 404
        
        response = await async_client.get(f"/api/v1/inventory/units/{uuid4()}")
        assert response.status_code == 404