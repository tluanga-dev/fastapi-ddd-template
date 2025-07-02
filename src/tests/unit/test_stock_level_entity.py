import pytest
from uuid import UUID, uuid4

from src.domain.entities.stock_level import StockLevel


class TestStockLevel:
    """Test cases for StockLevel entity."""
    
    def test_create_stock_level(self):
        """Test creating a new stock level."""
        sku_id = uuid4()
        location_id = uuid4()
        
        stock = StockLevel(
            sku_id=sku_id,
            location_id=location_id,
            quantity_on_hand=100,
            quantity_available=100,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0,
            reorder_point=20,
            reorder_quantity=50
        )
        
        assert stock.sku_id == sku_id
        assert stock.location_id == location_id
        assert stock.quantity_on_hand == 100
        assert stock.quantity_available == 100
        assert stock.quantity_reserved == 0
        assert stock.reorder_point == 20
        assert stock.reorder_quantity == 50
        assert isinstance(stock.id, UUID)
        assert stock.is_active is True
    
    def test_quantity_validation(self):
        """Test quantity validation on creation."""
        # Valid quantities
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=80,
            quantity_reserved=15,
            quantity_in_transit=0,
            quantity_damaged=5
        )
        assert stock.quantity_on_hand == 100
        
        # Invalid quantities - mismatch
        with pytest.raises(ValueError, match="Quantity mismatch"):
            StockLevel(
                sku_id=uuid4(),
                location_id=uuid4(),
                quantity_on_hand=100,
                quantity_available=90,
                quantity_reserved=15,  # 90 + 15 = 105, not 100
                quantity_in_transit=0,
                quantity_damaged=0
            )
    
    def test_negative_quantity_validation(self):
        """Test that negative quantities are not allowed."""
        with pytest.raises(ValueError, match="cannot be negative"):
            StockLevel(
                sku_id=uuid4(),
                location_id=uuid4(),
                quantity_on_hand=-1,
                quantity_available=0,
                quantity_reserved=0,
                quantity_in_transit=0,
                quantity_damaged=0
            )
        
        with pytest.raises(ValueError, match="cannot be negative"):
            StockLevel(
                sku_id=uuid4(),
                location_id=uuid4(),
                quantity_on_hand=10,
                quantity_available=-5,
                quantity_reserved=15,
                quantity_in_transit=0,
                quantity_damaged=0
            )
    
    def test_receive_stock(self):
        """Test receiving stock."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=50,
            quantity_available=50,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0
        )
        
        stock.receive_stock(25, "warehouse_user")
        assert stock.quantity_on_hand == 75
        assert stock.quantity_available == 75
        assert stock.updated_by == "warehouse_user"
        
        # Test negative quantity
        with pytest.raises(ValueError, match="Receive quantity must be positive"):
            stock.receive_stock(-5)
    
    def test_reserve_stock(self):
        """Test reserving stock."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=100,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0
        )
        
        stock.reserve_stock(30, "sales_user")
        assert stock.quantity_available == 70
        assert stock.quantity_reserved == 30
        assert stock.quantity_on_hand == 100  # Total unchanged
        
        # Test insufficient stock
        with pytest.raises(ValueError, match="Cannot reserve 80 units"):
            stock.reserve_stock(80)  # Only 70 available
    
    def test_release_reservation(self):
        """Test releasing reserved stock."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=70,
            quantity_reserved=30,
            quantity_in_transit=0,
            quantity_damaged=0
        )
        
        stock.release_reservation(20, "sales_user")
        assert stock.quantity_available == 90
        assert stock.quantity_reserved == 10
        
        # Test releasing more than reserved
        with pytest.raises(ValueError, match="Cannot release 15 units"):
            stock.release_reservation(15)  # Only 10 reserved
    
    def test_confirm_sale(self):
        """Test confirming sale from reserved stock."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=70,
            quantity_reserved=30,
            quantity_in_transit=0,
            quantity_damaged=0
        )
        
        stock.confirm_sale(20, "sales_user")
        assert stock.quantity_on_hand == 80
        assert stock.quantity_reserved == 10
        assert stock.quantity_available == 70  # Available unchanged
        
        # Test confirming more than reserved
        with pytest.raises(ValueError, match="Cannot sell 15 units"):
            stock.confirm_sale(15)
    
    def test_mark_damaged(self):
        """Test marking stock as damaged."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=100,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0
        )
        
        stock.mark_damaged(10, "inspector")
        assert stock.quantity_available == 90
        assert stock.quantity_damaged == 10
        assert stock.quantity_on_hand == 100  # Total unchanged
        
        # Test damaging more than available
        with pytest.raises(ValueError, match="Cannot mark 95 units as damaged"):
            stock.mark_damaged(95)
    
    def test_repair_damaged(self):
        """Test repairing damaged stock."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=85,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=15
        )
        
        stock.repair_damaged(5, "inspector")
        assert stock.quantity_available == 90
        assert stock.quantity_damaged == 10
        
        # Test repairing more than damaged
        with pytest.raises(ValueError, match="Cannot repair 15 units"):
            stock.repair_damaged(15)
    
    def test_update_reorder_levels(self):
        """Test updating reorder levels."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=100,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0,
            reorder_point=20
        )
        
        stock.update_reorder_levels(30, 50, 200, "inventory_manager")
        assert stock.reorder_point == 30
        assert stock.reorder_quantity == 50
        assert stock.maximum_stock == 200
        assert stock.updated_by == "inventory_manager"
        
        # Test negative reorder point
        with pytest.raises(ValueError, match="Reorder point cannot be negative"):
            stock.update_reorder_levels(-5, 50)
    
    def test_needs_reorder_property(self):
        """Test checking if stock needs reorder."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=15,
            quantity_reserved=85,
            quantity_in_transit=0,
            quantity_damaged=0,
            reorder_point=20
        )
        
        assert stock.needs_reorder is True
        
        stock.quantity_available = 25
        assert stock.needs_reorder is False
    
    def test_suggested_order_quantity(self):
        """Test calculating suggested order quantity."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=15,
            quantity_reserved=85,
            quantity_in_transit=0,
            quantity_damaged=0,
            reorder_point=20,
            reorder_quantity=50
        )
        
        # Should suggest reorder quantity when below reorder point
        assert stock.suggested_order_quantity == 50
        
        # No reorder needed when above reorder point
        stock.quantity_available = 25
        assert stock.suggested_order_quantity == 0
    
    def test_suggested_order_with_maximum_stock(self):
        """Test suggested order quantity with maximum stock."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=15,
            quantity_reserved=85,
            quantity_in_transit=5,
            quantity_damaged=0,
            reorder_point=20,
            reorder_quantity=50,
            maximum_stock=150
        )
        
        # Should order up to maximum stock considering in-transit
        # max_order = 150 - 100 - 5 = 45
        # Should return min(50, 45) = 45
        assert stock.suggested_order_quantity == 45
        
        # Without maximum stock, use reorder quantity
        stock.maximum_stock = None
        assert stock.suggested_order_quantity == 50
    
    def test_complex_stock_operations(self):
        """Test a series of complex stock operations."""
        stock = StockLevel(
            sku_id=uuid4(),
            location_id=uuid4(),
            quantity_on_hand=100,
            quantity_available=100,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0,
            reorder_point=20,
            reorder_quantity=50
        )
        
        # Reserve some stock
        stock.reserve_stock(40)
        assert stock.quantity_available == 60
        assert stock.quantity_reserved == 40
        
        # Confirm sale of part of reserved
        stock.confirm_sale(25)
        assert stock.quantity_on_hand == 75
        assert stock.quantity_reserved == 15
        assert stock.quantity_available == 60
        
        # Mark some as damaged
        stock.mark_damaged(10)
        assert stock.quantity_available == 50
        assert stock.quantity_damaged == 10
        assert stock.quantity_on_hand == 75
        
        # Receive new stock
        stock.receive_stock(50)
        assert stock.quantity_on_hand == 125
        assert stock.quantity_available == 100  # 50 + 50
        
        # Verify final state
        assert stock.quantity_reserved == 15
        assert stock.quantity_damaged == 10
        
        # Validate quantities
        total = stock.quantity_available + stock.quantity_reserved + stock.quantity_damaged
        assert total == stock.quantity_on_hand
    
    def test_entity_string_representation(self):
        """Test string representation of entity."""
        sku_id = uuid4()
        location_id = uuid4()
        
        stock = StockLevel(
            sku_id=sku_id,
            location_id=location_id,
            quantity_on_hand=100,
            quantity_available=100,
            quantity_reserved=0,
            quantity_in_transit=0,
            quantity_damaged=0
        )
        
        str_repr = str(stock)
        assert "StockLevel" in str_repr
        assert str(sku_id) in str_repr
        assert str(location_id) in str_repr