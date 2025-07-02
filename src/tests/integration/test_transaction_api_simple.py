import pytest
from httpx import AsyncClient
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import json

from src.domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod,
    LineItemType, RentalPeriodUnit
)


class TestTransactionAPISimple:
    """Simple integration tests for Transaction API endpoints without fixtures."""
    
    async def test_create_sale_transaction_invalid_customer(self, async_client: AsyncClient):
        """Test creating a sale transaction with invalid customer."""
        transaction_data = {
            "customer_id": str(uuid4()),  # Non-existent customer
            "location_id": str(uuid4()),  # Non-existent location
            "items": [
                {
                    "sku_id": str(uuid4()),
                    "quantity": 2,
                    "unit_price": 100.00,
                    "discount_percentage": 10
                }
            ],
            "discount_amount": 0,
            "tax_rate": 8.5,
            "auto_reserve": False
        }
        
        response = await async_client.post("/api/v1/transactions/sales", json=transaction_data)
        assert response.status_code == 400
        assert "Customer not found" in response.json()["detail"]
    
    async def test_create_sale_transaction_empty_items(self, async_client: AsyncClient):
        """Test creating a sale transaction with empty items."""
        transaction_data = {
            "customer_id": str(uuid4()),
            "location_id": str(uuid4()),
            "items": [],  # Empty items
            "discount_amount": 0,
            "tax_rate": 0,
            "auto_reserve": False
        }
        
        response = await async_client.post("/api/v1/transactions/sales", json=transaction_data)
        assert response.status_code == 400
        assert "At least one item is required" in response.json()["detail"]
    
    async def test_get_nonexistent_transaction(self, async_client: AsyncClient):
        """Test getting a non-existent transaction."""
        fake_id = str(uuid4())
        response = await async_client.get(f"/api/v1/transactions/{fake_id}")
        assert response.status_code == 404
        assert f"Transaction with id {fake_id} not found" in response.json()["detail"]
    
    async def test_get_transaction_by_invalid_number(self, async_client: AsyncClient):
        """Test getting a transaction by invalid number."""
        response = await async_client.get("/api/v1/transactions/number/INVALID-001")
        assert response.status_code == 404
        assert "Transaction with number INVALID-001 not found" in response.json()["detail"]
    
    async def test_list_transactions_empty(self, async_client: AsyncClient):
        """Test listing transactions when none exist."""
        response = await async_client.get("/api/v1/transactions/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["skip"] == 0
        assert data["limit"] == 100
    
    async def test_process_payment_invalid_transaction(self, async_client: AsyncClient):
        """Test processing payment for invalid transaction."""
        fake_id = str(uuid4())
        payment_data = {
            "payment_amount": 100.00,
            "payment_method": "CREDIT_CARD",
            "payment_reference": "CC-12345",
            "process_inventory": False
        }
        
        response = await async_client.post(
            f"/api/v1/transactions/{fake_id}/payment",
            json=payment_data
        )
        assert response.status_code == 400
        assert "Transaction not found" in response.json()["detail"]
    
    async def test_cancel_invalid_transaction(self, async_client: AsyncClient):
        """Test cancelling invalid transaction."""
        fake_id = str(uuid4())
        cancel_data = {
            "cancellation_reason": "Test cancel",
            "release_inventory": True
        }
        
        response = await async_client.post(
            f"/api/v1/transactions/{fake_id}/cancel",
            json=cancel_data
        )
        assert response.status_code == 400
        assert "Transaction not found" in response.json()["detail"]
    
    async def test_customer_summary_invalid_customer(self, async_client: AsyncClient):
        """Test getting summary for invalid customer."""
        fake_id = str(uuid4())
        response = await async_client.get(f"/api/v1/transactions/customer/{fake_id}/summary")
        assert response.status_code == 404
        assert f"Customer with id {fake_id} not found" in response.json()["detail"]
    
    async def test_create_rental_invalid_dates(self, async_client: AsyncClient):
        """Test creating rental with invalid dates."""
        transaction_data = {
            "customer_id": str(uuid4()),
            "location_id": str(uuid4()),
            "rental_start_date": str(date.today()),
            "rental_end_date": str(date.today() - timedelta(days=1)),  # End before start
            "items": [
                {
                    "sku_id": str(uuid4()),
                    "quantity": 1,
                    "rental_period_value": 7,
                    "rental_period_unit": "DAY"
                }
            ],
            "deposit_amount": 50.00,
            "discount_amount": 0,
            "tax_rate": 0,
            "auto_reserve": False
        }
        
        response = await async_client.post("/api/v1/transactions/rentals", json=transaction_data)
        assert response.status_code == 400
    
    async def test_overdue_rentals_empty(self, async_client: AsyncClient):
        """Test getting overdue rentals when none exist."""
        response = await async_client.get("/api/v1/transactions/rentals/overdue")
        assert response.status_code == 200
        assert response.json() == []
    
    async def test_daily_summary_empty(self, async_client: AsyncClient):
        """Test getting daily summary with no transactions."""
        start_date = str(date.today())
        end_date = str(date.today())
        
        response = await async_client.get(
            f"/api/v1/transactions/reports/daily?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        assert response.json() == []
    
    async def test_revenue_report_empty(self, async_client: AsyncClient):
        """Test getting revenue report with no transactions."""
        start_date = str(date.today())
        end_date = str(date.today())
        
        response = await async_client.get(
            f"/api/v1/transactions/reports/revenue?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        assert response.json() == []