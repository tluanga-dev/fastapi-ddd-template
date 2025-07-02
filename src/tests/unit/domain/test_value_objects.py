import pytest
from decimal import Decimal
from src.domain.value_objects import PhoneNumber, Address, Money


class TestPhoneNumber:
    """Test PhoneNumber value object."""
    
    def test_create_valid_phone_number(self):
        """Test creating a valid phone number."""
        phone = PhoneNumber("+1234567890")
        assert phone.value == "+1234567890"
    
    def test_phone_number_without_plus(self):
        """Test phone number without leading plus is normalized."""
        phone = PhoneNumber("1234567890")
        assert phone.value == "+1234567890"
    
    def test_phone_number_with_formatting(self):
        """Test phone number with formatting characters is cleaned."""
        phone = PhoneNumber("+1 (234) 567-8901")
        assert phone.value == "+12345678901"
    
    def test_invalid_phone_number_too_long(self):
        """Test phone number with more than 15 digits fails."""
        with pytest.raises(ValueError, match="Invalid phone number format"):
            PhoneNumber("+1234567890123456")
    
    def test_invalid_phone_number_too_short(self):
        """Test phone number with less than 2 digits fails."""
        with pytest.raises(ValueError, match="Invalid phone number format"):
            PhoneNumber("+1")
    
    def test_invalid_phone_number_with_letters(self):
        """Test phone number with letters fails."""
        with pytest.raises(ValueError, match="Invalid phone number format"):
            PhoneNumber("+1234ABC890")
    
    def test_format_display_us_number(self):
        """Test formatting US phone number for display."""
        phone = PhoneNumber("+12345678901")
        assert phone.format_display() == "+1 (234) 567-8901"
    
    def test_format_display_non_us_number(self):
        """Test formatting non-US phone number returns original."""
        phone = PhoneNumber("+919876543210")
        assert phone.format_display() == "+919876543210"
    
    def test_to_dict(self):
        """Test converting phone number to dictionary."""
        phone = PhoneNumber("+1234567890")
        assert phone.to_dict() == {"phone_number": "+1234567890"}
    
    def test_from_dict(self):
        """Test creating phone number from dictionary."""
        phone = PhoneNumber.from_dict({"phone_number": "+1234567890"})
        assert phone.value == "+1234567890"
    
    def test_phone_number_immutable(self):
        """Test phone number is immutable."""
        phone = PhoneNumber("+1234567890")
        with pytest.raises(AttributeError):
            phone.value = "+9876543210"


class TestAddress:
    """Test Address value object."""
    
    def test_create_valid_address(self):
        """Test creating a valid address."""
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        assert address.street == "123 Main St"
        assert address.city == "New York"
        assert address.state == "NY"
        assert address.country == "USA"
        assert address.postal_code == "10001"
    
    def test_create_address_without_postal_code(self):
        """Test creating address without postal code."""
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        assert address.postal_code is None
    
    def test_invalid_address_empty_street(self):
        """Test address with empty street fails."""
        with pytest.raises(ValueError, match="Street address cannot be empty"):
            Address(
                street="",
                city="New York",
                state="NY",
                country="USA"
            )
    
    def test_invalid_address_empty_city(self):
        """Test address with empty city fails."""
        with pytest.raises(ValueError, match="City cannot be empty"):
            Address(
                street="123 Main St",
                city="",
                state="NY",
                country="USA"
            )
    
    def test_invalid_address_empty_state(self):
        """Test address with empty state fails."""
        with pytest.raises(ValueError, match="State/Province cannot be empty"):
            Address(
                street="123 Main St",
                city="New York",
                state="",
                country="USA"
            )
    
    def test_invalid_address_empty_country(self):
        """Test address with empty country fails."""
        with pytest.raises(ValueError, match="Country cannot be empty"):
            Address(
                street="123 Main St",
                city="New York",
                state="NY",
                country=""
            )
    
    def test_us_zip_code_validation(self):
        """Test US ZIP code validation."""
        # Valid 5-digit ZIP
        address1 = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        assert address1.postal_code == "10001"
        
        # Valid ZIP+4
        address2 = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001-2345"
        )
        assert address2.postal_code == "10001-2345"
    
    def test_invalid_us_zip_code(self):
        """Test invalid US ZIP code fails."""
        with pytest.raises(ValueError, match="Invalid US ZIP code format"):
            Address(
                street="123 Main St",
                city="New York",
                state="NY",
                country="USA",
                postal_code="ABCDE"
            )
    
    def test_string_representation(self):
        """Test string representation of address."""
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        assert str(address) == "123 Main St, New York, NY, 10001, USA"
    
    def test_multiline_format(self):
        """Test multiline format of address."""
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        expected = "123 Main St\nNew York, NY 10001\nUSA"
        assert address.format_multiline() == expected
    
    def test_to_dict(self):
        """Test converting address to dictionary."""
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        expected = {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001"
        }
        assert address.to_dict() == expected
    
    def test_from_dict(self):
        """Test creating address from dictionary."""
        data = {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "postal_code": "10001"
        }
        address = Address.from_dict(data)
        assert address.street == "123 Main St"
        assert address.city == "New York"
    
    def test_address_immutable(self):
        """Test address is immutable."""
        address = Address(
            street="123 Main St",
            city="New York",
            state="NY",
            country="USA"
        )
        with pytest.raises(AttributeError):
            address.street = "456 Broadway"


