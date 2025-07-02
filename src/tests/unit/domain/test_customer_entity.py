import pytest
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

from src.domain.entities.customer import Customer
from src.domain.value_objects.customer_type import CustomerType, CustomerTier, BlacklistStatus


class TestCustomerEntity:
    """Test Customer domain entity."""
    
    def test_create_individual_customer(self):
        """Test creating an individual customer."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            tax_id="123456789",
            customer_tier=CustomerTier.SILVER,
            credit_limit=Decimal("5000.00")
        )
        
        assert customer.customer_code == "CUST001"
        assert customer.customer_type == CustomerType.INDIVIDUAL
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.tax_id == "123456789"
        assert customer.customer_tier == CustomerTier.SILVER
        assert customer.credit_limit == Decimal("5000.00")
        assert customer.blacklist_status == BlacklistStatus.CLEAR
        assert customer.lifetime_value == Decimal("0.00")
        assert customer.is_active is True
        assert isinstance(customer.id, UUID)
        assert isinstance(customer.created_at, datetime)
    
    def test_create_business_customer(self):
        """Test creating a business customer."""
        customer = Customer(
            customer_code="CUST002",
            customer_type=CustomerType.BUSINESS,
            business_name="ABC Corporation",
            tax_id="GST123456",
            customer_tier=CustomerTier.GOLD,
            credit_limit=Decimal("50000.00")
        )
        
        assert customer.customer_code == "CUST002"
        assert customer.customer_type == CustomerType.BUSINESS
        assert customer.business_name == "ABC Corporation"
        assert customer.tax_id == "GST123456"
        assert customer.customer_tier == CustomerTier.GOLD
        assert customer.credit_limit == Decimal("50000.00")
        assert customer.first_name is None
        assert customer.last_name is None
    
    def test_customer_code_validation(self):
        """Test customer code validation."""
        # Empty code
        with pytest.raises(ValueError, match="Customer code cannot be empty"):
            Customer(
                customer_code="",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="Doe"
            )
        
        # Whitespace only
        with pytest.raises(ValueError, match="Customer code cannot be empty"):
            Customer(
                customer_code="   ",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="Doe"
            )
        
        # Too long
        with pytest.raises(ValueError, match="Customer code cannot exceed 20 characters"):
            Customer(
                customer_code="A" * 21,
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="Doe"
            )
    
    def test_individual_customer_validation(self):
        """Test individual customer requires first and last name."""
        # Missing first name
        with pytest.raises(ValueError, match="First name is required for individual customers"):
            Customer(
                customer_code="CUST001",
                customer_type=CustomerType.INDIVIDUAL,
                last_name="Doe"
            )
        
        # Missing last name
        with pytest.raises(ValueError, match="Last name is required for individual customers"):
            Customer(
                customer_code="CUST001",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John"
            )
        
        # Empty first name
        with pytest.raises(ValueError, match="First name is required for individual customers"):
            Customer(
                customer_code="CUST001",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="   ",
                last_name="Doe"
            )
    
    def test_business_customer_validation(self):
        """Test business customer requires business name."""
        # Missing business name
        with pytest.raises(ValueError, match="Business name is required for business customers"):
            Customer(
                customer_code="CUST002",
                customer_type=CustomerType.BUSINESS
            )
        
        # Empty business name
        with pytest.raises(ValueError, match="Business name is required for business customers"):
            Customer(
                customer_code="CUST002",
                customer_type=CustomerType.BUSINESS,
                business_name="   "
            )
        
        # Too long business name
        with pytest.raises(ValueError, match="Business name cannot exceed 200 characters"):
            Customer(
                customer_code="CUST002",
                customer_type=CustomerType.BUSINESS,
                business_name="A" * 201
            )
    
    def test_name_length_validation(self):
        """Test name length limits."""
        # First name too long
        with pytest.raises(ValueError, match="First name cannot exceed 50 characters"):
            Customer(
                customer_code="CUST001",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="A" * 51,
                last_name="Doe"
            )
        
        # Last name too long
        with pytest.raises(ValueError, match="Last name cannot exceed 50 characters"):
            Customer(
                customer_code="CUST001",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="A" * 51
            )
    
    def test_tax_id_validation(self):
        """Test tax ID validation."""
        # Too long tax ID
        with pytest.raises(ValueError, match="Tax ID cannot exceed 50 characters"):
            Customer(
                customer_code="CUST001",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="Doe",
                tax_id="A" * 51
            )
    
    def test_credit_limit_validation(self):
        """Test credit limit validation."""
        # Negative credit limit
        with pytest.raises(ValueError, match="Credit limit cannot be negative"):
            Customer(
                customer_code="CUST001",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="Doe",
                credit_limit=Decimal("-100.00")
            )
    
    def test_lifetime_value_validation(self):
        """Test lifetime value validation."""
        # Negative lifetime value
        with pytest.raises(ValueError, match="Lifetime value cannot be negative"):
            Customer(
                customer_code="CUST001",
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="Doe",
                lifetime_value=Decimal("-100.00")
            )
    
    def test_get_display_name(self):
        """Test getting display name."""
        # Individual customer
        individual = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        assert individual.get_display_name() == "John Doe"
        
        # Business customer
        business = Customer(
            customer_code="CUST002",
            customer_type=CustomerType.BUSINESS,
            business_name="ABC Corporation"
        )
        assert business.get_display_name() == "ABC Corporation"
    
    def test_update_personal_info(self):
        """Test updating personal information."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        customer.update_personal_info(
            first_name="Jane",
            last_name="Smith",
            updated_by="admin"
        )
        
        assert customer.first_name == "Jane"
        assert customer.last_name == "Smith"
        assert customer.updated_by == "admin"
        assert isinstance(customer.updated_at, datetime)
    
    def test_update_personal_info_business_customer_fails(self):
        """Test updating personal info on business customer fails."""
        customer = Customer(
            customer_code="CUST002",
            customer_type=CustomerType.BUSINESS,
            business_name="ABC Corporation"
        )
        
        with pytest.raises(ValueError, match="Personal info can only be updated for individual customers"):
            customer.update_personal_info(first_name="John")
    
    def test_update_business_info(self):
        """Test updating business information."""
        customer = Customer(
            customer_code="CUST002",
            customer_type=CustomerType.BUSINESS,
            business_name="ABC Corporation"
        )
        
        customer.update_business_info(
            business_name="XYZ Corporation",
            tax_id="GST999999",
            updated_by="admin"
        )
        
        assert customer.business_name == "XYZ Corporation"
        assert customer.tax_id == "GST999999"
        assert customer.updated_by == "admin"
    
    def test_update_business_name_individual_customer_fails(self):
        """Test updating business name on individual customer fails."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        with pytest.raises(ValueError, match="Business name can only be updated for business customers"):
            customer.update_business_info(business_name="ABC Corp")
    
    def test_update_credit_limit(self):
        """Test updating credit limit."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            credit_limit=Decimal("1000.00")
        )
        
        customer.update_credit_limit(Decimal("5000.00"), updated_by="admin")
        
        assert customer.credit_limit == Decimal("5000.00")
        assert customer.updated_by == "admin"
    
    def test_update_credit_limit_negative_fails(self):
        """Test updating credit limit with negative value fails."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        with pytest.raises(ValueError, match="Credit limit cannot be negative"):
            customer.update_credit_limit(Decimal("-100.00"))
    
    def test_update_tier(self):
        """Test updating customer tier."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            customer_tier=CustomerTier.BRONZE
        )
        
        customer.update_tier(CustomerTier.GOLD, updated_by="admin")
        
        assert customer.customer_tier == CustomerTier.GOLD
        assert customer.updated_by == "admin"
    
    def test_blacklist(self):
        """Test blacklisting a customer."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        assert customer.blacklist_status == BlacklistStatus.CLEAR
        assert not customer.is_blacklisted()
        
        customer.blacklist(updated_by="admin")
        
        assert customer.blacklist_status == BlacklistStatus.BLACKLISTED
        assert customer.is_blacklisted()
        assert customer.updated_by == "admin"
    
    def test_blacklist_already_blacklisted_fails(self):
        """Test blacklisting already blacklisted customer fails."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            blacklist_status=BlacklistStatus.BLACKLISTED
        )
        
        with pytest.raises(ValueError, match="Customer is already blacklisted"):
            customer.blacklist()
    
    def test_remove_from_blacklist(self):
        """Test removing customer from blacklist."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            blacklist_status=BlacklistStatus.BLACKLISTED
        )
        
        customer.remove_from_blacklist(updated_by="admin")
        
        assert customer.blacklist_status == BlacklistStatus.CLEAR
        assert not customer.is_blacklisted()
        assert customer.updated_by == "admin"
    
    def test_remove_from_blacklist_not_blacklisted_fails(self):
        """Test removing non-blacklisted customer from blacklist fails."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        with pytest.raises(ValueError, match="Customer is not blacklisted"):
            customer.remove_from_blacklist()
    
    def test_update_lifetime_value(self):
        """Test updating lifetime value."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        customer.update_lifetime_value(Decimal("10000.00"), updated_by="system")
        
        assert customer.lifetime_value == Decimal("10000.00")
        assert customer.updated_by == "system"
    
    def test_update_lifetime_value_negative_fails(self):
        """Test updating lifetime value with negative amount fails."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        with pytest.raises(ValueError, match="Lifetime value cannot be negative"):
            customer.update_lifetime_value(Decimal("-100.00"))
    
    def test_record_transaction(self):
        """Test recording a transaction."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        assert customer.last_transaction_date is None
        
        customer.record_transaction(updated_by="system")
        
        assert customer.last_transaction_date is not None
        assert isinstance(customer.last_transaction_date, datetime)
        assert customer.updated_by == "system"
    
    def test_can_use_credit(self):
        """Test checking if customer can use credit."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            credit_limit=Decimal("5000.00")
        )
        
        # Can use credit within limit
        assert customer.can_use_credit(Decimal("1000.00")) is True
        assert customer.can_use_credit(Decimal("5000.00")) is True
        
        # Cannot use credit above limit
        assert customer.can_use_credit(Decimal("5001.00")) is False
        
        # Blacklisted customer cannot use credit
        customer.blacklist()
        assert customer.can_use_credit(Decimal("100.00")) is False
        
        # Inactive customer cannot use credit
        customer.remove_from_blacklist()
        customer.is_active = False
        assert customer.can_use_credit(Decimal("100.00")) is False
    
    def test_string_representation(self):
        """Test string representation of customer."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe"
        )
        
        assert str(customer) == "Customer(CUST001 - John Doe)"
    
    def test_repr_representation(self):
        """Test developer representation of customer."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            customer_tier=CustomerTier.SILVER
        )
        
        repr_str = repr(customer)
        assert "CUST001" in repr_str
        assert "INDIVIDUAL" in repr_str
        assert "John Doe" in repr_str
        assert "SILVER" in repr_str
        assert f"id={customer.id}" in repr_str
    
    def test_customer_inherits_base_entity(self):
        """Test that Customer properly inherits from BaseEntity."""
        customer = Customer(
            customer_code="CUST001",
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            created_by="creator",
            updated_by="updater"
        )
        
        assert isinstance(customer.id, UUID)
        assert isinstance(customer.created_at, datetime)
        assert isinstance(customer.updated_at, datetime)
        assert customer.created_by == "creator"
        assert customer.updated_by == "updater"
        assert customer.is_active is True