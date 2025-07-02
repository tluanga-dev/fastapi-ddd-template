import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.application.use_cases.rental_return.initiate_return_use_case import InitiateReturnUseCase
from src.application.use_cases.rental_return.calculate_late_fee_use_case import CalculateLateFeeUseCase
from src.application.use_cases.rental_return.process_partial_return_use_case import ProcessPartialReturnUseCase
from src.application.use_cases.rental_return.assess_damage_use_case import AssessDamageUseCase
from src.application.use_cases.rental_return.finalize_return_use_case import FinalizeReturnUseCase
from src.application.use_cases.rental_return.release_deposit_use_case import ReleaseDepositUseCase

from src.domain.entities.rental_return import RentalReturn
from src.domain.entities.rental_return_line import RentalReturnLine
from src.domain.entities.inspection_report import InspectionReport
from src.domain.entities.transaction_header import TransactionHeader
from src.domain.entities.transaction_line import TransactionLine
from src.domain.entities.inventory_unit import InventoryUnit

from src.domain.value_objects.rental_return_type import ReturnType, ReturnStatus
from src.domain.value_objects.transaction_type import TransactionType, TransactionStatus, LineItemType
from src.domain.value_objects.item_type import ConditionGrade, InventoryStatus
from src.domain.value_objects.inspection_type import InspectionStatus, DamageSeverity


