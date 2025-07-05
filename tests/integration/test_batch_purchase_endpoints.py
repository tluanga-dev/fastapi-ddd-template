import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from src.domain.entities.customer import Customer
from src.domain.entities.location import Location
from src.domain.entities.category import Category
from src.domain.entities.brand import Brand
from src.domain.value_objects.customer_type import CustomerType


@pytest.fixture
async def test_data(db_session):
    """Create test data for batch purchase tests."""
    from src.infrastructure.repositories.customer_repository import SQLAlchemyCustomerRepository
    from src.infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
    from src.infrastructure.repositories.category_repository import SQLAlchemyCategoryRepository
    from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository
    
    customer_repo = SQLAlchemyCustomerRepository(db_session)
    location_repo = SQLAlchemyLocationRepository(db_session)
    category_repo = SQLAlchemyCategoryRepository(db_session)
    brand_repo = SQLAlchemyBrandRepository(db_session)
    
    # Create supplier (business customer)
    supplier = Customer(
        customer_code="SUPP001",
        customer_type=CustomerType.BUSINESS,
        first_name="Tech",
        last_name="Solutions",
        business_name="Tech Solutions Inc.",
        email="orders@techsolutions.com",
        phone="555-0123"
    )
    await customer_repo.create(supplier)
    
    # Create location
    location = Location(
        location_code="WH001",
        location_name="Main Warehouse",
        location_type="WAREHOUSE",
        address="123 Industrial Blvd"
    )
    await location_repo.create(location)
    
    # Create category
    category = Category(
        category_code="ELEC",
        category_name="Electronics",
        description="Electronic devices and components"
    )
    await category_repo.create(category)
    
    # Create brand
    brand = Brand(
        brand_code="DELL",
        brand_name="Dell Technologies",
        description="Computer hardware manufacturer"
    )
    await brand_repo.create(brand)
    
    return {
        "supplier": supplier,
        "location": location,
        "category": category,
        "brand": brand
    }


