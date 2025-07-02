import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.entities.transaction_header import TransactionHeader
from src.domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, PaymentMethod
)


class TestTransactionHeader:
    """Test cases for TransactionHeader entity."""
    
    def test_create_sale_transaction(self):
        """Test creating a sale transaction."""
        transaction = TransactionHeader(
            transaction_number="LOC-SAL-20240101-0001",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            total_amount=Decimal("100.00")
        )
        
        assert transaction.transaction_number == "LOC-SAL-20240101-0001"
        assert transaction.transaction_type == TransactionType.SALE
        assert transaction.status == TransactionStatus.DRAFT
        assert transaction.payment_status == PaymentStatus.PENDING
        assert transaction.total_amount == Decimal("100.00")
        assert transaction.balance_due == Decimal("100.00")
        assert transaction.is_sale is True
        assert transaction.is_rental is False
    
    def test_create_rental_transaction(self):
        """Test creating a rental transaction."""
        start_date = date.today()
        end_date = date.today().replace(day=date.today().day + 7)
        
        transaction = TransactionHeader(
            transaction_number="LOC-RNT-20240101-0001",
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            rental_start_date=start_date,
            rental_end_date=end_date,
            total_amount=Decimal("200.00"),
            deposit_amount=Decimal("50.00")
        )
        
        assert transaction.transaction_type == TransactionType.RENTAL
        assert transaction.rental_start_date == start_date
        assert transaction.rental_end_date == end_date
        assert transaction.rental_days == 8  # 7 days + 1
        assert transaction.deposit_amount == Decimal("50.00")
        assert transaction.is_rental is True
    
    def test_transaction_validation(self):
        """Test transaction validation rules."""
        # Missing transaction number
        with pytest.raises(ValueError, match="Transaction number is required"):
            TransactionHeader(
                transaction_number="",
                transaction_type=TransactionType.SALE,
                transaction_date=datetime.utcnow(),
                customer_id=uuid4(),
                location_id=uuid4()
            )
        
        # Missing customer ID
        with pytest.raises(ValueError, match="Customer ID is required"):
            TransactionHeader(
                transaction_number="TRN-001",
                transaction_type=TransactionType.SALE,
                transaction_date=datetime.utcnow(),
                customer_id=None,
                location_id=uuid4()
            )
        
        # Negative amounts
        with pytest.raises(ValueError, match="Total amount cannot be negative"):
            TransactionHeader(
                transaction_number="TRN-001",
                transaction_type=TransactionType.SALE,
                transaction_date=datetime.utcnow(),
                customer_id=uuid4(),
                location_id=uuid4(),
                total_amount=Decimal("-100.00")
            )
    
    def test_rental_date_validation(self):
        """Test rental date validation."""
        # Missing rental dates
        with pytest.raises(ValueError, match="Rental start date is required"):
            TransactionHeader(
                transaction_number="RNT-001",
                transaction_type=TransactionType.RENTAL,
                transaction_date=datetime.utcnow(),
                customer_id=uuid4(),
                location_id=uuid4()
            )
        
        # End date before start date
        with pytest.raises(ValueError, match="Rental end date must be after start date"):
            TransactionHeader(
                transaction_number="RNT-001",
                transaction_type=TransactionType.RENTAL,
                transaction_date=datetime.utcnow(),
                customer_id=uuid4(),
                location_id=uuid4(),
                rental_start_date=date.today() + timedelta(days=10),
                rental_end_date=date.today() + timedelta(days=5)
            )
    
    def test_status_transitions(self):
        """Test transaction status transitions."""
        transaction = TransactionHeader(
            transaction_number="TRN-001",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4()
        )
        
        # Valid transitions from DRAFT
        assert transaction.can_transition_to(TransactionStatus.PENDING) is True
        assert transaction.can_transition_to(TransactionStatus.CANCELLED) is True
        assert transaction.can_transition_to(TransactionStatus.COMPLETED) is False
        
        # Update to PENDING
        transaction.update_status(TransactionStatus.PENDING)
        assert transaction.status == TransactionStatus.PENDING
        
        # Valid transitions from PENDING
        assert transaction.can_transition_to(TransactionStatus.CONFIRMED) is True
        assert transaction.can_transition_to(TransactionStatus.CANCELLED) is True
        assert transaction.can_transition_to(TransactionStatus.DRAFT) is False
    
    def test_apply_payment(self):
        """Test applying payment to transaction."""
        transaction = TransactionHeader(
            transaction_number="TRN-001",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            status=TransactionStatus.PENDING,
            total_amount=Decimal("100.00")
        )
        
        # Apply partial payment
        transaction.apply_payment(
            amount=Decimal("60.00"),
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_reference="CC-12345"
        )
        
        assert transaction.paid_amount == Decimal("60.00")
        assert transaction.balance_due == Decimal("40.00")
        assert transaction.payment_status == PaymentStatus.PARTIALLY_PAID
        assert transaction.payment_method == PaymentMethod.CREDIT_CARD
        assert transaction.is_paid_in_full is False
        
        # Apply remaining payment
        transaction.apply_payment(
            amount=Decimal("40.00"),
            payment_method=PaymentMethod.CASH
        )
        
        assert transaction.paid_amount == Decimal("100.00")
        assert transaction.balance_due == Decimal("0.00")
        assert transaction.payment_status == PaymentStatus.PAID
        assert transaction.is_paid_in_full is True
    
    def test_payment_validation(self):
        """Test payment validation."""
        transaction = TransactionHeader(
            transaction_number="TRN-001",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            status=TransactionStatus.PENDING,
            total_amount=Decimal("100.00")
        )
        
        # Negative payment
        with pytest.raises(ValueError, match="Payment amount must be positive"):
            transaction.apply_payment(Decimal("-10.00"), PaymentMethod.CASH)
        
        # Overpayment is allowed (could be tip, advance payment, etc.)
        transaction.apply_payment(Decimal("150.00"), PaymentMethod.CASH)
        assert transaction.paid_amount == Decimal("150.00")
        assert transaction.payment_status == PaymentStatus.PAID
        
        # Payment on cancelled transaction
        transaction.status = TransactionStatus.CANCELLED
        with pytest.raises(ValueError, match="Cannot apply payment"):
            transaction.apply_payment(Decimal("50.00"), PaymentMethod.CASH)
    
    def test_cancel_transaction(self):
        """Test cancelling transaction."""
        transaction = TransactionHeader(
            transaction_number="TRN-001",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            status=TransactionStatus.PENDING
        )
        
        transaction.cancel_transaction("Customer request", "admin")
        
        assert transaction.status == TransactionStatus.CANCELLED
        assert transaction.payment_status == PaymentStatus.CANCELLED
        assert "Customer request" in transaction.notes
        assert transaction.updated_by == "admin"
        
        # Cannot cancel already cancelled
        with pytest.raises(ValueError, match="already cancelled"):
            transaction.cancel_transaction("Test", "admin")
    
    def test_process_refund(self):
        """Test processing refund."""
        transaction = TransactionHeader(
            transaction_number="TRN-001",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            status=TransactionStatus.COMPLETED,
            total_amount=Decimal("100.00"),
            paid_amount=Decimal("100.00")
        )
        
        # Process partial refund
        transaction.process_refund(
            refund_amount=Decimal("25.00"),
            reason="Damaged item",
            refunded_by="manager"
        )
        
        assert transaction.status == TransactionStatus.REFUNDED
        assert transaction.payment_status == PaymentStatus.REFUNDED
        assert transaction.paid_amount == Decimal("75.00")
        assert "Damaged item" in transaction.notes
        
        # Cannot refund non-completed transaction (status changed to REFUNDED)
        with pytest.raises(ValueError, match="Can only refund completed transactions"):
            transaction.process_refund(Decimal("100.00"), "Test")
    
    def test_rental_return(self):
        """Test completing rental return."""
        transaction = TransactionHeader(
            transaction_number="RNT-001",
            transaction_type=TransactionType.RENTAL,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            status=TransactionStatus.IN_PROGRESS,
            rental_start_date=date.today(),
            rental_end_date=date.today().replace(day=date.today().day + 7)
        )
        
        return_date = date.today().replace(day=date.today().day + 5)
        transaction.complete_rental_return(return_date, "staff")
        
        assert transaction.actual_return_date == return_date
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.updated_by == "staff"
        
        # Cannot return non-rental
        sale_transaction = TransactionHeader(
            transaction_number="SAL-001",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            status=TransactionStatus.IN_PROGRESS
        )
        
        with pytest.raises(ValueError, match="only process return for rental"):
            sale_transaction.complete_rental_return(date.today())
    
    def test_mark_overdue(self):
        """Test marking transaction as overdue."""
        transaction = TransactionHeader(
            transaction_number="TRN-001",
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=uuid4(),
            location_id=uuid4(),
            status=TransactionStatus.CONFIRMED,
            payment_status=PaymentStatus.PENDING
        )
        
        transaction.mark_as_overdue("system")
        assert transaction.payment_status == PaymentStatus.OVERDUE
        
        # Cannot mark paid transaction as overdue
        transaction.payment_status = PaymentStatus.PAID
        with pytest.raises(ValueError, match="Cannot mark paid transaction"):
            transaction.mark_as_overdue()