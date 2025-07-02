import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.entities.rental_return import RentalReturn
from src.domain.entities.rental_return_line import RentalReturnLine
from src.domain.entities.inspection_report import InspectionReport
from src.domain.value_objects.rental_return_type import ReturnType, ReturnStatus
from src.domain.value_objects.item_type import ConditionGrade
from src.domain.value_objects.inspection_type import InspectionStatus, DamageSeverity


class TestRentalReturn:
    """Test cases for RentalReturn entity."""
    
    def test_create_rental_return(self):
        """Test creating a rental return."""
        transaction_id = uuid4()
        return_date = date.today()
        
        rental_return = RentalReturn(
            rental_transaction_id=transaction_id,
            return_date=return_date,
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED,
            expected_return_date=date.today(),
            processed_by="test_user"
        )
        
        assert rental_return.rental_transaction_id == transaction_id
        assert rental_return.return_date == return_date
        assert rental_return.return_type == ReturnType.FULL
        assert rental_return.return_status == ReturnStatus.INITIATED
        assert rental_return.processed_by == "test_user"
        assert rental_return.lines == []
        assert rental_return.inspection_reports == []
    
    def test_rental_return_is_late(self):
        """Test late return detection."""
        # Return that's late
        late_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            expected_return_date=date.today() - timedelta(days=1),  # Past date
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
        
        assert late_return.is_late() is True
        assert late_return.days_late() > 0
        
        # Return that's on time
        on_time_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            expected_return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
        
        assert on_time_return.is_late() is False
        assert on_time_return.days_late() == 0
    
    def test_calculate_late_fees(self):
        """Test late fee calculation."""
        rental_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            expected_return_date=date.today() - timedelta(days=15),  # 15 days late
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
        
        daily_rate = Decimal("5.00")
        days_late = rental_return.days_late()
        expected_fee = daily_rate * days_late
        
        calculated_fee = rental_return.calculate_late_fees(daily_rate)
        assert calculated_fee == expected_fee
    
    def test_calculate_damage_fees(self):
        """Test damage fee calculation."""
        rental_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
        
        # Add some lines with damage fees
        line1 = RentalReturnLine(
            return_id=rental_return.id,
            inventory_unit_id=uuid4(),
            original_quantity=1,
            returned_quantity=1,
            damage_fee=Decimal("25.00")
        )
        
        line2 = RentalReturnLine(
            return_id=rental_return.id,
            inventory_unit_id=uuid4(),
            original_quantity=1,
            returned_quantity=1,
            damage_fee=Decimal("15.00")
        )
        
        rental_return.add_line(line1)
        rental_return.add_line(line2)
        
        total_damage = rental_return.calculate_damage_fees()
        assert total_damage == Decimal("40.00")
    
    def test_calculate_deposit_release(self):
        """Test deposit release calculation."""
        rental_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.COMPLETED,
            total_late_fee=Decimal("10.00"),
            total_damage_fee=Decimal("25.00"),
            total_cleaning_fee=Decimal("15.00")
        )
        
        original_deposit = Decimal("100.00")
        release_amount = rental_return.calculate_deposit_release(original_deposit)
        
        # Should release: 100 - (10 + 25 + 15) = 50
        assert release_amount == Decimal("50.00")
    
    def test_update_status(self):
        """Test status updates."""
        rental_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
        
        rental_return.update_status(ReturnStatus.IN_INSPECTION, "inspector")
        assert rental_return.return_status == ReturnStatus.IN_INSPECTION
        assert rental_return.updated_by == "inspector"
    
    def test_finalize_return(self):
        """Test return finalization."""
        rental_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.IN_INSPECTION
        )
        
        rental_return.finalize_return(
            finalized_by="manager",
            total_late_fee=Decimal("10.00"),
            total_damage_fee=Decimal("20.00"),
            notes="All good"
        )
        
        assert rental_return.return_status == ReturnStatus.COMPLETED
        assert rental_return.finalized_by == "manager"
        assert rental_return.total_late_fee == Decimal("10.00")
        assert rental_return.total_damage_fee == Decimal("20.00")
        assert rental_return.finalized_at is not None
    
    def test_record_deposit_release(self):
        """Test deposit release recording."""
        rental_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.COMPLETED
        )
        
        release_amount = Decimal("75.00")
        withheld_amount = Decimal("25.00")
        
        rental_return.record_deposit_release(
            release_amount=release_amount,
            withheld_amount=withheld_amount,
            release_date=datetime.utcnow(),
            processed_by="clerk",
            notes="Partial release due to damage"
        )
        
        assert rental_return.deposit_released is True
        assert rental_return.deposit_release_amount == release_amount
        assert rental_return.deposit_withheld_amount == withheld_amount
        assert rental_return.deposit_release_date is not None