class TestBatchPurchaseEndpoints:
    """Test batch purchase API endpoints."""
    
    async def test_create_batch_purchase_with_new_items(self, client, test_data):
        """Test creating a batch purchase with new item masters and SKUs."""
        request_data = {
            "supplier_id": str(test_data["supplier"].id),
            "location_id": str(test_data["location"].id),
            "purchase_date": date.today().isoformat(),
            "tax_rate": 8.25,
            "invoice_number": "INV-2024-001",
            "notes": "Test batch purchase with new items",
            "auto_generate_codes": True,
            "validate_only": False,
            "items": [
                {
                    "new_item_master": {
                        "item_name": "Dell Laptop XPS 13",
                        "category_id": str(test_data["category"].id),
                        "brand_id": str(test_data["brand"].id),
                        "description": "High-performance ultrabook",
                        "is_serialized": True
                    },
                    "new_sku": {
                        "sku_name": "Dell XPS 13 - 16GB/512GB",
                        "model_number": "XPS13-16-512",
                        "weight": 1.2,
                        "dimensions": {"length": 30.2, "width": 19.9, "height": 1.48},
                        "is_rentable": True,
                        "is_saleable": True,
                        "min_rental_days": 1,
                        "max_rental_days": 30,
                        "rental_base_price": 25.0,
                        "sale_base_price": 999.99
                    },
                    "quantity": 2,
                    "unit_cost": 750.00,
                    "condition_notes": "New in box",
                    "notes": "For rental fleet"
                },
                {
                    "new_item_master": {
                        "item_name": "Dell Wireless Mouse",
                        "category_id": str(test_data["category"].id),
                        "brand_id": str(test_data["brand"].id),
                        "description": "Wireless optical mouse",
                        "is_serialized": False
                    },
                    "new_sku": {
                        "sku_name": "Dell WM126 Wireless Mouse",
                        "model_number": "WM126",
                        "weight": 0.06,
                        "is_rentable": False,
                        "is_saleable": True,
                        "sale_base_price": 19.99
                    },
                    "quantity": 10,
                    "unit_cost": 12.50,
                    "condition_notes": "New",
                    "notes": "Accessories for laptops"
                }
            ]
        }
        
        response = await client.post("/api/v1/transactions/purchases/batch", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "transaction_id" in data
        assert "transaction_number" in data
        assert "created_item_masters" in data
        assert "created_skus" in data
        assert "total_amount" in data
        assert "total_items" in data
        assert "processing_time_ms" in data
        
        # Verify entities were created
        assert len(data["created_item_masters"]) == 2
        assert len(data["created_skus"]) == 2
        assert data["total_items"] == 2
        
        # Verify total calculation (subtotal + tax)
        subtotal = (2 * 750.00) + (10 * 12.50)  # 1500 + 125 = 1625
        tax = subtotal * 0.0825  # 134.06
        expected_total = subtotal + tax  # 1759.06
        assert abs(data["total_amount"] - expected_total) < 0.01
        
        # Verify transaction was created by fetching it
        transaction_response = await client.get(f"/api/v1/transactions/{data['transaction_id']}")
        assert transaction_response.status_code == 200
        transaction_data = transaction_response.json()
        assert transaction_data["transaction_type"] == "PURCHASE"
        assert len(transaction_data["lines"]) == 2
    
    async def test_validate_batch_purchase_only(self, client, test_data):
        """Test validating a batch purchase without creating records."""
        request_data = {
            "supplier_id": str(test_data["supplier"].id),
            "location_id": str(test_data["location"].id),
            "purchase_date": date.today().isoformat(),
            "tax_rate": 7.0,
            "auto_generate_codes": True,
            "validate_only": True,
            "items": [
                {
                    "new_item_master": {
                        "item_name": "Test Laptop",
                        "category_id": str(test_data["category"].id),
                        "is_serialized": True
                    },
                    "new_sku": {
                        "sku_name": "Test Laptop SKU",
                        "is_saleable": True,
                        "sale_base_price": 500.0
                    },
                    "quantity": 1,
                    "unit_cost": 400.00
                }
            ]
        }
        
        response = await client.post("/api/v1/transactions/purchases/batch/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify validation response structure
        assert data["is_valid"] is True
        assert "validation_errors" in data
        assert "warnings" in data
        assert data["items_to_create"] == 1
        assert data["skus_to_create"] == 1
        assert data["existing_skus"] == 0
        assert len(data["generated_item_codes"]) == 1
        assert len(data["generated_sku_codes"]) == 1
        
        # Verify no actual entities were created (validation only)
        # The generated codes should be based on the item/SKU names
        assert "TESTLAPTOP" in data["generated_item_codes"][0]
        assert "TESTLAPTOPSKU" in data["generated_sku_codes"][0]
    
    async def test_batch_purchase_validation_errors(self, client, test_data):
        """Test batch purchase validation with invalid data."""
        request_data = {
            "supplier_id": str(test_data["supplier"].id),
            "location_id": str(test_data["location"].id),
            "purchase_date": date.today().isoformat(),
            "items": [
                {
                    "new_item_master": {
                        "item_name": "",  # Invalid: empty name
                        "category_id": str(uuid4()),  # Invalid: non-existent category
                    },
                    "new_sku": {
                        "sku_name": "",  # Invalid: empty name
                        "min_rental_days": 5,
                        "max_rental_days": 3,  # Invalid: max < min
                    },
                    "quantity": 0,  # Invalid: zero quantity
                    "unit_cost": -10.00  # Invalid: negative cost
                }
            ]
        }
        
        response = await client.post("/api/v1/transactions/purchases/batch", json=request_data)
        
        assert response.status_code == 400
        error_data = response.json()
        
        # Verify error response structure
        assert "error_type" in error_data
        assert "error_message" in error_data
        assert "failed_at_step" in error_data
        assert "suggested_actions" in error_data
        
        # Should fail at validation step
        assert error_data["failed_at_step"] == "validation"
        assert "validation failed" in error_data["error_message"].lower()
    
    async def test_batch_purchase_with_existing_sku(self, client, test_data):
        """Test batch purchase using existing SKUs."""
        # First create an item master and SKU
        from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
        from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
        from src.domain.entities.item_master import ItemMaster
        from src.domain.entities.sku import SKU
        from src.domain.value_objects.item_type import ItemType
        
        item_repo = SQLAlchemyItemMasterRepository(client.app.state.db_session)
        sku_repo = SQLAlchemySKURepository(client.app.state.db_session)
        
        # Create item master
        item_master = ItemMaster(
            item_code="EXISTING001",
            item_name="Existing Test Item",
            category_id=test_data["category"].id,
            item_type=ItemType.PRODUCT
        )
        await item_repo.create(item_master)
        
        # Create SKU
        sku = SKU(
            sku_code="EXISTING-SKU-001",
            sku_name="Existing Test SKU",
            item_id=item_master.id,
            sale_base_price=Decimal("100.00")
        )
        await sku_repo.create(sku)
        
        # Now create batch purchase using existing SKU
        request_data = {
            "supplier_id": str(test_data["supplier"].id),
            "location_id": str(test_data["location"].id),
            "purchase_date": date.today().isoformat(),
            "items": [
                {
                    "sku_id": str(sku.id),
                    "quantity": 5,
                    "unit_cost": 80.00,
                    "notes": "Restocking existing item"
                }
            ]
        }
        
        response = await client.post("/api/v1/transactions/purchases/batch", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify no new entities were created
        assert len(data["created_item_masters"]) == 0
        assert len(data["created_skus"]) == 0
        assert len(data["used_existing_skus"]) == 1
        assert str(sku.id) in data["used_existing_skus"]
        
        # Verify total calculation
        expected_total = 5 * 80.00  # No tax in this example
        assert data["total_amount"] == expected_total
    
    async def test_batch_purchase_mixed_items(self, client, test_data):
        """Test batch purchase with mix of existing and new items."""
        # First create an existing SKU
        from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
        from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
        from src.domain.entities.item_master import ItemMaster
        from src.domain.entities.sku import SKU
        from src.domain.value_objects.item_type import ItemType
        
        item_repo = SQLAlchemyItemMasterRepository(client.app.state.db_session)
        sku_repo = SQLAlchemySKURepository(client.app.state.db_session)
        
        # Create existing item and SKU
        existing_item = ItemMaster(
            item_code="MIXED001",
            item_name="Mixed Test Item",
            category_id=test_data["category"].id,
            item_type=ItemType.PRODUCT
        )
        await item_repo.create(existing_item)
        
        existing_sku = SKU(
            sku_code="MIXED-SKU-001",
            sku_name="Mixed Test SKU",
            item_id=existing_item.id,
            sale_base_price=Decimal("50.00")
        )
        await sku_repo.create(existing_sku)
        
        # Create batch purchase with mixed items
        request_data = {
            "supplier_id": str(test_data["supplier"].id),
            "location_id": str(test_data["location"].id),
            "purchase_date": date.today().isoformat(),
            "items": [
                {
                    "sku_id": str(existing_sku.id),
                    "quantity": 3,
                    "unit_cost": 40.00,
                    "notes": "Existing item restock"
                },
                {
                    "new_item_master": {
                        "item_name": "New Mixed Item",
                        "category_id": str(test_data["category"].id),
                    },
                    "new_sku": {
                        "sku_name": "New Mixed SKU",
                        "sale_base_price": 75.0
                    },
                    "quantity": 2,
                    "unit_cost": 60.00,
                    "notes": "New item creation"
                }
            ]
        }
        
        response = await client.post("/api/v1/transactions/purchases/batch", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify mix of created and existing entities
        assert len(data["created_item_masters"]) == 1
        assert len(data["created_skus"]) == 1
        assert len(data["used_existing_skus"]) == 1
        assert data["total_items"] == 2
        
        # Verify total calculation
        expected_total = (3 * 40.00) + (2 * 60.00)  # 120 + 120 = 240
        assert data["total_amount"] == expected_total
    
    async def test_batch_purchase_auto_code_generation(self, client, test_data):
        """Test automatic code generation for item masters and SKUs."""
        request_data = {
            "supplier_id": str(test_data["supplier"].id),
            "location_id": str(test_data["location"].id),
            "purchase_date": date.today().isoformat(),
            "auto_generate_codes": True,
            "validate_only": True,  # Just test validation to see generated codes
            "items": [
                {
                    "new_item_master": {
                        "item_name": "MacBook Pro 14-inch",
                        "category_id": str(test_data["category"].id),
                    },
                    "new_sku": {
                        "sku_name": "MacBook Pro 14-inch M3 16GB/512GB",
                        "sale_base_price": 1999.0
                    },
                    "quantity": 1,
                    "unit_cost": 1600.00
                }
            ]
        }
        
        response = await client.post("/api/v1/transactions/purchases/batch/validate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify codes were generated
        assert len(data["generated_item_codes"]) == 1
        assert len(data["generated_sku_codes"]) == 1
        
        # Verify generated codes contain elements from the names
        item_code = data["generated_item_codes"][0]
        sku_code = data["generated_sku_codes"][0]
        
        assert "MACBOOK" in item_code or "MACBOOKPRO" in item_code
        assert "MACBOOK" in sku_code or "MACBOOKPRO" in sku_code
    
    async def test_batch_purchase_error_rollback(self, client, test_data):
        """Test that entities are rolled back on error."""
        # Create a request that will fail at SKU creation step
        # by using an invalid item master reference
        request_data = {
            "supplier_id": str(test_data["supplier"].id),
            "location_id": str(test_data["location"].id),
            "purchase_date": date.today().isoformat(),
            "items": [
                {
                    "new_item_master": {
                        "item_name": "Rollback Test Item",
                        "category_id": str(test_data["category"].id),
                    },
                    "new_sku": {
                        "sku_name": "Rollback Test SKU",
                        "sku_code": "DUPLICATE_CODE",  # We'll create this first to cause conflict
                        "sale_base_price": 100.0
                    },
                    "quantity": 1,
                    "unit_cost": 80.00
                }
            ]
        }
        
        # First create a SKU with the duplicate code
        from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
        from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
        from src.domain.entities.item_master import ItemMaster
        from src.domain.entities.sku import SKU
        from src.domain.value_objects.item_type import ItemType
        
        item_repo = SQLAlchemyItemMasterRepository(client.app.state.db_session)
        sku_repo = SQLAlchemySKURepository(client.app.state.db_session)
        
        existing_item = ItemMaster(
            item_code="DUPLICATE_ITEM",
            item_name="Duplicate Item",
            category_id=test_data["category"].id,
            item_type=ItemType.PRODUCT
        )
        await item_repo.create(existing_item)
        
        duplicate_sku = SKU(
            sku_code="DUPLICATE_CODE",
            sku_name="Duplicate SKU",
            item_id=existing_item.id
        )
        await sku_repo.create(duplicate_sku)
        
        # Now try the batch purchase which should fail
        response = await client.post("/api/v1/transactions/purchases/batch", json=request_data)
        
        assert response.status_code == 400
        
        # Verify that no item masters were left behind
        # (they should have been rolled back due to SKU creation failure)
        items = await item_repo.list()
        rollback_items = [item for item in items if "Rollback Test" in item.item_name]
        assert len(rollback_items) == 0  # Should be rolled back