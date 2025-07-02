import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient

from src.domain.entities.customer import Customer
from src.domain.entities.location import Location
from src.domain.entities.category import Category
from src.domain.entities.brand import Brand
from src.domain.entities.item_master import ItemMaster
from src.domain.entities.sku import SKU
from src.domain.entities.inventory_unit import InventoryUnit
from src.domain.entities.stock_level import StockLevel
from src.domain.entities.transaction_header import TransactionHeader
from src.domain.entities.transaction_line import TransactionLine

from src.domain.value_objects.customer_type import CustomerType
from src.domain.entities.location import LocationType
from src.domain.value_objects.transaction_type import TransactionType, TransactionStatus, LineItemType
from src.domain.value_objects.item_type import ItemType, ConditionGrade, InventoryStatus
from src.domain.value_objects.rental_return_type import ReturnType, ReturnStatus

from src.infrastructure.repositories.customer_repository import SQLAlchemyCustomerRepository
from src.infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
from src.infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository
from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
from src.infrastructure.repositories.inventory_unit_repository import SQLAlchemyInventoryUnitRepository
from src.infrastructure.repositories.stock_level_repository import SQLAlchemyStockLevelRepository
from src.infrastructure.repositories.transaction_header_repository import SQLAlchemyTransactionHeaderRepository
from src.infrastructure.repositories.transaction_line_repository import SQLAlchemyTransactionLineRepository