class TestRentalReturnLine:
    """Test cases for RentalReturnLine entity."""
    
    def test_create_rental_return_line(self):
        """Test creating a rental return line."""
        return_id = uuid4()
        inventory_unit_id = uuid4()
        
        line = RentalReturnLine(
            return_id=return_id,
            inventory_unit_id=inventory_unit_id,
            original_quantity=5,
            returned_quantity=3,
            condition_grade=ConditionGrade.A
        )
        
        assert line.return_id == return_id
        assert line.inventory_unit_id == inventory_unit_id
        assert line.original_quantity == 5
        assert line.returned_quantity == 3
        assert line.condition_grade == ConditionGrade.A
        assert line.is_processed is False
    
    def test_update_return_quantity(self):
        """Test updating return quantity."""
        line = RentalReturnLine(
            return_id=uuid4(),
            inventory_unit_id=uuid4(),
            original_quantity=5,
            returned_quantity=3
        )
        
        line.update_return_quantity(4, "user")
        assert line.returned_quantity == 4
        assert line.updated_by == "user"
    
    def test_update_return_quantity_validation(self):
        """Test return quantity validation."""
        line = RentalReturnLine(
            return_id=uuid4(),
            inventory_unit_id=uuid4(),
            original_quantity=5,
            returned_quantity=3
        )
        
        # Should not allow negative quantity
        with pytest.raises(ValueError, match="Returned quantity cannot be negative"):
            line.update_return_quantity(-1, "user")
        
        # Should not allow quantity greater than original
        with pytest.raises(ValueError, match="Cannot return more than originally rented"):
            line.update_return_quantity(6, "user")
    
    def test_update_condition(self):
        """Test updating condition grade."""
        line = RentalReturnLine(
            return_id=uuid4(),
            inventory_unit_id=uuid4(),
            original_quantity=1,
            returned_quantity=1
        )
        
        line.update_condition(ConditionGrade.B, "Minor wear", "inspector")
        assert line.condition_grade == ConditionGrade.B
        assert line.notes == "Minor wear"
        assert line.updated_by == "inspector"
    
    def test_set_fees(self):
        """Test setting various fees."""
        line = RentalReturnLine(
            return_id=uuid4(),
            inventory_unit_id=uuid4(),
            original_quantity=1,
            returned_quantity=1
        )
        
        line.set_late_fee(Decimal("10.00"), "system")
        line.set_damage_fee(Decimal("25.00"), "inspector")
        line.set_cleaning_fee(Decimal("15.00"), "manager")
        line.set_replacement_fee(Decimal("100.00"), "manager")
        
        assert line.late_fee == Decimal("10.00")
        assert line.damage_fee == Decimal("25.00")
        assert line.cleaning_fee == Decimal("15.00")
        assert line.replacement_fee == Decimal("100.00")
    
    def test_process_line(self):
        """Test processing a line."""
        line = RentalReturnLine(
            return_id=uuid4(),
            inventory_unit_id=uuid4(),
            original_quantity=1,
            returned_quantity=1
        )
        
        assert line.is_processed is False
        
        line.process_line("processor")
        assert line.is_processed is True
        assert line.processed_by == "processor"
        assert line.processed_at is not None
    
    def test_calculate_total_fees(self):
        """Test total fee calculation."""
        line = RentalReturnLine(
            return_id=uuid4(),
            inventory_unit_id=uuid4(),
            original_quantity=1,
            returned_quantity=1,
            late_fee=Decimal("10.00"),
            damage_fee=Decimal("25.00"),
            cleaning_fee=Decimal("15.00"),
            replacement_fee=Decimal("50.00")
        )
        
        total = line.calculate_total_fees()
        assert total == Decimal("100.00")


