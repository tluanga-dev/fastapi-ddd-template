import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.entities.inventory_unit import InventoryUnit
from src.domain.value_objects.item_type import InventoryStatus, ConditionGrade


class TestInventoryUnit:
    """Test cases for InventoryUnit entity."""
    
    def test_create_inventory_unit(self):
        """Test creating a new inventory unit."""
        unit = InventoryUnit(
            inventory_code="INV-001",
            sku_id=uuid4(),
            location_id=uuid4(),
            serial_number="SN123456",
            current_status=InventoryStatus.AVAILABLE_SALE,
            condition_grade=ConditionGrade.A
        )
        
        assert unit.inventory_code == "INV-001"
        assert unit.serial_number == "SN123456"
        assert unit.current_status == InventoryStatus.AVAILABLE_SALE
        assert unit.condition_grade == ConditionGrade.A
        assert unit.total_rental_days == 0
        assert unit.rental_count == 0
        assert isinstance(unit.id, UUID)
        assert unit.is_active is True
    
    def test_create_inventory_unit_with_optional_fields(self):
        """Test creating inventory unit with all optional fields."""
        purchase_date = date.today()
        purchase_cost = Decimal("999.99")
        
        unit = InventoryUnit(
            inventory_code="INV-002",
            sku_id=uuid4(),
            location_id=uuid4(),
            serial_number="SN789012",
            current_status=InventoryStatus.AVAILABLE_RENT,
            condition_grade=ConditionGrade.B,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            current_value=Decimal("850.00"),
            notes="Test notes",
            created_by="test_user"
        )
        
        assert unit.purchase_date == purchase_date
        assert unit.purchase_cost == purchase_cost
        assert unit.current_value == Decimal("850.00")
        assert unit.notes == "Test notes"
        assert unit.created_by == "test_user"
    
    def test_inventory_code_validation(self):
        """Test inventory code validation."""
        # Empty inventory code
        with pytest.raises(ValueError, match="Inventory code is required"):
            InventoryUnit(
                inventory_code="",
                sku_id=uuid4(),
                location_id=uuid4()
            )
        
        # Whitespace only inventory code
        with pytest.raises(ValueError, match="Inventory code is required"):
            InventoryUnit(
                inventory_code="   ",
                sku_id=uuid4(),
                location_id=uuid4()
            )
    
    def test_update_status(self):
        """Test updating inventory status."""
        unit = InventoryUnit(
            inventory_code="INV-003",
            sku_id=uuid4(),
            location_id=uuid4(),
            current_status=InventoryStatus.AVAILABLE_SALE
        )
        
        # Test valid status update
        unit.update_status(InventoryStatus.RESERVED_SALE, "test_user")
        assert unit.current_status == InventoryStatus.RESERVED_SALE
        assert unit.updated_by == "test_user"
        assert unit.updated_at is not None
    
    def test_status_transition_validation(self):
        """Test status transition validation."""
        unit = InventoryUnit(
            inventory_code="INV-004",
            sku_id=uuid4(),
            location_id=uuid4(),
            current_status=InventoryStatus.AVAILABLE_SALE
        )
        
        # Valid transitions
        assert unit.can_transition_to(InventoryStatus.RESERVED_SALE) is True
        assert unit.can_transition_to(InventoryStatus.AVAILABLE_RENT) is True
        
        # Invalid transitions
        assert unit.can_transition_to(InventoryStatus.RENTED) is False
        assert unit.can_transition_to(InventoryStatus.SOLD) is False
    
    def test_all_status_transitions(self):
        """Test all defined status transitions."""
        # Test AVAILABLE_SALE transitions
        unit = InventoryUnit(
            inventory_code="INV-005",
            sku_id=uuid4(),
            location_id=uuid4(),
            current_status=InventoryStatus.AVAILABLE_SALE
        )
        assert unit.can_transition_to(InventoryStatus.RESERVED_SALE) is True
        assert unit.can_transition_to(InventoryStatus.INSPECTION_PENDING) is True
        
        # Test RESERVED_SALE transitions
        unit.current_status = InventoryStatus.RESERVED_SALE
        assert unit.can_transition_to(InventoryStatus.SOLD) is True
        assert unit.can_transition_to(InventoryStatus.AVAILABLE_SALE) is True
        
        # Test RENTED transitions
        unit.current_status = InventoryStatus.RENTED
        assert unit.can_transition_to(InventoryStatus.INSPECTION_PENDING) is True
        assert unit.can_transition_to(InventoryStatus.DAMAGED) is True
    
    def test_update_condition(self):
        """Test updating condition grade."""
        unit = InventoryUnit(
            inventory_code="INV-006",
            sku_id=uuid4(),
            location_id=uuid4(),
            condition_grade=ConditionGrade.A
        )
        
        unit.update_condition(ConditionGrade.B, "Condition update note", "inspector")
        assert unit.condition_grade == ConditionGrade.B
        assert unit.updated_by == "inspector"
        assert "Condition update note" in unit.notes
    
    def test_record_inspection(self):
        """Test recording inspection."""
        unit = InventoryUnit(
            inventory_code="INV-007",
            sku_id=uuid4(),
            location_id=uuid4()
        )
        
        unit.record_inspection(ConditionGrade.B, "Inspection note", "inspector")
        
        assert unit.last_inspection_date == date.today()
        assert unit.condition_grade == ConditionGrade.B
        assert unit.updated_by == "inspector"
        assert "Inspection note" in unit.notes
    
    def test_update_location(self):
        """Test updating location."""
        old_location = uuid4()
        new_location = uuid4()
        
        unit = InventoryUnit(
            inventory_code="INV-008",
            sku_id=uuid4(),
            location_id=old_location
        )
        
        unit.update_location(new_location, "transfer_user")
        assert unit.location_id == new_location
        assert unit.updated_by == "transfer_user"
        
        # Test cannot move if rented
        unit.current_status = InventoryStatus.RENTED
        with pytest.raises(ValueError, match="Cannot move inventory in RENTED status"):
            unit.update_location(uuid4())
    
    def test_increment_rental_stats(self):
        """Test incrementing rental statistics."""
        unit = InventoryUnit(
            inventory_code="INV-009",
            sku_id=uuid4(),
            location_id=uuid4()
        )
        
        assert unit.rental_count == 0
        assert unit.total_rental_days == 0
        
        unit.increment_rental_stats(7, "rental_system")
        assert unit.rental_count == 1
        assert unit.total_rental_days == 7
        
        unit.increment_rental_stats(3, "rental_system")
        assert unit.rental_count == 2
        assert unit.total_rental_days == 10
    
    def test_deactivate(self):
        """Test deactivating inventory unit."""
        unit = InventoryUnit(
            inventory_code="INV-010",
            sku_id=uuid4(),
            location_id=uuid4()
        )
        
        assert unit.is_active is True
        
        unit.is_active = False
        unit.update_timestamp("admin")
        assert unit.is_active is False
        assert unit.updated_by == "admin"
    
    def test_is_rentable(self):
        """Test checking if unit is rentable."""
        unit = InventoryUnit(
            inventory_code="INV-011",
            sku_id=uuid4(),
            location_id=uuid4(),
            current_status=InventoryStatus.AVAILABLE_RENT
        )
        
        assert unit.is_rentable is True
        
        unit.current_status = InventoryStatus.RENTED
        assert unit.is_rentable is False
        
        unit.current_status = InventoryStatus.AVAILABLE_SALE
        assert unit.is_rentable is False
    
    def test_is_saleable(self):
        """Test checking if unit is saleable."""
        unit = InventoryUnit(
            inventory_code="INV-012",
            sku_id=uuid4(),
            location_id=uuid4(),
            current_status=InventoryStatus.AVAILABLE_SALE
        )
        
        assert unit.is_saleable is True
        
        unit.current_status = InventoryStatus.SOLD
        assert unit.is_saleable is False
        
        unit.current_status = InventoryStatus.AVAILABLE_RENT
        assert unit.is_saleable is False
    
    def test_requires_inspection(self):
        """Test checking if unit requires inspection."""
        unit = InventoryUnit(
            inventory_code="INV-013",
            sku_id=uuid4(),
            location_id=uuid4()
        )
        
        # Default status should not require inspection
        assert unit.requires_inspection is False
        
        # Inspection pending status
        unit.current_status = InventoryStatus.INSPECTION_PENDING
        assert unit.requires_inspection is True
        
        # Other status
        unit.current_status = InventoryStatus.AVAILABLE_RENT
        assert unit.requires_inspection is False
    
    def test_update_value(self):
        """Test updating current value."""
        unit = InventoryUnit(
            inventory_code="INV-014",
            sku_id=uuid4(),
            location_id=uuid4(),
            purchase_cost=Decimal("1000.00")
        )
        
        unit.update_value(Decimal("900.00"), "valuation_system")
        assert unit.current_value == Decimal("900.00")
        assert unit.updated_by == "valuation_system"
    
    def test_entity_string_representation(self):
        """Test string representation of entity."""
        unit = InventoryUnit(
            inventory_code="INV-015",
            sku_id=uuid4(),
            location_id=uuid4()
        )
        
        str_repr = str(unit)
        assert "INV-015" in str_repr
        assert "InventoryUnit" in str_repr