@pytest.mark.integration
class TestRentalReturnAPI:
    """Integration tests for Rental Return API endpoints."""
    
    @pytest.fixture
    async def setup_test_data(self, db_session):
        """Set up test data for rental return tests."""
        # Create customer
        customer_repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="Test",
            last_name="Customer"
        )
        customer = await customer_repo.create(customer)
        
        # Create location
        location_repo = SQLAlchemyLocationRepository(db_session)
        location = Location(
            location_code="LOC001",
            location_name="Main Store",
            location_type=LocationType.STORE,
            address="123 Main St",
            city="Test City",
            state="TC",
            country="USA"
        )
        location = await location_repo.create(location)
        
        # Create category
        category_repo = SQLAlchemyCategoryRepository(db_session)
        category = Category(
            category_name="Electronics"
        )
        category = await category_repo.create(category)
        
        # Create brand
        brand_repo = SQLAlchemyBrandRepository(db_session)
        brand = Brand(
            brand_name="Apple Inc.",
            brand_code="APPLE",
            description="Apple products"
        )
        brand = await brand_repo.create(brand)
        
        # Create item master
        item_repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="LAPTOP001",
            item_name="MacBook Pro 13\"",
            category_id=category.id,
            brand_id=brand.id,
            description="MacBook Pro 13 inch laptop",
            is_serialized=True
        )
        item = await item_repo.create(item)
        
        # Create SKU
        sku_repo = SQLAlchemySKURepository(db_session)
        sku = SKU(
            sku_code="LAPTOP001-NEW",
            sku_name="Laptop Model A",
            item_id=item.id,
            is_rentable=True,
            is_saleable=True,
            rental_base_price=Decimal("50.00"),
            sale_base_price=Decimal("1500.00")
        )
        sku = await sku_repo.create(sku)
        
        # Create inventory units
        inventory_repo = SQLAlchemyInventoryUnitRepository(db_session)
        inventory_units = []
        for i in range(3):
            unit = InventoryUnit(
                inventory_code=f"INV{i+1:03d}",
                sku_id=sku.id,
                location_id=location.id,
                serial_number=f"SN{i+1:03d}",
                condition_grade=ConditionGrade.A,
                current_status=InventoryStatus.AVAILABLE_RENT
            )
            unit = await inventory_repo.create(unit)
            inventory_units.append(unit)
        
        # Create stock level
        stock_repo = SQLAlchemyStockLevelRepository(db_session)
        stock_level = StockLevel(
            sku_id=sku.id,
            location_id=location.id,
            quantity_on_hand=3,
            quantity_available=3,
            quantity_reserved=0
        )
        stock_level = await stock_repo.create(stock_level)
        
        # Create rental transaction
        transaction_repo = SQLAlchemyTransactionHeaderRepository(db_session)
        transaction = TransactionHeader(
            transaction_number="TXN001",
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime.now(),
            customer_id=customer.id,
            location_id=location.id,
            status=TransactionStatus.IN_PROGRESS,
            rental_start_date=date.today(),
            rental_end_date=date.today() + timedelta(days=7),
            deposit_amount=Decimal("200.00")
        )
        transaction = await transaction_repo.create(transaction)
        
        # Create transaction lines
        line_repo = SQLAlchemyTransactionLineRepository(db_session)
        transaction_lines = []
        for i, unit in enumerate(inventory_units[:2]):  # Rent 2 units
            line = TransactionLine(
                transaction_id=transaction.id,
                line_number=i+1,
                line_type=LineItemType.PRODUCT,
                inventory_unit_id=unit.id,
                sku_id=sku.id,
                quantity=Decimal("1"),
                unit_price=sku.rental_base_price,
                line_total=sku.rental_base_price
            )
            line = await line_repo.create(line)
            transaction_lines.append(line)
            
            # Update inventory status to rented
            unit.update_status(InventoryStatus.RENTED, "system")
            await inventory_repo.update(unit.id, unit)
        
        return {
            'customer': customer,
            'location': location,
            'transaction': transaction,
            'transaction_lines': transaction_lines,
            'inventory_units': inventory_units,
            'sku': sku
        }
    
    async def test_initiate_return_success(self, async_client: AsyncClient, setup_test_data):
        """Test successful return initiation."""
        test_data = setup_test_data
        
        # Prepare request data
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1,
                    "notes": "Good condition"
                },
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][1].inventory_unit_id),
                    "quantity": 1,
                    "notes": "Minor wear"
                }
            ],
            "return_location_id": str(test_data['location'].id),
            "return_type": "FULL",
            "notes": "Complete return",
            "processed_by": "clerk001"
        }
        
        # Make request
        response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["rental_transaction_id"] == str(test_data['transaction'].id)
        assert data["return_status"] == "INITIATED"
        assert data["return_type"] == "FULL"
        assert len(data["lines"]) == 2
    
    async def test_list_returns(self, async_client: AsyncClient, setup_test_data):
        """Test listing rental returns."""
        test_data = setup_test_data
        
        # First create a return
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        
        # Now list returns
        response = await async_client.get("/api/v1/rental-returns/")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["returns"]) >= 1
        assert data["skip"] == 0
        assert data["limit"] == 100
    
    async def test_get_return_by_id(self, async_client: AsyncClient, setup_test_data):
        """Test getting a specific return by ID."""
        test_data = setup_test_data
        
        # Create a return first
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Get the return by ID
        response = await async_client.get(f"/api/v1/rental-returns/{created_return['id']}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_return["id"]
        assert data["rental_transaction_id"] == str(test_data['transaction'].id)
    
    async def test_process_partial_return(self, async_client: AsyncClient, setup_test_data):
        """Test processing a partial return."""
        test_data = setup_test_data
        
        # Create a partial return first
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "return_type": "PARTIAL",
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Process the partial return
        line_id = created_return["lines"][0]["id"]
        process_data = {
            "line_updates": [
                {
                    "line_id": line_id,
                    "returned_quantity": 1,
                    "condition_grade": "A",
                    "notes": "Excellent condition"
                }
            ],
            "process_inventory": True,
            "updated_by": "processor001"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-returns/{created_return['id']}/process-partial",
            json=process_data
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_return["id"]
        # Should still be partial since we only have one line
        assert data["return_status"] in ["INITIATED", "PARTIALLY_COMPLETED"]
    
    async def test_validate_partial_return(self, async_client: AsyncClient, setup_test_data):
        """Test validating a partial return proposal."""
        test_data = setup_test_data
        
        # Create a return first
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                },
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][1].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Validate partial return
        line_ids = [line["id"] for line in created_return["lines"]]
        proposed_quantities = {line_ids[0]: 1, line_ids[1]: 1}
        
        response = await async_client.post(
            f"/api/v1/rental-returns/{created_return['id']}/validate-partial",
            json=proposed_quantities
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["summary"]["lines_being_returned"] == 2
        assert data["summary"]["total_proposed_quantity"] == 2
    
    async def test_calculate_late_fee(self, async_client: AsyncClient, setup_test_data):
        """Test calculating late fees."""
        test_data = setup_test_data
        
        # Create a return with past expected return date (simulate late return)
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Calculate late fee
        late_fee_data = {
            "daily_late_fee_rate": 5.00,
            "use_percentage_of_rental_rate": False,
            "updated_by": "system"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-returns/{created_return['id']}/calculate-late-fee",
            json=late_fee_data
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "is_late" in data
        assert "total_late_fee" in data
        assert data["return_id"] == created_return["id"]
    
    async def test_assess_damage(self, async_client: AsyncClient, setup_test_data):
        """Test damage assessment."""
        test_data = setup_test_data
        
        # Create a return first
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Assess damage
        line_id = created_return["lines"][0]["id"]
        assessment_data = {
            "inspector_id": "inspector001",
            "line_assessments": [
                {
                    "line_id": line_id,
                    "condition_grade": "C",
                    "damage_description": "Minor scratches on surface",
                    "estimated_repair_cost": 25.00,
                    "damage_photos": ["photo1.jpg", "photo2.jpg"],
                    "cleaning_required": False,
                    "replacement_required": False
                }
            ],
            "general_notes": "Inspection completed successfully"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-returns/{created_return['id']}/assess-damage",
            json=assessment_data
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["return_id"] == created_return["id"]
        assert data["inspector_id"] == "inspector001"
        assert data["inspection_status"] == "IN_PROGRESS"
    
    async def test_get_inspection_summary(self, async_client: AsyncClient, setup_test_data):
        """Test getting inspection summary."""
        test_data = setup_test_data
        
        # Create a return first
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Get inspection summary
        response = await async_client.get(
            f"/api/v1/rental-returns/{created_return['id']}/inspection-summary"
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["return_id"] == created_return["id"]
        assert "has_inspections" in data
        assert "total_reports" in data
    
    async def test_finalize_return(self, async_client: AsyncClient, setup_test_data):
        """Test finalizing a return."""
        test_data = setup_test_data
        
        # Create and process a return first
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Process the return first
        line_id = created_return["lines"][0]["id"]
        process_data = {
            "line_updates": [
                {
                    "line_id": line_id,
                    "returned_quantity": 1,
                    "condition_grade": "A",
                    "notes": "Good condition"
                }
            ],
            "updated_by": "processor001"
        }
        
        await async_client.post(
            f"/api/v1/rental-returns/{created_return['id']}/process-partial",
            json=process_data
        )
        
        # Finalize the return (force finalize to skip validation)
        finalize_data = {
            "finalized_by": "manager001",
            "force_finalize": True,
            "finalization_notes": "Manual finalization"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-returns/{created_return['id']}/finalize",
            json=finalize_data
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_return["id"]
        assert data["return_status"] == "COMPLETED"
        assert data["finalized_by"] == "manager001"
    
    async def test_get_finalization_preview(self, async_client: AsyncClient, setup_test_data):
        """Test getting finalization preview."""
        test_data = setup_test_data
        
        # Create a return first
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Get finalization preview
        response = await async_client.get(
            f"/api/v1/rental-returns/{created_return['id']}/finalization-preview"
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["return_id"] == created_return["id"]
        assert "can_finalize" in data
        assert "fee_totals" in data
        assert "inventory_changes" in data
    
    async def test_get_deposit_preview(self, async_client: AsyncClient, setup_test_data):
        """Test getting deposit release preview."""
        test_data = setup_test_data
        
        # Create and finalize a return first
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Get deposit preview
        response = await async_client.get(
            f"/api/v1/rental-returns/{created_return['id']}/deposit-preview"
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["return_id"] == created_return["id"]
        assert "can_release_deposit" in data
        assert "deposit_calculation" in data
    
    async def test_get_outstanding_returns(self, async_client: AsyncClient, setup_test_data):
        """Test getting outstanding returns."""
        test_data = setup_test_data
        
        # Create a return that's not completed
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        
        # Get outstanding returns
        response = await async_client.get("/api/v1/rental-returns/outstanding")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["returns"]) >= 1
    
    async def test_get_status_counts(self, async_client: AsyncClient, setup_test_data):
        """Test getting return status counts."""
        test_data = setup_test_data
        
        # Create a return
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        
        # Get status counts
        response = await async_client.get("/api/v1/rental-returns/statistics/status-counts")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "status_counts" in data
        assert isinstance(data["status_counts"], dict)
    
    async def test_get_return_fees(self, async_client: AsyncClient, setup_test_data):
        """Test getting return fees."""
        test_data = setup_test_data
        
        # Create a return
        request_data = {
            "rental_transaction_id": str(test_data['transaction'].id),
            "return_date": date.today().isoformat(),
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['transaction_lines'][0].inventory_unit_id),
                    "quantity": 1
                }
            ],
            "processed_by": "clerk001"
        }
        
        create_response = await async_client.post("/api/v1/rental-returns/", json=request_data)
        assert create_response.status_code == 201
        created_return = create_response.json()
        
        # Get return fees
        response = await async_client.get(f"/api/v1/rental-returns/{created_return['id']}/fees")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["return_id"] == created_return["id"]
        assert "fees" in data
    
    async def test_error_handling_not_found(self, async_client: AsyncClient):
        """Test error handling for non-existent return."""
        non_existent_id = str(uuid4())
        
        response = await async_client.get(f"/api/v1/rental-returns/{non_existent_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    async def test_error_handling_invalid_data(self, async_client: AsyncClient):
        """Test error handling for invalid request data."""
        invalid_data = {
            "rental_transaction_id": "invalid-uuid",
            "return_date": "invalid-date",
            "return_items": []
        }
        
        response = await async_client.post("/api/v1/rental-returns/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error