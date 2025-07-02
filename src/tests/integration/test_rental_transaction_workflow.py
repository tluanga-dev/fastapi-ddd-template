import pytest
from httpx import AsyncClient
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.value_objects.customer_type import CustomerType
from src.domain.value_objects.item_type import ItemType, ConditionGrade, InventoryStatus
from src.domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod
)
from src.domain.entities.location import LocationType


class TestRentalTransactionWorkflow:
    """Integration tests for complete rental transaction workflow."""
    
    @pytest.fixture
    async def setup_rental_test_data(self, db_session):
        """Set up test data for rental workflow testing."""
        from src.domain.entities.customer import Customer
        from src.domain.entities.location import Location
        from src.domain.entities.category import Category
        from src.domain.entities.brand import Brand
        from src.domain.entities.item_master import ItemMaster
        from src.domain.entities.sku import SKU
        from src.domain.entities.inventory_unit import InventoryUnit
        from src.domain.entities.stock_level import StockLevel
        
        from src.infrastructure.repositories.customer_repository import SQLAlchemyCustomerRepository
        from src.infrastructure.repositories.location_repository_impl import SQLAlchemyLocationRepository
        from src.infrastructure.repositories.category_repository_impl import SQLAlchemyCategoryRepository
        from src.infrastructure.repositories.brand_repository import SQLAlchemyBrandRepository
        from src.infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
        from src.infrastructure.repositories.sku_repository import SQLAlchemySKURepository
        from src.infrastructure.repositories.inventory_unit_repository import SQLAlchemyInventoryUnitRepository
        from src.infrastructure.repositories.stock_level_repository import SQLAlchemyStockLevelRepository
        
        # Create repositories
        customer_repo = SQLAlchemyCustomerRepository(db_session)
        location_repo = SQLAlchemyLocationRepository(db_session)
        category_repo = SQLAlchemyCategoryRepository(db_session)
        brand_repo = SQLAlchemyBrandRepository(db_session)
        item_repo = SQLAlchemyItemMasterRepository(db_session)
        sku_repo = SQLAlchemySKURepository(db_session)
        inventory_repo = SQLAlchemyInventoryUnitRepository(db_session)
        stock_repo = SQLAlchemyStockLevelRepository(db_session)
        
        # Create customer
        customer = Customer(
            customer_code="RENTAL_CUST_001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Rental"
        )
        customer = await customer_repo.create(customer)
        
        # Create location
        location = Location(
            location_code="RENTAL_STORE",
            location_name="Rental Store",
            location_type=LocationType.STORE,
            address="123 Rental St",
            city="Rental City",
            state="RC",
            country="USA",
            postal_code="12345"
        )
        location = await location_repo.create(location)
        
        # Create category
        category = Category(
            category_name="Rental Equipment"
        )
        category = await category_repo.create(category)
        
        # Create brand
        brand = Brand(
            brand_name="RentalBrand",
            brand_code="RBRAND"
        )
        brand = await brand_repo.create(brand)
        
        # Create item master
        item = ItemMaster(
            item_code="RENTAL_LAPTOP",
            item_name="Rental Laptop",
            item_type=ItemType.PRODUCT,
            category_id=category.id,
            brand_id=brand.id,
            is_serialized=True
        )
        item = await item_repo.create(item)
        
        # Create SKU
        sku = SKU(
            sku_code="LAPTOP_RENTAL_SKU",
            sku_name="Laptop for Rental",
            item_id=item.id,
            is_rentable=True,
            is_saleable=False,
            min_rental_days=1,
            max_rental_days=30,
            rental_base_price=Decimal("50.00")
        )
        sku = await sku_repo.create(sku)
        
        # Create inventory units
        units = []
        for i in range(3):
            unit = InventoryUnit(
                inventory_code=f"RENTAL_UNIT_{i+1:03d}",
                sku_id=sku.id,
                location_id=location.id,
                serial_number=f"SERIAL_{i+1:03d}",
                condition_grade=ConditionGrade.A,
                current_status=InventoryStatus.AVAILABLE_RENT
            )
            unit = await inventory_repo.create(unit)
            units.append(unit)
        
        # Create stock level
        stock = StockLevel(
            sku_id=sku.id,
            location_id=location.id,
            quantity_on_hand=3,
            quantity_available=3,
            quantity_reserved=0
        )
        stock = await stock_repo.create(stock)
        
        return {
            "customer": customer,
            "location": location,
            "category": category,
            "brand": brand,
            "item": item,
            "sku": sku,
            "units": units,
            "stock": stock
        }
    
    async def test_complete_rental_workflow(self, async_client: AsyncClient, setup_rental_test_data):
        """Test complete rental workflow from booking to return."""
        test_data = setup_rental_test_data
        
        # 1. Create rental booking
        booking_data = {
            "customer_id": str(test_data["customer"].id),
            "location_id": str(test_data["location"].id),
            "items": [
                {
                    "sku_id": str(test_data["sku"].id),
                    "quantity": 2,
                    "rental_start_date": str(date.today()),
                    "rental_end_date": str(date.today() + timedelta(days=7))
                }
            ],
            "deposit_percentage": 30.0,
            "tax_rate": 8.25
        }
        
        response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        assert response.status_code == 201
        booking_result = response.json()
        transaction_id = booking_result["transaction"]["id"]
        
        # Verify booking details
        assert booking_result["transaction"]["status"] == TransactionStatus.DRAFT.value
        assert booking_result["transaction"]["payment_status"] == PaymentStatus.PENDING.value
        assert booking_result["transaction"]["rental_days"] == 8  # 7 days + 1
        
        # 2. Checkout rental (process payment)
        checkout_data = {
            "payment_amount": float(booking_result["transaction"]["deposit_amount"]),
            "payment_method": PaymentMethod.CREDIT_CARD.value,
            "payment_reference": "CARD_1234"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/checkout",
            json=checkout_data
        )
        assert response.status_code == 200
        checkout_result = response.json()
        
        # Verify checkout
        assert checkout_result["transaction"]["status"] in [
            TransactionStatus.CONFIRMED.value,
            TransactionStatus.IN_PROGRESS.value
        ]
        assert checkout_result["transaction"]["payment_status"] == PaymentStatus.PARTIALLY_PAID.value
        
        # 3. Process pickup
        # Get inventory units from booking
        response = await async_client.get(f"/api/v1/rental-transactions/{transaction_id}")
        assert response.status_code == 200
        transaction_details = response.json()
        
        # Create pickup request for 2 units
        pickup_data = {
            "pickup_items": [
                {
                    "inventory_unit_id": str(test_data["units"][0].id),
                    "serial_number": test_data["units"][0].serial_number,
                    "condition_notes": "Good condition",
                    "accessories_included": ["Power adapter", "Carrying case"]
                },
                {
                    "inventory_unit_id": str(test_data["units"][1].id),
                    "serial_number": test_data["units"][1].serial_number,
                    "condition_notes": "Excellent condition",
                    "accessories_included": ["Power adapter", "Carrying case"]
                }
            ],
            "pickup_person_name": "John Rental",
            "pickup_person_id": "DL123456"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/pickup",
            json=pickup_data
        )
        assert response.status_code == 200
        pickup_result = response.json()
        
        # Verify pickup
        assert pickup_result["transaction"]["status"] == TransactionStatus.IN_PROGRESS.value
        assert len(pickup_result["inspection_reports"]) == 2
        
        # 4. Extend rental period
        new_end_date = date.today() + timedelta(days=10)
        extension_data = {
            "new_end_date": str(new_end_date),
            "payment_amount": 150.00,
            "payment_method": PaymentMethod.CREDIT_CARD.value,
            "extension_notes": "Customer requested 3 more days"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/extend",
            json=extension_data
        )
        assert response.status_code == 200
        extension_result = response.json()
        
        # Verify extension
        assert extension_result["transaction"]["rental_end_date"] == str(new_end_date)
        assert extension_result["extension_summary"]["extension_days"] == 3
        
        # 5. Complete return
        return_data = {
            "return_items": [
                {
                    "inventory_unit_id": str(test_data["units"][0].id),
                    "condition_grade": ConditionGrade.A.value,
                    "is_damaged": False
                },
                {
                    "inventory_unit_id": str(test_data["units"][1].id),
                    "condition_grade": ConditionGrade.B.value,
                    "is_damaged": True,
                    "damage_description": "Minor scratch on surface",
                    "damage_photos": ["photo1.jpg"]
                }
            ],
            "is_partial_return": False,
            "damage_fee_percentage": 20.0,
            "process_refund": True,
            "refund_method": PaymentMethod.CREDIT_CARD.value
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/return",
            json=return_data
        )
        assert response.status_code == 200
        return_result = response.json()
        
        # Verify return
        assert return_result["transaction"]["status"] == TransactionStatus.COMPLETED.value
        assert return_result["return_summary"]["items_returned"] == 2
        assert return_result["return_summary"]["damage_fees"] > 0  # Due to damaged item
    
    async def test_rental_booking_validation(self, async_client: AsyncClient, setup_rental_test_data):
        """Test rental booking validation."""
        test_data = setup_rental_test_data
        
        # Test with invalid rental period (too short)
        booking_data = {
            "customer_id": str(test_data["customer"].id),
            "location_id": str(test_data["location"].id),
            "items": [
                {
                    "sku_id": str(test_data["sku"].id),
                    "quantity": 1,
                    "rental_start_date": str(date.today()),
                    "rental_end_date": str(date.today())  # Same day (0 days)
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        assert response.status_code == 400
        
        # Test with quantity exceeding availability
        booking_data["items"][0]["quantity"] = 10  # We only have 3 units
        booking_data["items"][0]["rental_end_date"] = str(date.today() + timedelta(days=7))
        
        response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        assert response.status_code == 400
    
    async def test_rental_cancellation(self, async_client: AsyncClient, setup_rental_test_data):
        """Test rental cancellation with refund."""
        test_data = setup_rental_test_data
        
        # Create and checkout a booking
        booking_data = {
            "customer_id": str(test_data["customer"].id),
            "location_id": str(test_data["location"].id),
            "items": [
                {
                    "sku_id": str(test_data["sku"].id),
                    "quantity": 1,
                    "rental_start_date": str(date.today() + timedelta(days=7)),
                    "rental_end_date": str(date.today() + timedelta(days=14))
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        assert response.status_code == 201
        booking_result = response.json()
        transaction_id = booking_result["transaction"]["id"]
        
        # Checkout with full payment
        checkout_data = {
            "payment_amount": float(booking_result["transaction"]["total_amount"]),
            "payment_method": PaymentMethod.CREDIT_CARD.value,
            "collect_full_payment": True
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/checkout",
            json=checkout_data
        )
        assert response.status_code == 200
        
        # Cancel booking
        cancel_data = {
            "cancellation_reason": "Customer changed plans",
            "refund_percentage": 100.0,  # Full refund
            "refund_method": PaymentMethod.CREDIT_CARD.value
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/cancel",
            json=cancel_data
        )
        assert response.status_code == 200
        cancel_result = response.json()
        
        # Verify cancellation
        assert cancel_result["transaction"]["status"] == TransactionStatus.CANCELLED.value
        assert cancel_result["transaction"]["payment_status"] == PaymentStatus.REFUNDED.value
        assert cancel_result["refund_summary"]["refund_percentage"] == 100.0
    
    async def test_rental_availability_check(self, async_client: AsyncClient, setup_rental_test_data):
        """Test rental availability checking."""
        test_data = setup_rental_test_data
        
        # Check availability
        availability_data = {
            "sku_id": str(test_data["sku"].id),
            "location_id": str(test_data["location"].id),
            "rental_start_date": str(date.today()),
            "rental_end_date": str(date.today() + timedelta(days=7)),
            "quantity": 2
        }
        
        response = await async_client.post(
            "/api/v1/rental-transactions/availability/check",
            json=availability_data
        )
        assert response.status_code == 200
        availability_result = response.json()
        
        # Verify availability
        assert availability_result["is_available"] is True
        assert availability_result["available_quantity"] >= 2
        assert len(availability_result["available_units"]) >= 2
    
    async def test_partial_return(self, async_client: AsyncClient, setup_rental_test_data):
        """Test partial return scenario."""
        test_data = setup_rental_test_data
        
        # Create booking for 2 items
        booking_data = {
            "customer_id": str(test_data["customer"].id),
            "location_id": str(test_data["location"].id),
            "items": [
                {
                    "sku_id": str(test_data["sku"].id),
                    "quantity": 2,
                    "rental_start_date": str(date.today()),
                    "rental_end_date": str(date.today() + timedelta(days=7))
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/rental-transactions/bookings",
            json=booking_data
        )
        assert response.status_code == 201
        transaction_id = response.json()["transaction"]["id"]
        
        # Checkout and pickup
        checkout_data = {
            "payment_amount": float(response.json()["transaction"]["deposit_amount"]),
            "payment_method": PaymentMethod.CASH.value
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/checkout",
            json=checkout_data
        )
        assert response.status_code == 200
        
        pickup_data = {
            "pickup_items": [
                {
                    "inventory_unit_id": str(test_data["units"][0].id),
                    "serial_number": test_data["units"][0].serial_number
                },
                {
                    "inventory_unit_id": str(test_data["units"][1].id),
                    "serial_number": test_data["units"][1].serial_number
                }
            ],
            "pickup_person_name": "John Rental"
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/pickup",
            json=pickup_data
        )
        assert response.status_code == 200
        
        # Return only 1 item (partial return)
        return_data = {
            "return_items": [
                {
                    "inventory_unit_id": str(test_data["units"][0].id),
                    "condition_grade": ConditionGrade.A.value,
                    "is_damaged": False
                }
            ],
            "is_partial_return": True,
            "process_refund": False  # Don't refund yet since it's partial
        }
        
        response = await async_client.post(
            f"/api/v1/rental-transactions/{transaction_id}/return",
            json=return_data
        )
        assert response.status_code == 200
        partial_return_result = response.json()
        
        # Verify partial return
        assert partial_return_result["return_summary"]["items_returned"] == 1
        assert partial_return_result["return_summary"]["is_complete"] is False
        
        # Transaction should still be in progress
        assert partial_return_result["transaction"]["status"] == TransactionStatus.IN_PROGRESS.value