class TestMoney:
    """Test Money value object."""
    
    def test_create_money_from_decimal(self):
        """Test creating money from Decimal."""
        money = Money(Decimal("100.50"))
        assert money.amount == Decimal("100.50")
        assert money.currency == "INR"
    
    def test_create_money_from_string(self):
        """Test creating money from string."""
        money = Money("100.50")
        assert money.amount == Decimal("100.50")
    
    def test_create_money_from_int(self):
        """Test creating money from integer."""
        money = Money(100)
        assert money.amount == Decimal("100.00")
    
    def test_create_money_from_float(self):
        """Test creating money from float."""
        money = Money(100.5)
        assert money.amount == Decimal("100.50")
    
    def test_create_money_with_currency(self):
        """Test creating money with specific currency."""
        money = Money(100, "USD")
        assert money.currency == "USD"
    
    def test_currency_normalized_to_uppercase(self):
        """Test currency is normalized to uppercase."""
        money = Money(100, "usd")
        assert money.currency == "USD"
    
    def test_invalid_currency_code(self):
        """Test invalid currency code fails."""
        with pytest.raises(ValueError, match="Currency must be a 3-letter ISO code"):
            Money(100, "US")
    
    def test_amount_rounded_to_two_decimals(self):
        """Test amount is rounded to 2 decimal places."""
        money = Money("100.555")
        assert money.amount == Decimal("100.56")  # Rounded up
    
    def test_string_representation(self):
        """Test string representation of money."""
        money = Money(1000.50, "INR")
        assert str(money) == "INR 1,000.50"
    
    def test_addition(self):
        """Test adding two money values."""
        money1 = Money(100, "INR")
        money2 = Money(50, "INR")
        result = money1 + money2
        assert result.amount == Decimal("150.00")
        assert result.currency == "INR"
    
    def test_addition_different_currencies(self):
        """Test adding different currencies fails."""
        money1 = Money(100, "INR")
        money2 = Money(50, "USD")
        with pytest.raises(ValueError, match="Cannot add different currencies"):
            money1 + money2
    
    def test_subtraction(self):
        """Test subtracting two money values."""
        money1 = Money(100, "INR")
        money2 = Money(30, "INR")
        result = money1 - money2
        assert result.amount == Decimal("70.00")
    
    def test_multiplication(self):
        """Test multiplying money by scalar."""
        money = Money(100, "INR")
        result = money * 1.5
        assert result.amount == Decimal("150.00")
    
    def test_division(self):
        """Test dividing money by scalar."""
        money = Money(100, "INR")
        result = money / 2
        assert result.amount == Decimal("50.00")
    
    def test_division_by_zero(self):
        """Test division by zero fails."""
        money = Money(100, "INR")
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            money / 0
    
    def test_equality(self):
        """Test money equality comparison."""
        money1 = Money(100, "INR")
        money2 = Money(100, "INR")
        money3 = Money(100, "USD")
        
        assert money1 == money2
        assert money1 != money3
    
    def test_comparison_operators(self):
        """Test money comparison operators."""
        money1 = Money(100, "INR")
        money2 = Money(200, "INR")
        
        assert money1 < money2
        assert money1 <= money2
        assert money2 > money1
        assert money2 >= money1
    
    def test_comparison_different_currencies(self):
        """Test comparing different currencies fails."""
        money1 = Money(100, "INR")
        money2 = Money(100, "USD")
        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            money1 < money2
    
    def test_is_zero(self):
        """Test checking if money is zero."""
        money1 = Money(0, "INR")
        money2 = Money(100, "INR")
        
        assert money1.is_zero()
        assert not money2.is_zero()
    
    def test_is_positive_negative(self):
        """Test checking if money is positive or negative."""
        positive = Money(100, "INR")
        negative = Money(-100, "INR")
        zero = Money(0, "INR")
        
        assert positive.is_positive()
        assert not positive.is_negative()
        assert negative.is_negative()
        assert not negative.is_positive()
        assert not zero.is_positive()
        assert not zero.is_negative()
    
    def test_apply_percentage(self):
        """Test applying percentage to money."""
        money = Money(100, "INR")
        
        # 10% of 100
        result = money.apply_percentage(10)
        assert result.amount == Decimal("10.00")
        
        # 15.5% of 100
        result = money.apply_percentage(15.5)
        assert result.amount == Decimal("15.50")
    
    def test_to_dict(self):
        """Test converting money to dictionary."""
        money = Money(100.50, "INR")
        expected = {
            "amount": "100.50",
            "currency": "INR"
        }
        assert money.to_dict() == expected
    
    def test_from_dict(self):
        """Test creating money from dictionary."""
        data = {
            "amount": "100.50",
            "currency": "USD"
        }
        money = Money.from_dict(data)
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"
    
    def test_zero_factory_method(self):
        """Test creating zero money value."""
        money = Money.zero()
        assert money.amount == Decimal("0.00")
        assert money.currency == "INR"
        
        money_usd = Money.zero("USD")
        assert money_usd.amount == Decimal("0.00")
        assert money_usd.currency == "USD"
    
    def test_money_immutable(self):
        """Test money is immutable."""
        money = Money(100, "INR")
        with pytest.raises(AttributeError):
            money.amount = Decimal("200")