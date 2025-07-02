import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.entities.transaction_line import TransactionLine
from src.domain.value_objects.transaction_type import LineItemType, RentalPeriodUnit


class TestTransactionLine:
    """Test cases for TransactionLine entity."""
    
    def test_create_product_line(self):
        """Test creating a product line."""
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Test Product",
            quantity=Decimal("2"),
            unit_price=Decimal("50.00")
        )
        
        assert line.line_number == 1
        assert line.line_type == LineItemType.PRODUCT
        assert line.quantity == Decimal("2")
        assert line.unit_price == Decimal("50.00")
        assert line.returned_quantity == Decimal("0")
        assert line.is_fully_returned is False
    
    def test_line_validation(self):
        """Test transaction line validation."""
        # Missing transaction ID
        with pytest.raises(ValueError, match="Transaction ID is required"):
            TransactionLine(
                transaction_id=None,
                line_number=1,
                line_type=LineItemType.PRODUCT,
                description="Test"
            )
        
        # Invalid line number
        with pytest.raises(ValueError, match="Line number must be positive"):
            TransactionLine(
                transaction_id=uuid4(),
                line_number=0,
                line_type=LineItemType.PRODUCT,
                description="Test"
            )
        
        # Empty description
        with pytest.raises(ValueError, match="Description is required"):
            TransactionLine(
                transaction_id=uuid4(),
                line_number=1,
                line_type=LineItemType.PRODUCT,
                description=""
            )
        
        # Negative quantity
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            TransactionLine(
                transaction_id=uuid4(),
                line_number=1,
                line_type=LineItemType.PRODUCT,
                description="Test",
                quantity=Decimal("-1")
            )
    
    def test_product_line_requires_sku(self):
        """Test that product lines require SKU."""
        with pytest.raises(ValueError, match="SKU ID is required for PRODUCT"):
            TransactionLine(
                transaction_id=uuid4(),
                line_number=1,
                line_type=LineItemType.PRODUCT,
                description="Test Product"
            )
        
        # Service lines also require SKU
        with pytest.raises(ValueError, match="SKU ID is required for SERVICE"):
            TransactionLine(
                transaction_id=uuid4(),
                line_number=1,
                line_type=LineItemType.SERVICE,
                description="Test Service"
            )
    
    def test_calculate_line_total(self):
        """Test line total calculation."""
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Test Product",
            quantity=Decimal("3"),
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("10"),
            tax_rate=Decimal("8")
        )
        
        line.calculate_line_total()
        
        # Subtotal: 3 * 100 = 300
        # Discount: 300 * 0.1 = 30
        # After discount: 270
        # Tax: 270 * 0.08 = 21.6
        # Total: 270 + 21.6 = 291.6
        
        assert line.discount_amount == Decimal("30.00")
        assert line.tax_amount == Decimal("21.60")
        assert line.line_total == Decimal("291.60")
    
    def test_discount_line_negative_total(self):
        """Test that discount lines have negative totals."""
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.DISCOUNT,
            description="Discount",
            quantity=Decimal("1"),
            unit_price=Decimal("50.00")
        )
        
        line.calculate_line_total()
        assert line.line_total == Decimal("-50.00")
    
    def test_apply_discount(self):
        """Test applying discount to line."""
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Test Product",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00")
        )
        
        # Apply percentage discount
        line.apply_discount(discount_percentage=Decimal("15"))
        assert line.discount_percentage == Decimal("15")
        # apply_discount calls calculate_line_total automatically
        assert line.discount_amount == Decimal("30.00")  # 200 * 0.15
        assert line.line_total == Decimal("170.00")
        
        # Apply amount discount
        line.apply_discount(discount_amount=Decimal("25.00"))
        assert line.discount_amount == Decimal("25.00")
        assert line.discount_percentage == Decimal("0.00")  # Reset when using amount
        
        # apply_discount already calculated the total
        assert line.line_total == Decimal("175.00")
    
    def test_discount_validation(self):
        """Test discount validation."""
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Test",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00")
        )
        
        # Cannot apply both types
        with pytest.raises(ValueError, match="Cannot apply both"):
            line.apply_discount(
                discount_percentage=Decimal("10"),
                discount_amount=Decimal("10.00")
            )
        
        # Invalid percentage
        with pytest.raises(ValueError, match="between 0 and 100"):
            line.apply_discount(discount_percentage=Decimal("150"))
        
        # Negative amount
        with pytest.raises(ValueError, match="cannot be negative"):
            line.apply_discount(discount_amount=Decimal("-10"))
    
    def test_process_return(self):
        """Test processing returns."""
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Test Product",
            quantity=Decimal("5"),
            unit_price=Decimal("50.00")
        )
        
        # Return partial quantity
        line.process_return(
            return_quantity=Decimal("2"),
            return_date=date.today(),
            return_reason="Customer dissatisfied"
        )
        
        assert line.returned_quantity == Decimal("2")
        assert line.return_date == date.today()
        assert line.remaining_quantity == Decimal("3")
        assert line.is_partially_returned is True
        assert line.is_fully_returned is False
        assert "Customer dissatisfied" in line.notes
        
        # Return remaining
        line.process_return(
            return_quantity=Decimal("3"),
            return_date=date.today()
        )
        
        assert line.returned_quantity == Decimal("5")
        assert line.remaining_quantity == Decimal("0")
        assert line.is_fully_returned is True
    
    def test_return_validation(self):
        """Test return validation."""
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Test",
            quantity=Decimal("3"),
            unit_price=Decimal("50.00")
        )
        
        # Negative return quantity
        with pytest.raises(ValueError, match="must be positive"):
            line.process_return(Decimal("-1"), date.today())
        
        # Return more than quantity
        with pytest.raises(ValueError, match="exceeds remaining quantity"):
            line.process_return(Decimal("5"), date.today())
        
        # Return after partial return
        line.process_return(Decimal("2"), date.today())
        
        with pytest.raises(ValueError, match="exceeds remaining quantity"):
            line.process_return(Decimal("2"), date.today())  # Only 1 remaining
    
    def test_rental_line(self):
        """Test rental-specific features."""
        start_date = date.today()
        end_date = date.today() + timedelta(days=7)
        
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Rental Item",
            quantity=Decimal("1"),
            unit_price=Decimal("70.00"),  # 7 days * $10/day
            rental_period_value=7,
            rental_period_unit=RentalPeriodUnit.DAY,
            rental_start_date=start_date,
            rental_end_date=end_date
        )
        
        assert line.rental_period_value == 7
        assert line.rental_period_unit == RentalPeriodUnit.DAY
        assert line.rental_days == 7
    
    def test_rental_validation(self):
        """Test rental validation."""
        # Period value without unit
        with pytest.raises(ValueError, match="Rental period unit is required"):
            TransactionLine(
                transaction_id=uuid4(),
                line_number=1,
                line_type=LineItemType.PRODUCT,
                sku_id=uuid4(),
                description="Test",
                rental_period_value=7
            )
        
        # Invalid rental dates
        with pytest.raises(ValueError, match="end date must be after start date"):
            TransactionLine(
                transaction_id=uuid4(),
                line_number=1,
                line_type=LineItemType.PRODUCT,
                sku_id=uuid4(),
                description="Test",
                rental_start_date=date.today() + timedelta(days=10),
                rental_end_date=date.today() + timedelta(days=5)
            )
    
    def test_update_rental_period(self):
        """Test updating rental period."""
        start_date = date.today()
        
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Rental Item",
            quantity=Decimal("1"),
            unit_price=Decimal("70.00"),
            rental_period_value=7,
            rental_period_unit=RentalPeriodUnit.DAY,
            rental_start_date=start_date,
            rental_end_date=date.today() + timedelta(days=7)
        )
        
        # Extend rental
        new_end_date = date.today() + timedelta(days=10)
        line.update_rental_period(new_end_date, "customer")
        
        assert line.rental_end_date == new_end_date
        assert line.rental_days == 10
        assert line.rental_period_value == 10  # Updated for DAY units
        assert line.updated_by == "customer"
        
        # Cannot set end before start
        with pytest.raises(ValueError, match="must be after start date"):
            line.update_rental_period(date(2023, 12, 31))
    
    def test_effective_unit_price(self):
        """Test effective unit price calculation."""
        line = TransactionLine(
            transaction_id=uuid4(),
            line_number=1,
            line_type=LineItemType.PRODUCT,
            sku_id=uuid4(),
            description="Test",
            quantity=Decimal("2"),
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("30.00")
        )
        
        # (2 * 100 - 30) / 2 = 85
        assert line.effective_unit_price == Decimal("85.00")
        
        # Zero quantity
        line.quantity = Decimal("0")
        assert line.effective_unit_price == Decimal("0.00")