class TestInitiateReturnUseCase:
    """Test cases for InitiateReturnUseCase."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            'return_repository': AsyncMock(),
            'line_repository': AsyncMock(),
            'transaction_repository': AsyncMock(),
            'transaction_line_repository': AsyncMock(),
            'inventory_repository': AsyncMock()
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mock repositories."""
        return InitiateReturnUseCase(**mock_repositories)
    
    @pytest.fixture
    def sample_transaction(self):
        """Create sample rental transaction."""
        return TransactionHeader(
            transaction_number="TRX-001",
            customer_id=uuid4(),
            location_id=uuid4(),
            transaction_type=TransactionType.RENTAL,
            status=TransactionStatus.IN_PROGRESS,
            transaction_date=datetime.now(),
            rental_start_date=date.today(),
            rental_end_date=date.today() + timedelta(days=7),
            deposit_amount=Decimal("100.00")
        )
    
    @pytest.fixture
    def sample_transaction_lines(self):
        """Create sample transaction lines."""
        return [
            TransactionLine(
                transaction_id=uuid4(),
                line_number=1,
                line_type=LineItemType.PRODUCT,
                inventory_unit_id=uuid4(),
                quantity=Decimal("2"),
                unit_price=Decimal("50.00")
            ),
            TransactionLine(
                transaction_id=uuid4(),
                line_number=2,
                line_type=LineItemType.PRODUCT,
                inventory_unit_id=uuid4(),
                quantity=Decimal("1"),
                unit_price=Decimal("75.00")
            )
        ]
    
    @pytest.fixture
    def sample_inventory_units(self, sample_transaction_lines):
        """Create sample inventory units."""
        return [
            InventoryUnit(
                sku_id=uuid4(),
                location_id=uuid4(),
                condition_grade=ConditionGrade.A,
                status=InventoryStatus.RENTED
            ) for line in sample_transaction_lines
        ]
    
    async def test_initiate_return_success(
        self, 
        use_case, 
        mock_repositories, 
        sample_transaction, 
        sample_transaction_lines,
        sample_inventory_units
    ):
        """Test successful return initiation."""
        # Setup mocks
        mock_repositories['transaction_repository'].get_by_id.return_value = sample_transaction
        mock_repositories['transaction_line_repository'].get_by_transaction.return_value = sample_transaction_lines
        mock_repositories['return_repository'].get_by_transaction_id.return_value = []
        
        # Mock inventory units
        mock_repositories['inventory_repository'].get_by_id.side_effect = sample_inventory_units
        
        # Mock creation
        created_return = RentalReturn(
            rental_transaction_id=sample_transaction.id,
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
        mock_repositories['return_repository'].create.return_value = created_return
        mock_repositories['line_repository'].create_batch.return_value = []
        
        # Execute
        return_items = [
            {"inventory_unit_id": sample_transaction_lines[0].inventory_unit_id, "quantity": 2},
            {"inventory_unit_id": sample_transaction_lines[1].inventory_unit_id, "quantity": 1}
        ]
        
        result = await use_case.execute(
            rental_transaction_id=sample_transaction.id,
            return_date=date.today(),
            return_items=return_items,
            processed_by="test_user"
        )
        
        # Verify
        assert result.rental_transaction_id == sample_transaction.id
        assert result.return_status == ReturnStatus.INITIATED
        mock_repositories['return_repository'].create.assert_called_once()
    
    async def test_initiate_return_invalid_transaction(self, use_case, mock_repositories):
        """Test return initiation with invalid transaction."""
        # Setup mocks
        mock_repositories['transaction_repository'].get_by_id.return_value = None
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(
                rental_transaction_id=uuid4(),
                return_date=date.today(),
                return_items=[],
                processed_by="test_user"
            )
    
    async def test_initiate_return_invalid_quantity(
        self, 
        use_case, 
        mock_repositories, 
        sample_transaction, 
        sample_transaction_lines,
        sample_inventory_units
    ):
        """Test return initiation with invalid quantity."""
        # Setup mocks
        mock_repositories['transaction_repository'].get_by_id.return_value = sample_transaction
        mock_repositories['transaction_line_repository'].get_by_transaction.return_value = sample_transaction_lines
        mock_repositories['return_repository'].get_by_transaction_id.return_value = []
        mock_repositories['inventory_repository'].get_by_id.side_effect = sample_inventory_units
        
        # Execute with invalid quantity
        return_items = [
            {"inventory_unit_id": sample_transaction_lines[0].inventory_unit_id, "quantity": 5}  # More than rented
        ]
        
        with pytest.raises(ValueError, match="Cannot return"):
            await use_case.execute(
                rental_transaction_id=sample_transaction.id,
                return_date=date.today(),
                return_items=return_items,
                processed_by="test_user"
            )


class TestCalculateLateFeeUseCase:
    """Test cases for CalculateLateFeeUseCase."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            'return_repository': AsyncMock(),
            'line_repository': AsyncMock(),
            'transaction_repository': AsyncMock(),
            'sku_repository': AsyncMock()
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mock repositories."""
        return CalculateLateFeeUseCase(**mock_repositories)
    
    @pytest.fixture
    def late_return(self):
        """Create a late rental return."""
        return RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            expected_return_date=date.today() - timedelta(days=1),  # Past date
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
    
    @pytest.fixture
    def return_lines(self, late_return):
        """Create return lines."""
        return [
            RentalReturnLine(
                return_id=late_return.id,
                inventory_unit_id=uuid4(),
                original_quantity=2,
                returned_quantity=2
            ),
            RentalReturnLine(
                return_id=late_return.id,
                inventory_unit_id=uuid4(),
                original_quantity=1,
                returned_quantity=1
            )
        ]
    
    async def test_calculate_late_fee_success(
        self, 
        use_case, 
        mock_repositories, 
        late_return, 
        return_lines
    ):
        """Test successful late fee calculation."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = late_return
        mock_repositories['transaction_repository'].get_by_id.return_value = MagicMock()
        mock_repositories['line_repository'].get_by_return_id.return_value = return_lines
        mock_repositories['line_repository'].update.return_value = None
        mock_repositories['return_repository'].update.return_value = late_return
        
        # Execute
        result = await use_case.execute(
            return_id=late_return.id,
            daily_late_fee_rate=Decimal("5.00"),
            updated_by="system"
        )
        
        # Verify
        assert result["is_late"] is True
        assert result["days_late"] > 0
        assert result["total_late_fee"] > 0
        assert len(result["line_fees"]) == 2
    
    async def test_calculate_late_fee_not_late(self, use_case, mock_repositories):
        """Test late fee calculation for non-late return."""
        # Create on-time return
        on_time_return = RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            expected_return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
        
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = on_time_return
        
        # Execute
        result = await use_case.execute(
            return_id=on_time_return.id,
            daily_late_fee_rate=Decimal("5.00"),
            updated_by="system"
        )
        
        # Verify
        assert result["is_late"] is False
        assert result["days_late"] == 0
        assert result["total_late_fee"] == 0.0
    
    async def test_calculate_projected_late_fee(
        self, 
        use_case, 
        mock_repositories, 
        late_return, 
        return_lines
    ):
        """Test projected late fee calculation."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = late_return
        mock_repositories['line_repository'].get_by_return_id.return_value = return_lines
        
        # Execute
        future_date = date.today() + timedelta(days=365)
        result = await use_case.calculate_projected_late_fee(
            return_id=late_return.id,
            projected_return_date=future_date,
            daily_late_fee_rate=Decimal("5.00")
        )
        
        # Verify
        assert result["would_be_late"] is True
        assert result["projected_days_late"] > 0
        assert result["projected_late_fee"] > 0


class TestProcessPartialReturnUseCase:
    """Test cases for ProcessPartialReturnUseCase."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            'return_repository': AsyncMock(),
            'line_repository': AsyncMock(),
            'inventory_repository': AsyncMock(),
            'stock_repository': AsyncMock()
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mock repositories."""
        return ProcessPartialReturnUseCase(**mock_repositories)
    
    @pytest.fixture
    def partial_return(self):
        """Create a partial return."""
        return RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.PARTIAL,
            return_status=ReturnStatus.INITIATED
        )
    
    @pytest.fixture
    def return_lines(self, partial_return):
        """Create return lines for partial return."""
        line1 = RentalReturnLine(
            return_id=partial_return.id,
            inventory_unit_id=uuid4(),
            original_quantity=3,
            returned_quantity=0  # Not yet returned
        )
        
        line2 = RentalReturnLine(
            return_id=partial_return.id,
            inventory_unit_id=uuid4(),
            original_quantity=2,
            returned_quantity=0  # Not yet returned
        )
        
        return [line1, line2]
    
    async def test_process_partial_return_success(
        self, 
        use_case, 
        mock_repositories, 
        partial_return, 
        return_lines
    ):
        """Test successful partial return processing."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = partial_return
        mock_repositories['line_repository'].get_by_return_id.return_value = return_lines
        mock_repositories['line_repository'].update.return_value = None
        mock_repositories['return_repository'].update.return_value = partial_return
        mock_repositories['inventory_repository'].get_by_id.return_value = MagicMock()
        mock_repositories['inventory_repository'].update.return_value = None
        mock_repositories['stock_repository'].get_by_sku_location.return_value = MagicMock()
        mock_repositories['stock_repository'].update.return_value = None
        
        # Execute
        line_updates = [
            {
                "line_id": return_lines[0].id,
                "returned_quantity": 2,
                "condition_grade": "A",
                "notes": "Good condition"
            },
            {
                "line_id": return_lines[1].id,
                "returned_quantity": 1,
                "condition_grade": "B",
                "notes": "Minor wear"
            }
        ]
        
        result = await use_case.execute(
            return_id=partial_return.id,
            line_updates=line_updates,
            updated_by="clerk"
        )
        
        # Verify
        assert result.id == partial_return.id
        assert mock_repositories['line_repository'].update.call_count == 2
    
    async def test_validate_partial_return(
        self, 
        use_case, 
        mock_repositories, 
        partial_return, 
        return_lines
    ):
        """Test partial return validation."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = partial_return
        mock_repositories['line_repository'].get_by_return_id.return_value = return_lines
        
        # Execute
        proposed_quantities = {
            return_lines[0].id: 2,
            return_lines[1].id: 1
        }
        
        result = await use_case.validate_partial_return(
            return_id=partial_return.id,
            proposed_quantities=proposed_quantities
        )
        
        # Verify
        assert result["is_valid"] is True
        assert result["summary"]["lines_being_returned"] == 2
        assert result["summary"]["total_proposed_quantity"] == 3
    
    async def test_validate_partial_return_invalid_quantity(
        self, 
        use_case, 
        mock_repositories, 
        partial_return, 
        return_lines
    ):
        """Test partial return validation with invalid quantities."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = partial_return
        mock_repositories['line_repository'].get_by_return_id.return_value = return_lines
        
        # Execute with invalid quantity
        proposed_quantities = {
            return_lines[0].id: 5,  # More than original quantity (3)
            return_lines[1].id: 1
        }
        
        result = await use_case.validate_partial_return(
            return_id=partial_return.id,
            proposed_quantities=proposed_quantities
        )
        
        # Verify
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0


class TestAssessDamageUseCase:
    """Test cases for AssessDamageUseCase."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            'return_repository': AsyncMock(),
            'line_repository': AsyncMock(),
            'inspection_repository': AsyncMock()
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mock repositories."""
        return AssessDamageUseCase(**mock_repositories)
    
    @pytest.fixture
    def rental_return(self):
        """Create a rental return."""
        return RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.INITIATED
        )
    
    @pytest.fixture
    def return_lines(self, rental_return):
        """Create return lines."""
        return [
            RentalReturnLine(
                return_id=rental_return.id,
                inventory_unit_id=uuid4(),
                original_quantity=1,
                returned_quantity=1
            )
        ]
    
    async def test_assess_damage_success(
        self, 
        use_case, 
        mock_repositories, 
        rental_return, 
        return_lines
    ):
        """Test successful damage assessment."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = rental_return
        mock_repositories['line_repository'].get_by_return_id.return_value = return_lines
        mock_repositories['line_repository'].update.return_value = None
        
        created_report = InspectionReport(
            return_id=rental_return.id,
            inspector_id="inspector123",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        mock_repositories['inspection_repository'].create.return_value = created_report
        mock_repositories['return_repository'].update.return_value = rental_return
        
        # Execute
        line_assessments = [
            {
                "line_id": return_lines[0].id,
                "condition_grade": "C",
                "damage_description": "Minor scratches",
                "estimated_repair_cost": Decimal("25.00"),
                "damage_photos": ["photo1.jpg"]
            }
        ]
        
        result = await use_case.execute(
            return_id=rental_return.id,
            inspector_id="inspector123",
            line_assessments=line_assessments,
            general_notes="Inspection completed"
        )
        
        # Verify
        assert result.return_id == rental_return.id
        assert result.inspector_id == "inspector123"
        mock_repositories['inspection_repository'].create.assert_called_once()
    
    async def test_complete_inspection(self, use_case, mock_repositories):
        """Test inspection completion."""
        # Create inspection report
        inspection_report = InspectionReport(
            return_id=uuid4(),
            inspector_id="inspector",
            inspection_date=datetime.utcnow(),
            inspection_status=InspectionStatus.IN_PROGRESS
        )
        
        # Setup mocks
        mock_repositories['inspection_repository'].get_by_id.return_value = inspection_report
        mock_repositories['inspection_repository'].update.return_value = inspection_report
        
        # Execute
        result = await use_case.complete_inspection(
            inspection_report_id=inspection_report.id,
            approved=True,
            approver_id="manager",
            approval_notes="Approved"
        )
        
        # Verify
        assert result.id == inspection_report.id
        mock_repositories['inspection_repository'].update.assert_called_once()


class TestFinalizeReturnUseCase:
    """Test cases for FinalizeReturnUseCase."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            'return_repository': AsyncMock(),
            'line_repository': AsyncMock(),
            'transaction_repository': AsyncMock(),
            'inventory_repository': AsyncMock(),
            'stock_repository': AsyncMock()
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mock repositories."""
        return FinalizeReturnUseCase(**mock_repositories)
    
    @pytest.fixture
    def completable_return(self):
        """Create a return ready for finalization."""
        return RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.IN_INSPECTION
        )
    
    @pytest.fixture
    def processed_lines(self, completable_return):
        """Create processed return lines."""
        line = RentalReturnLine(
            return_id=completable_return.id,
            inventory_unit_id=uuid4(),
            original_quantity=1,
            returned_quantity=1,
            condition_grade=ConditionGrade.A
        )
        line.process_line("processor")
        return [line]
    
    async def test_finalize_return_success(
        self, 
        use_case, 
        mock_repositories, 
        completable_return, 
        processed_lines
    ):
        """Test successful return finalization."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = completable_return
        mock_repositories['line_repository'].get_by_return_id.return_value = processed_lines
        mock_repositories['inventory_repository'].get_by_id.return_value = MagicMock()
        mock_repositories['inventory_repository'].update.return_value = None
        mock_repositories['stock_repository'].get_by_sku_location.return_value = MagicMock()
        mock_repositories['stock_repository'].update.return_value = None
        mock_repositories['transaction_repository'].get_by_id.return_value = MagicMock()
        mock_repositories['transaction_repository'].update.return_value = None
        mock_repositories['return_repository'].update.return_value = completable_return
        
        # Execute
        result = await use_case.execute(
            return_id=completable_return.id,
            finalized_by="manager"
        )
        
        # Verify
        assert result.id == completable_return.id
        mock_repositories['return_repository'].update.assert_called()
    
    async def test_get_finalization_preview(
        self, 
        use_case, 
        mock_repositories, 
        completable_return, 
        processed_lines
    ):
        """Test finalization preview."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = completable_return
        mock_repositories['line_repository'].get_by_return_id.return_value = processed_lines
        
        # Execute
        result = await use_case.get_finalization_preview(completable_return.id)
        
        # Verify
        assert result["return_id"] == str(completable_return.id)
        assert "can_finalize" in result
        assert "fee_totals" in result
        assert "inventory_changes" in result