class TestInspectionReport:
    """Test cases for InspectionReport entity."""
    
    def test_create_inspection_report(self):
        """Test creating an inspection report."""
        return_id = uuid4()
        inspector_id = "inspector_123"
        inspection_date = datetime.utcnow()
        
        report = InspectionReport(
            return_id=return_id,
            inspector_id=inspector_id,
            inspection_date=inspection_date,
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        
        assert report.return_id == return_id
        assert report.inspector_id == inspector_id
        assert report.inspection_date == inspection_date
        assert report.inspection_status == InspectionStatus.IN_PROGRESS
        assert report.damage_found is False
        assert report.damage_findings == []
    
    def test_add_damage_finding(self):
        """Test adding damage findings."""
        report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        
        report.add_damage_finding(
            item_description="Laptop computer",
            damage_description="Screen has scratches",
            severity=DamageSeverity.MINOR,
            estimated_cost=Decimal("50.00"),
            photos=["photo1.jpg", "photo2.jpg"]
        )
        
        assert len(report.damage_findings) == 1
        finding = report.damage_findings[0]
        assert finding["item_description"] == "Laptop computer"
        assert finding["severity"] == DamageSeverity.MINOR
        assert finding["estimated_cost"] == Decimal("50.00")
    
    def test_mark_damage_found(self):
        """Test marking damage as found."""
        report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        
        total_cost = Decimal("75.00")
        report.mark_damage_found(total_cost)
        
        assert report.damage_found is True
        assert report.total_damage_cost == total_cost
    
    def test_mark_no_damage_found(self):
        """Test marking no damage found."""
        report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        
        report.mark_no_damage_found()
        
        assert report.damage_found is False
        assert report.total_damage_cost == Decimal("0.00")
        assert report.inspection_status == InspectionStatus.COMPLETED
    
    def test_approve_inspection(self):
        """Test approving an inspection."""
        report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.COMPLETED
        )
        
        report.approve_inspection("manager", "Approved - damages verified")
        
        assert report.is_approved is True
        assert report.approved_by == "manager"
        assert report.approval_notes == "Approved - damages verified"
        assert report.approved_at is not None
    
    def test_reject_inspection(self):
        """Test rejecting an inspection."""
        report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.COMPLETED
        )
        
        report.reject_inspection("manager", "Damages not properly documented")
        
        assert report.is_approved is False
        assert report.approved_by == "manager"
        assert report.approval_notes == "Damages not properly documented"
        assert report.inspection_status == InspectionStatus.REJECTED
    
    def test_complete_inspection(self):
        """Test completing an inspection."""
        report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        
        report.complete_inspection("All items inspected", "inspector")
        
        assert report.inspection_status == InspectionStatus.COMPLETED
        assert report.completion_notes == "All items inspected"
        assert report.updated_by == "inspector"
    
    def test_add_photos(self):
        """Test adding photos to inspection."""
        report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        
        photos = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
        report.add_photos(photos)
        
        assert report.photos == photos
    
    def test_calculate_total_damage_cost(self):
        """Test calculating total damage cost from findings."""
        report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        
        # Add multiple damage findings
        report.add_damage_finding(
            item_description="Item 1",
            damage_description="Minor damage",
            severity=DamageSeverity.MINOR,
            estimated_cost=Decimal("25.00")
        )
        
        report.add_damage_finding(
            item_description="Item 2", 
            damage_description="Major damage",
            severity=DamageSeverity.MAJOR,
            estimated_cost=Decimal("75.00")
        )
        
        total_cost = report.calculate_total_damage_cost()
        assert total_cost == Decimal("100.00")