import pytest
from uuid import uuid4
from datetime import datetime

from src.domain.entities.item_master import ItemMaster
from src.domain.value_objects.item_type import ItemType


class TestItemMasterEntity:
    """Unit tests for ItemMaster entity."""
    
    def test_create_valid_item_master(self):
        """Test creating a valid item master."""
        category_id = uuid4()
        brand_id = uuid4()
        
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=category_id,
            item_type=ItemType.PRODUCT,
            brand_id=brand_id,
            description="Test description",
            is_serialized=True
        )
        
        assert item.item_code == "ITEM001"
        assert item.item_name == "Test Item"
        assert item.category_id == category_id
        assert item.item_type == ItemType.PRODUCT
        assert item.brand_id == brand_id
        assert item.description == "Test description"
        assert item.is_serialized is True
        assert item.is_active is True
        assert item.id is not None
        assert isinstance(item.created_at, datetime)
    
    def test_create_item_without_brand(self):
        """Test creating an item without brand."""
        item = ItemMaster(
            item_code="ITEM002",
            item_name="No Brand Item",
            category_id=uuid4(),
            item_type=ItemType.PRODUCT
        )
        
        assert item.brand_id is None
        assert item.description is None
        assert item.is_serialized is False
    
    def test_create_service_item(self):
        """Test creating a service item."""
        item = ItemMaster(
            item_code="SVC001",
            item_name="Test Service",
            category_id=uuid4(),
            item_type=ItemType.SERVICE
        )
        
        assert item.item_type == ItemType.SERVICE
        assert item.is_serialized is False
    
    def test_item_code_required(self):
        """Test that item code is required."""
        with pytest.raises(ValueError, match="Item code is required"):
            ItemMaster(
                item_code="",
                item_name="Test Item",
                category_id=uuid4()
            )
    
    def test_item_name_required(self):
        """Test that item name is required."""
        with pytest.raises(ValueError, match="Item name is required"):
            ItemMaster(
                item_code="ITEM001",
                item_name="",
                category_id=uuid4()
            )
    
    def test_category_required(self):
        """Test that category is required."""
        with pytest.raises(ValueError, match="Category is required"):
            ItemMaster(
                item_code="ITEM001",
                item_name="Test Item",
                category_id=None
            )
    
    def test_bundle_cannot_be_serialized(self):
        """Test that bundle items cannot be serialized."""
        with pytest.raises(ValueError, match="Bundle items cannot be serialized"):
            ItemMaster(
                item_code="BUNDLE001",
                item_name="Test Bundle",
                category_id=uuid4(),
                item_type=ItemType.BUNDLE,
                is_serialized=True
            )
    
    def test_service_cannot_be_serialized(self):
        """Test that service items cannot be serialized."""
        with pytest.raises(ValueError, match="Service items cannot be serialized"):
            ItemMaster(
                item_code="SVC001",
                item_name="Test Service",
                category_id=uuid4(),
                item_type=ItemType.SERVICE,
                is_serialized=True
            )
    
    def test_update_basic_info(self):
        """Test updating basic item information."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Original Name",
            category_id=uuid4()
        )
        
        original_updated_at = item.updated_at
        
        item.update_basic_info(
            item_name="Updated Name",
            description="New description",
            updated_by="user123"
        )
        
        assert item.item_name == "Updated Name"
        assert item.description == "New description"
        assert item.updated_by == "user123"
        assert item.updated_at > original_updated_at
    
    def test_update_basic_info_empty_name_fails(self):
        """Test that updating with empty name fails."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=uuid4()
        )
        
        with pytest.raises(ValueError, match="Item name cannot be empty"):
            item.update_basic_info(item_name="   ")
    
    def test_update_category(self):
        """Test updating item category."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=uuid4()
        )
        
        new_category_id = uuid4()
        item.update_category(new_category_id, updated_by="user123")
        
        assert item.category_id == new_category_id
        assert item.updated_by == "user123"
    
    def test_update_category_invalid_fails(self):
        """Test that updating with invalid category fails."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=uuid4()
        )
        
        with pytest.raises(ValueError, match="Category ID is required"):
            item.update_category(None)
    
    def test_update_brand(self):
        """Test updating item brand."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=uuid4()
        )
        
        brand_id = uuid4()
        item.update_brand(brand_id, updated_by="user123")
        
        assert item.brand_id == brand_id
        
        # Test removing brand
        item.update_brand(None)
        assert item.brand_id is None
    
    def test_enable_serialization(self):
        """Test enabling serialization for product."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=uuid4(),
            item_type=ItemType.PRODUCT,
            is_serialized=False
        )
        
        item.enable_serialization(updated_by="user123")
        
        assert item.is_serialized is True
        assert item.updated_by == "user123"
    
    def test_enable_serialization_for_bundle_fails(self):
        """Test that enabling serialization for bundle fails."""
        item = ItemMaster(
            item_code="BUNDLE001",
            item_name="Test Bundle",
            category_id=uuid4(),
            item_type=ItemType.BUNDLE
        )
        
        with pytest.raises(ValueError, match="BUNDLE items cannot be serialized"):
            item.enable_serialization()
    
    def test_disable_serialization(self):
        """Test disabling serialization."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=uuid4(),
            is_serialized=True
        )
        
        item.disable_serialization(updated_by="user123")
        
        assert item.is_serialized is False
        assert item.updated_by == "user123"
    
    def test_deactivate_and_activate(self):
        """Test deactivating and activating item."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=uuid4()
        )
        
        assert item.is_active is True
        
        item.deactivate(updated_by="user123")
        assert item.is_active is False
        assert item.updated_by == "user123"
        
        item.activate(updated_by="user456")
        assert item.is_active is True
        assert item.updated_by == "user456"
    
    def test_string_representations(self):
        """Test string representations."""
        item = ItemMaster(
            item_code="ITEM001",
            item_name="Test Item",
            category_id=uuid4()
        )
        
        assert str(item) == "ItemMaster(ITEM001: Test Item)"
        assert "ITEM001" in repr(item)
        assert "Test Item" in repr(item)
        assert "PRODUCT" in repr(item)