class TestReleaseDepositUseCase:
    """Test cases for ReleaseDepositUseCase."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            'return_repository': AsyncMock(),
            'transaction_repository': AsyncMock()
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories):
        """Create use case with mock repositories."""
        return ReleaseDepositUseCase(**mock_repositories)
    
    @pytest.fixture
    def completed_return(self):
        """Create a completed return."""
        return RentalReturn(
            rental_transaction_id=uuid4(),
            return_date=date.today(),
            return_type=ReturnType.FULL,
            return_status=ReturnStatus.COMPLETED,
            total_late_fee=Decimal("10.00"),
            total_damage_fee=Decimal("15.00")
        )
    
    @pytest.fixture
    def rental_transaction(self, completed_return):
        """Create rental transaction with deposit."""
        return TransactionHeader(
            customer_id=uuid4(),
            transaction_type=TransactionType.RENTAL,
            status=TransactionStatus.COMPLETED,
            transaction_date=date.today(),
            deposit_amount=Decimal("100.00")
        )
    
    async def test_release_deposit_success(
        self, 
        use_case, 
        mock_repositories, 
        completed_return, 
        rental_transaction
    ):
        """Test successful deposit release."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = completed_return
        mock_repositories['transaction_repository'].get_by_id.return_value = rental_transaction
        mock_repositories['return_repository'].update.return_value = completed_return
        
        # Execute
        result = await use_case.execute(
            return_id=completed_return.id,
            processed_by="clerk"
        )
        
        # Verify
        assert result["return_id"] == str(completed_return.id)
        assert result["original_deposit"] == 100.0
        assert result["release_amount"] == 75.0  # 100 - (10 + 15)
        assert result["withheld_amount"] == 25.0
    
    async def test_calculate_deposit_preview(
        self, 
        use_case, 
        mock_repositories, 
        completed_return, 
        rental_transaction
    ):
        """Test deposit release preview."""
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = completed_return
        mock_repositories['transaction_repository'].get_by_id.return_value = rental_transaction
        
        # Execute
        result = await use_case.calculate_deposit_preview(completed_return.id)
        
        # Verify
        assert result["return_id"] == str(completed_return.id)
        assert result["can_release_deposit"] is True
        assert "deposit_calculation" in result
    
    async def test_reverse_deposit_release(
        self, 
        use_case, 
        mock_repositories, 
        completed_return
    ):
        """Test deposit release reversal."""
        # Setup completed return with deposit released
        completed_return.deposit_released = True
        completed_return.deposit_release_amount = Decimal("75.00")
        
        # Setup mocks
        mock_repositories['return_repository'].get_by_id.return_value = completed_return
        mock_repositories['return_repository'].update.return_value = completed_return
        
        # Execute
        result = await use_case.reverse_deposit_release(
            return_id=completed_return.id,
            reason="Correction needed",
            processed_by="manager"
        )
        
        # Verify
        assert result["return_id"] == str(completed_return.id)
        assert result["reversal_reason"] == "Correction needed"
        assert result["status"] == "reversed"