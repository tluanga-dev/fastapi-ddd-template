import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.customer import Customer
from src.domain.entities.location import Location
from src.domain.entities.category import Category
from src.domain.entities.brand import Brand
from src.domain.entities.item_master import ItemMaster
from src.domain.entities.sku import SKU
from src.domain.entities.inventory_unit import InventoryUnit
from src.domain.entities.stock_level import StockLevel

from src.domain.value_objects.customer_type import CustomerType, BlacklistStatus
from src.domain.entities.location import LocationType
from src.domain.value_objects.item_type import InventoryStatus, ConditionGrade
from src.domain.value_objects.transaction_type import TransactionType, TransactionStatus, PaymentStatus

from src.infrastructure.repositories.customer_repository import SQLAlchemyCustomerRepository
from src.infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
from src.infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository
from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
from src.infrastructure.repositories.inventory_unit_repository import SQLAlchemyInventoryUnitRepository
from src.infrastructure.repositories.stock_level_repository import SQLAlchemyStockLevelRepository


@pytest.mark.integration
class TestRentalTransactionAPI:
    """Integration tests for Rental Transaction API endpoints."""
    
    @pytest.fixture
    async def setup_test_data(self, db_session: AsyncSession):
        """Set up test data for rental transaction tests."""
        # Create customer
        customer_repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="Test",
            last_name="Customer",
            blacklist_status=BlacklistStatus.CLEAR
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
            brand_name="TestBrand",
            brand_code="TB001",
            description="Test Brand"
        )
        brand = await brand_repo.create(brand)
        
        # Create item master
        item_repo = SQLAlchemyItemMasterRepository(db_session)
        item = ItemMaster(
            item_code="LAPTOP001",
            item_name="Test Laptop",
            category_id=category.id,
            brand_id=brand.id,
            description="Test laptop for rental",
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
            sale_base_price=Decimal("1500.00"),
            min_rental_days=1,
            max_rental_days=30
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
            quantity_available=3
        )
        stock_level = await stock_repo.create(stock_level)
        
        return {
            'customer': customer,
            'location': location,
            'sku': sku,
            'inventory_units': inventory_units,
            'stock_level': stock_level
        }
    
    @pytest.mark.asyncio
    async def test_create_rental_booking(self, async_client: AsyncClient, setup_test_data):
        """Test creating a rental booking."""
        test_data = setup_test_data
        
        # Prepare request data
        booking_data = {
            "customer_id": str(test_data['customer'].id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 2,
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": (date.today() + timedelta(days=1)).isoformat(),
            "rental_end_date": (date.today() + timedelta(days=8)).isoformat(),
            "deposit_percentage": "30.00",
            "tax_rate": "8.25",
            "notes": "Test rental booking",
            "created_by": "clerk001"
        }
        
        # Make request
        response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == str(test_data['customer'].id)
        assert data["transaction_type"] == "RENTAL"
        assert data["status"] == "PENDING"
        assert len(data["lines"]) == 1
        assert data["lines"][0]["quantity"] == "2.00"
        assert float(data["deposit_amount"]) > 0
        assert float(data["tax_amount"]) > 0
    
    @pytest.mark.asyncio
    async def test_create_booking_insufficient_inventory(self, async_client: AsyncClient, setup_test_data):
        """Test creating booking with insufficient inventory."""
        test_data = setup_test_data
        
        # Try to book more units than available
        booking_data = {
            "customer_id": str(test_data['customer'].id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 5,  # More than available (3)
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": (date.today() + timedelta(days=1)).isoformat(),
            "rental_end_date": (date.today() + timedelta(days=8)).isoformat(),
            "created_by": "clerk001"
        }
        
        response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        
        assert response.status_code == 400
        assert "Insufficient inventory" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_checkout_rental(self, async_client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test checkout process for rental."""
        test_data = setup_test_data
        
        # First create a booking
        booking_data = {
            "customer_id": str(test_data['customer'].id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 1,
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": (date.today() + timedelta(days=1)).isoformat(),
            "rental_end_date": (date.today() + timedelta(days=8)).isoformat(),
            "created_by": "clerk001"
        }
        
        booking_response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        assert booking_response.status_code == 201
        booking = booking_response.json()
        
        # Checkout the booking
        checkout_data = {
            "payment_method": "CASH",
            "payment_amount": booking["total_amount"],
            "payment_reference": "CASH001",
            "processed_by": "cashier001"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/checkout",
            json=checkout_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CHECKED_OUT"
        assert data["payment_status"] == "PAID"
        assert float(data["paid_amount"]) == float(booking["total_amount"])
    
    @pytest.mark.asyncio
    async def test_pickup_rental(self, async_client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test rental pickup process."""
        test_data = setup_test_data
        
        # Create and checkout a booking
        booking_data = {
            "customer_id": str(test_data['customer'].id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 1,
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=7)).isoformat(),
            "created_by": "clerk001"
        }
        
        booking_response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        booking = booking_response.json()
        
        # Checkout
        checkout_data = {
            "payment_method": "CASH",
            "payment_amount": booking["total_amount"],
            "processed_by": "cashier001"
        }
        
        await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/checkout",
            json=checkout_data
        )
        
        # Pickup
        pickup_data = {
            "pickup_items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "serial_numbers": [test_data['inventory_units'][0].serial_number],
                    "inspection_notes": "Good condition",
                    "photos": ["photo1.jpg"]
                }
            ],
            "processed_by": "warehouse001"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/pickup",
            json=pickup_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"
        assert data["actual_start_date"] is not None
    
    @pytest.mark.asyncio
    async def test_return_rental(self, async_client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test rental return process."""
        test_data = setup_test_data
        
        # Create, checkout and pickup a rental
        booking_data = {
            "customer_id": str(test_data['customer'].id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 1,
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=7)).isoformat(),
            "created_by": "clerk001"
        }
        
        booking_response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        booking = booking_response.json()
        
        # Checkout
        checkout_data = {
            "payment_method": "CASH",
            "payment_amount": booking["total_amount"],
            "processed_by": "cashier001"
        }
        
        await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/checkout",
            json=checkout_data
        )
        
        # Pickup
        pickup_data = {
            "pickup_items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "serial_numbers": [test_data['inventory_units'][0].serial_number],
                    "inspection_notes": "Good condition"
                }
            ],
            "processed_by": "warehouse001"
        }
        
        await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/pickup",
            json=pickup_data
        )
        
        # Return
        return_data = {
            "return_items": [
                {
                    "inventory_unit_id": str(test_data['inventory_units'][0].id),
                    "condition_grade": "A",
                    "inspection_notes": "Returned in good condition",
                    "photos": ["return_photo1.jpg"]
                }
            ],
            "late_fee_waived": True,
            "damage_fee": "0.00",
            "processed_by": "warehouse001"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/return",
            json=return_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["actual_return_date"] is not None
    
    @pytest.mark.asyncio
    async def test_extend_rental(self, async_client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test extending a rental."""
        test_data = setup_test_data
        
        # Create and checkout a booking
        booking_data = {
            "customer_id": str(test_data['customer'].id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 1,
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=7)).isoformat(),
            "created_by": "clerk001"
        }
        
        booking_response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        booking = booking_response.json()
        
        # Checkout
        checkout_data = {
            "payment_method": "CASH",
            "payment_amount": booking["total_amount"],
            "processed_by": "cashier001"
        }
        
        await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/checkout",
            json=checkout_data
        )
        
        # Extend rental
        extend_data = {
            "new_end_date": (date.today() + timedelta(days=14)).isoformat(),
            "extension_reason": "Customer needs more time",
            "payment_method": "CASH",
            "processed_by": "clerk001"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/extend",
            json=extend_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rental_end_date"] == extend_data["new_end_date"]
        assert float(data["total_amount"]) > float(booking["total_amount"])
    
    @pytest.mark.asyncio
    async def test_cancel_rental_booking(self, async_client: AsyncClient, setup_test_data):
        """Test cancelling a rental booking."""
        test_data = setup_test_data
        
        # Create a booking
        booking_data = {
            "customer_id": str(test_data['customer'].id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 1,
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": (date.today() + timedelta(days=7)).isoformat(),
            "rental_end_date": (date.today() + timedelta(days=14)).isoformat(),
            "created_by": "clerk001"
        }
        
        booking_response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        booking = booking_response.json()
        
        # Cancel booking
        cancel_data = {
            "cancellation_reason": "Customer changed mind",
            "refund_percentage": "100.00",
            "cancelled_by": "manager001"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/cancel",
            json=cancel_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"
        assert "Customer changed mind" in data["notes"]
    
    @pytest.mark.asyncio
    async def test_list_rental_transactions(self, async_client: AsyncClient, setup_test_data):
        """Test listing rental transactions."""
        test_data = setup_test_data
        
        # Create a few bookings
        for i in range(3):
            booking_data = {
                "customer_id": str(test_data['customer'].id),
                "location_id": str(test_data['location'].id),
                "items": [
                    {
                        "sku_id": str(test_data['sku'].id),
                        "quantity": 1,
                        "rental_days": 7,
                        "unit_price": "50.00"
                    }
                ],
                "rental_start_date": (date.today() + timedelta(days=i+1)).isoformat(),
                "rental_end_date": (date.today() + timedelta(days=i+8)).isoformat(),
                "created_by": "clerk001"
            }
            
            await async_client.post(
                "/api/v1/rental-transactions/bookings",
                json=booking_data
            )
        
        # List transactions
        response = await async_client.get("/api/v1/rental-transactions/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3
    
    @pytest.mark.asyncio
    async def test_get_customer_rentals(self, async_client: AsyncClient, setup_test_data):
        """Test getting customer's rental history."""
        test_data = setup_test_data
        
        # Create a booking
        booking_data = {
            "customer_id": str(test_data['customer'].id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 1,
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=7)).isoformat(),
            "created_by": "clerk001"
        }
        
        await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        
        # Get customer rentals
        response = await async_client.get(
            f"/api/v1/rental-transactions/customer/{test_data['customer'].id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(t["customer_id"] == str(test_data['customer'].id) for t in data["items"])
    
    @pytest.mark.asyncio
    async def test_blacklisted_customer_cannot_rent(self, async_client: AsyncClient, db_session: AsyncSession, setup_test_data):
        """Test that blacklisted customers cannot rent."""
        test_data = setup_test_data
        
        # Update customer to blacklisted
        customer_repo = SQLAlchemyCustomerRepository(db_session)
        customer = test_data['customer']
        customer.blacklist_status = BlacklistStatus.BLACKLISTED
        customer.blacklist_reason = "Payment default"
        await customer_repo.update(customer.id, customer)
        
        # Try to create booking
        booking_data = {
            "customer_id": str(customer.id),
            "location_id": str(test_data['location'].id),
            "items": [
                {
                    "sku_id": str(test_data['sku'].id),
                    "quantity": 1,
                    "rental_days": 7,
                    "unit_price": "50.00"
                }
            ],
            "rental_start_date": date.today().isoformat(),
            "rental_end_date": (date.today() + timedelta(days=7)).isoformat(),
            "created_by": "clerk001"
        }
        
        response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        
        # Should fail at checkout, not booking
        assert response.status_code == 201
        booking = response.json()
        
        # Try to checkout - this should fail
        checkout_data = {
            "payment_method": "CASH",
            "payment_amount": booking["total_amount"],
            "processed_by": "cashier001"
        }
        
        checkout_response = await async_client.post(
            f"/api/v1/rental-transactions/{booking['id']}/checkout",
            json=checkout_data
        )
        
        assert checkout_response.status_code == 400
        assert "BLACKLISTED" in checkout_response.json()["detail"]