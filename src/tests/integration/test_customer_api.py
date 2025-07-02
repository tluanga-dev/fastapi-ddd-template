import pytest
from uuid import UUID
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.customer import Customer
from src.domain.value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus
from src.infrastructure.repositories.customer_repository import SQLAlchemyCustomerRepository


@pytest.mark.integration
class TestCustomerAPI:
    """Integration tests for Customer API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_individual_customer(self, async_client: AsyncClient):
        """Test creating an individual customer."""
        customer_data = {
            "customer_code": "CUST001",
            "customer_type": "INDIVIDUAL",
            "first_name": "John",
            "last_name": "Doe",
            "tax_id": "123456789",
            "customer_tier": "SILVER",
            "credit_limit": "5000.00"
        }
        
        response = await async_client.post("/api/v1/customers/", json=customer_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_code"] == "CUST001"
        assert data["customer_type"] == "INDIVIDUAL"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["display_name"] == "John Doe"
        assert data["customer_tier"] == "SILVER"
        assert float(data["credit_limit"]) == 5000.00
        assert data["blacklist_status"] == "CLEAR"
        assert data["is_active"] is True
        assert "id" in data
        assert UUID(data["id"])  # Validate UUID format
    
    @pytest.mark.asyncio
    async def test_create_business_customer(self, async_client: AsyncClient):
        """Test creating a business customer."""
        customer_data = {
            "customer_code": "CUST002",
            "customer_type": "BUSINESS",
            "business_name": "ABC Corporation",
            "tax_id": "GST123456",
            "customer_tier": "GOLD",
            "credit_limit": "50000.00"
        }
        
        response = await async_client.post("/api/v1/customers/", json=customer_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_code"] == "CUST002"
        assert data["customer_type"] == "BUSINESS"
        assert data["business_name"] == "ABC Corporation"
        assert data["display_name"] == "ABC Corporation"
        assert data["customer_tier"] == "GOLD"
        assert float(data["credit_limit"]) == 50000.00
    
    @pytest.mark.asyncio
    async def test_create_customer_missing_required_fields(self, async_client: AsyncClient):
        """Test creating customer with missing required fields fails."""
        # Individual without first name
        customer_data = {
            "customer_code": "CUST003",
            "customer_type": "INDIVIDUAL",
            "last_name": "Doe"
        }
        
        response = await async_client.post("/api/v1/customers/", json=customer_data)
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()
        
        # Business without business name
        customer_data = {
            "customer_code": "CUST004",
            "customer_type": "BUSINESS"
        }
        
        response = await async_client.post("/api/v1/customers/", json=customer_data)
        assert response.status_code == 400
        assert "Business name is required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_customer_duplicate_code(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test creating customer with duplicate code fails."""
        # Create first customer
        repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="Jane",
            last_name="Smith"
        )
        await repo.create(customer)
        
        # Try to create duplicate
        customer_data = {
            "customer_code": "CUST001",
            "customer_type": "INDIVIDUAL",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = await async_client.post("/api/v1/customers/", json=customer_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_customer_by_id(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting customer by ID."""
        # Create customer
        repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        created_customer = await repo.create(customer)
        
        # Get by ID
        response = await async_client.get(f"/api/v1/customers/{created_customer.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(created_customer.id)
        assert data["customer_code"] == "CUST001"
        assert data["display_name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, async_client: AsyncClient):
        """Test getting non-existent customer returns 404."""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await async_client.get(f"/api/v1/customers/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_customer_by_code(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting customer by code."""
        # Create customer
        repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.BUSINESS,
            business_name="Test Corp"
        )
        await repo.create(customer)
        
        # Get by code
        response = await async_client.get("/api/v1/customers/code/CUST001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["customer_code"] == "CUST001"
        assert data["business_name"] == "Test Corp"
    
    @pytest.mark.asyncio
    async def test_list_customers(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing customers with pagination."""
        # Create multiple customers
        repo = SQLAlchemyCustomerRepository(db_session)
        for i in range(5):
            customer = Customer(
                customer_code=f"CUST{i:03d}",
                customer_type=CustomerType.INDIVIDUAL,
                first_name=f"User{i}",
                last_name="Test",
                customer_tier=CustomerTier.BRONZE if i < 3 else CustomerTier.SILVER
            )
            await repo.create(customer)
        
        # List all customers
        response = await async_client.get("/api/v1/customers/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        assert len(data["items"]) >= 5
        assert data["skip"] == 0
        assert data["limit"] == 100
        
        # Test pagination
        response = await async_client.get("/api/v1/customers/?skip=2&limit=2")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2
    
    @pytest.mark.asyncio
    async def test_list_customers_with_filters(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test listing customers with filters."""
        # Create customers
        repo = SQLAlchemyCustomerRepository(db_session)
        
        individual = Customer(
            customer_code="IND001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Individual"
        )
        
        business = Customer(
            customer_code="BUS001",
            customer_type=CustomerType.BUSINESS,
            business_name="Business Corp"
        )
        
        blacklisted = Customer(
            customer_code="BLK001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="Bad",
            last_name="Customer",
            blacklist_status=BlacklistStatus.BLACKLISTED
        )
        
        await repo.create(individual)
        await repo.create(business)
        await repo.create(blacklisted)
        
        # Filter by customer type
        response = await async_client.get("/api/v1/customers/?customer_type=BUSINESS")
        data = response.json()
        assert all(item["customer_type"] == "BUSINESS" for item in data["items"])
        
        # Filter by blacklist status
        response = await async_client.get("/api/v1/customers/?blacklist_status=BLACKLISTED")
        data = response.json()
        assert all(item["blacklist_status"] == "BLACKLISTED" for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_search_customers(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test searching customers by name."""
        # Create customers
        repo = SQLAlchemyCustomerRepository(db_session)
        
        customers = [
            Customer(
                customer_code="SEARCH001",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="Smith"
            ),
            Customer(
                customer_code="SEARCH002",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="Jane",
                last_name="Johnson"
            ),
            Customer(
                customer_code="SEARCH003",
                customer_type=CustomerType.BUSINESS,
                business_name="Johnson Industries"
            )
        ]
        
        for customer in customers:
            await repo.create(customer)
        
        # Search for "John"
        response = await async_client.get("/api/v1/customers/search/name?name=John")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # John Smith and Johnson Industries
        names = [item["display_name"] for item in data]
        assert "John Smith" in names
        assert "Johnson Industries" in names
    
    @pytest.mark.asyncio
    async def test_update_customer(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test updating customer information."""
        # Create customer
        repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="UPDATE001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            credit_limit=Decimal("1000.00"),
            customer_tier=CustomerTier.BRONZE
        )
        created_customer = await repo.create(customer)
        
        # Update customer
        update_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "credit_limit": "5000.00",
            "customer_tier": "SILVER"
        }
        
        response = await async_client.put(
            f"/api/v1/customers/{created_customer.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
        assert data["display_name"] == "Jane Smith"
        assert float(data["credit_limit"]) == 5000.00
        assert data["customer_tier"] == "SILVER"
    
    @pytest.mark.asyncio
    async def test_blacklist_customer(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test blacklisting a customer."""
        # Create customer
        repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="BLACK001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        created_customer = await repo.create(customer)
        
        # Blacklist customer
        blacklist_data = {
            "action": "blacklist",
            "reason": "Payment default"
        }
        
        response = await async_client.post(
            f"/api/v1/customers/{created_customer.id}/blacklist",
            json=blacklist_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["blacklist_status"] == "BLACKLISTED"
        
        # Unblacklist customer
        unblacklist_data = {
            "action": "unblacklist",
            "reason": "Resolved payment issues"
        }
        
        response = await async_client.post(
            f"/api/v1/customers/{created_customer.id}/blacklist",
            json=unblacklist_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["blacklist_status"] == "CLEAR"
    
    @pytest.mark.asyncio
    async def test_update_credit_limit(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test updating customer credit limit."""
        # Create customer
        repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="CREDIT001",
            customer_type=CustomerType.BUSINESS,
            business_name="Test Corp",
            credit_limit=Decimal("10000.00")
        )
        created_customer = await repo.create(customer)
        
        # Update credit limit
        credit_data = {
            "credit_limit": "25000.00",
            "reason": "Good payment history"
        }
        
        response = await async_client.put(
            f"/api/v1/customers/{created_customer.id}/credit-limit",
            json=credit_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert float(data["credit_limit"]) == 25000.00
    
    @pytest.mark.asyncio
    async def test_update_customer_tier(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test updating customer tier."""
        # Create customer
        repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="TIER001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            customer_tier=CustomerTier.BRONZE
        )
        created_customer = await repo.create(customer)
        
        # Update tier
        tier_data = {
            "customer_tier": "PLATINUM",
            "reason": "Loyalty upgrade"
        }
        
        response = await async_client.put(
            f"/api/v1/customers/{created_customer.id}/tier",
            json=tier_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["customer_tier"] == "PLATINUM"
    
    @pytest.mark.asyncio
    async def test_get_blacklisted_customers(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting all blacklisted customers."""
        # Create customers
        repo = SQLAlchemyCustomerRepository(db_session)
        
        for i in range(3):
            customer = Customer(
                customer_code=f"BLK{i:03d}",
                customer_type=CustomerType.INDIVIDUAL,
                first_name=f"Bad{i}",
                last_name="Customer",
                blacklist_status=BlacklistStatus.BLACKLISTED
            )
            await repo.create(customer)
        
        # Get blacklisted customers
        response = await async_client.get("/api/v1/customers/blacklisted/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert all(item["blacklist_status"] == "BLACKLISTED" for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_get_customers_by_tier(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test getting customers by tier."""
        # Create customers
        repo = SQLAlchemyCustomerRepository(db_session)
        
        for i in range(3):
            customer = Customer(
                customer_code=f"GOLD{i:03d}",
                customer_type=CustomerType.BUSINESS,
                business_name=f"Gold Company {i}",
                customer_tier=CustomerTier.GOLD,
                lifetime_value=Decimal(f"{100000 * (i + 1)}")
            )
            await repo.create(customer)
        
        # Get gold tier customers
        response = await async_client.get("/api/v1/customers/tier/GOLD")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert all(item["customer_tier"] == "GOLD" for item in data["items"])
        
        # Should be ordered by lifetime value descending
        values = [float(item["lifetime_value"]) for item in data["items"][:3]]
        assert values == sorted(values, reverse=True)
    
    @pytest.mark.asyncio
    async def test_delete_customer(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test soft deleting a customer."""
        # Create customer
        repo = SQLAlchemyCustomerRepository(db_session)
        customer = Customer(
            customer_code="DELETE001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="Delete",
            last_name="Me"
        )
        created_customer = await repo.create(customer)
        
        # Delete customer
        response = await async_client.delete(f"/api/v1/customers/{created_customer.id}")
        
        assert response.status_code == 204
        
        # Verify customer is soft deleted
        deleted_customer = await repo.get_by_id(created_customer.id)
        assert deleted_customer.is_active is False
    
    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent customer returns 404."""
        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await async_client.delete(f"/api/v1/customers/{fake_id}")
        
        assert response.status_code == 404