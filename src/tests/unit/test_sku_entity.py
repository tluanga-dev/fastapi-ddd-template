import pytest
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from src.domain.entities.sku import SKU


class TestSKUEntity:
    """Unit tests for SKU entity."""
    
    def test_create_valid_sku(self):
        """Test creating a valid SKU."""
        item_id = uuid4()
        
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=item_id,
            barcode="1234567890",
            model_number="MODEL-123",
            weight=Decimal("2.5"),
            dimensions={"length": Decimal("10"), "width": Decimal("5"), "height": Decimal("3")},
            is_rentable=True,
            is_saleable=True,
            min_rental_days=3,
            max_rental_days=30,
            rental_base_price=Decimal("10.00"),
            sale_base_price=Decimal("100.00")
        )
        
        assert sku.sku_code == "SKU001"
        assert sku.sku_name == "Test SKU"
        assert sku.item_id == item_id
        assert sku.barcode == "1234567890"
        assert sku.model_number == "MODEL-123"
        assert sku.weight == Decimal("2.5")
        assert sku.dimensions["length"] == Decimal("10")
        assert sku.is_rentable is True
        assert sku.is_saleable is True
        assert sku.min_rental_days == 3
        assert sku.max_rental_days == 30
        assert sku.rental_base_price == Decimal("10.00")
        assert sku.sale_base_price == Decimal("100.00")
        assert sku.is_active is True
        assert sku.id is not None
        assert isinstance(sku.created_at, datetime)
    
    def test_create_minimal_sku(self):
        """Test creating SKU with minimal required fields."""
        sku = SKU(
            sku_code="SKU002",
            sku_name="Minimal SKU",
            item_id=uuid4()
        )
        
        assert sku.barcode is None
        assert sku.model_number is None
        assert sku.weight is None
        assert sku.dimensions == {}
        assert sku.is_rentable is False
        assert sku.is_saleable is True
        assert sku.min_rental_days == 1
        assert sku.max_rental_days is None
        assert sku.rental_base_price is None
        assert sku.sale_base_price is None
    
    def test_sku_code_required(self):
        """Test that SKU code is required."""
        with pytest.raises(ValueError, match="SKU code is required"):
            SKU(
                sku_code="",
                sku_name="Test SKU",
                item_id=uuid4()
            )
    
    def test_sku_name_required(self):
        """Test that SKU name is required."""
        with pytest.raises(ValueError, match="SKU name is required"):
            SKU(
                sku_code="SKU001",
                sku_name="",
                item_id=uuid4()
            )
    
    def test_item_id_required(self):
        """Test that item ID is required."""
        with pytest.raises(ValueError, match="Item ID is required"):
            SKU(
                sku_code="SKU001",
                sku_name="Test SKU",
                item_id=None
            )
    
    def test_sku_must_be_rentable_or_saleable(self):
        """Test that SKU must be either rentable or saleable."""
        with pytest.raises(ValueError, match="SKU must be either rentable or saleable"):
            SKU(
                sku_code="SKU001",
                sku_name="Test SKU",
                item_id=uuid4(),
                is_rentable=False,
                is_saleable=False
            )
    
    def test_rental_validation(self):
        """Test rental-specific validations."""
        # Test min rental days must be at least 1
        with pytest.raises(ValueError, match="Minimum rental days must be at least 1"):
            SKU(
                sku_code="SKU001",
                sku_name="Test SKU",
                item_id=uuid4(),
                is_rentable=True,
                min_rental_days=0
            )
        
        # Test max rental days must be >= min
        with pytest.raises(ValueError, match="Maximum rental days must be greater than or equal to minimum"):
            SKU(
                sku_code="SKU001",
                sku_name="Test SKU",
                item_id=uuid4(),
                is_rentable=True,
                min_rental_days=7,
                max_rental_days=5
            )
        
        # Test rental price cannot be negative
        with pytest.raises(ValueError, match="Rental base price cannot be negative"):
            SKU(
                sku_code="SKU001",
                sku_name="Test SKU",
                item_id=uuid4(),
                is_rentable=True,
                rental_base_price=Decimal("-10.00")
            )
    
    def test_sale_validation(self):
        """Test sale-specific validations."""
        # Test sale price cannot be negative
        with pytest.raises(ValueError, match="Sale base price cannot be negative"):
            SKU(
                sku_code="SKU001",
                sku_name="Test SKU",
                item_id=uuid4(),
                is_saleable=True,
                sale_base_price=Decimal("-100.00")
            )
    
    def test_physical_specs_validation(self):
        """Test physical specifications validation."""
        # Test weight cannot be negative
        with pytest.raises(ValueError, match="Weight cannot be negative"):
            SKU(
                sku_code="SKU001",
                sku_name="Test SKU",
                item_id=uuid4(),
                weight=Decimal("-1.5")
            )
        
        # Test dimensions cannot be negative
        with pytest.raises(ValueError, match="Dimension length cannot be negative"):
            SKU(
                sku_code="SKU001",
                sku_name="Test SKU",
                item_id=uuid4(),
                dimensions={"length": Decimal("-10")}
            )
    
    def test_update_basic_info(self):
        """Test updating basic SKU information."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Original Name",
            item_id=uuid4()
        )
        
        original_updated_at = sku.updated_at
        
        sku.update_basic_info(
            sku_name="Updated Name",
            barcode="9876543210",
            model_number="NEW-MODEL",
            updated_by="user123"
        )
        
        assert sku.sku_name == "Updated Name"
        assert sku.barcode == "9876543210"
        assert sku.model_number == "NEW-MODEL"
        assert sku.updated_by == "user123"
        assert sku.updated_at > original_updated_at
    
    def test_update_basic_info_empty_name_fails(self):
        """Test that updating with empty name fails."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4()
        )
        
        with pytest.raises(ValueError, match="SKU name cannot be empty"):
            sku.update_basic_info(sku_name="   ")
    
    def test_update_physical_specs(self):
        """Test updating physical specifications."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4()
        )
        
        sku.update_physical_specs(
            weight=Decimal("3.5"),
            dimensions={"length": Decimal("15"), "width": Decimal("10"), "height": Decimal("5")},
            updated_by="user123"
        )
        
        assert sku.weight == Decimal("3.5")
        assert sku.dimensions["length"] == Decimal("15")
        assert sku.dimensions["width"] == Decimal("10")
        assert sku.dimensions["height"] == Decimal("5")
    
    def test_update_physical_specs_validation(self):
        """Test physical specs update validation."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4()
        )
        
        with pytest.raises(ValueError, match="Weight cannot be negative"):
            sku.update_physical_specs(weight=Decimal("-1"))
        
        with pytest.raises(ValueError, match="Dimension width cannot be negative"):
            sku.update_physical_specs(dimensions={"width": Decimal("-5")})
    
    def test_update_rental_settings(self):
        """Test updating rental settings."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=True,
            min_rental_days=1
        )
        
        sku.update_rental_settings(
            min_rental_days=7,
            max_rental_days=60,
            rental_base_price=Decimal("15.00"),
            updated_by="user123"
        )
        
        assert sku.min_rental_days == 7
        assert sku.max_rental_days == 60
        assert sku.rental_base_price == Decimal("15.00")
    
    def test_update_rental_settings_validation(self):
        """Test rental settings update validation."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=True
        )
        
        with pytest.raises(ValueError, match="Minimum rental days must be at least 1"):
            sku.update_rental_settings(min_rental_days=0)
        
        with pytest.raises(ValueError, match="Rental base price cannot be negative"):
            sku.update_rental_settings(rental_base_price=Decimal("-5"))
    
    def test_update_sale_settings(self):
        """Test updating sale settings."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4()
        )
        
        sku.update_sale_settings(
            sale_base_price=Decimal("150.00"),
            updated_by="user123"
        )
        
        assert sku.sale_base_price == Decimal("150.00")
    
    def test_enable_rental(self):
        """Test enabling rental for SKU."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=False
        )
        
        sku.enable_rental(
            min_days=3,
            base_price=Decimal("20.00"),
            updated_by="user123"
        )
        
        assert sku.is_rentable is True
        assert sku.min_rental_days == 3
        assert sku.rental_base_price == Decimal("20.00")
    
    def test_disable_rental(self):
        """Test disabling rental for SKU."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=True,
            is_saleable=True
        )
        
        sku.disable_rental(updated_by="user123")
        
        assert sku.is_rentable is False
    
    def test_disable_rental_when_not_saleable_fails(self):
        """Test that disabling rental fails when SKU is not saleable."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=True,
            is_saleable=False
        )
        
        with pytest.raises(ValueError, match="Cannot disable rental when sale is also disabled"):
            sku.disable_rental()
    
    def test_enable_sale(self):
        """Test enabling sale for SKU."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=True,
            is_saleable=False
        )
        
        sku.enable_sale(
            base_price=Decimal("200.00"),
            updated_by="user123"
        )
        
        assert sku.is_saleable is True
        assert sku.sale_base_price == Decimal("200.00")
    
    def test_disable_sale(self):
        """Test disabling sale for SKU."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=True,
            is_saleable=True
        )
        
        sku.disable_sale(updated_by="user123")
        
        assert sku.is_saleable is False
    
    def test_disable_sale_when_not_rentable_fails(self):
        """Test that disabling sale fails when SKU is not rentable."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=False,
            is_saleable=True
        )
        
        with pytest.raises(ValueError, match="Cannot disable sale when rental is also disabled"):
            sku.disable_sale()
    
    def test_deactivate_and_activate(self):
        """Test deactivating and activating SKU."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4()
        )
        
        assert sku.is_active is True
        
        sku.deactivate(updated_by="user123")
        assert sku.is_active is False
        assert sku.updated_by == "user123"
        
        sku.activate(updated_by="user456")
        assert sku.is_active is True
        assert sku.updated_by == "user456"
    
    def test_string_representations(self):
        """Test string representations."""
        sku = SKU(
            sku_code="SKU001",
            sku_name="Test SKU",
            item_id=uuid4(),
            is_rentable=True,
            is_saleable=False
        )
        
        assert str(sku) == "SKU(SKU001: Test SKU)"
        assert "SKU001" in repr(sku)
        assert "Test SKU" in repr(sku)
        assert "rentable=True" in repr(sku)
        assert "saleable=False" in repr(sku)