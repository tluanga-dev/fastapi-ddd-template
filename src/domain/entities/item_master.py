from typing import Optional
from datetime import datetime
from uuid import UUID

from ..entities.base import BaseEntity
from ..value_objects.item_type import ItemType


class ItemMaster(BaseEntity):
    """Item Master entity representing a product definition."""
    
    def __init__(
        self,
        item_code: str,
        item_name: str,
        category_id: UUID,
        item_type: ItemType = ItemType.PRODUCT,
        brand_id: Optional[UUID] = None,
        description: Optional[str] = None,
        is_serialized: bool = False,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Initialize Item Master entity."""
        super().__init__(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            is_active=is_active,
            created_by=created_by,
            updated_by=updated_by
        )
        self.item_code = item_code
        self.item_name = item_name
        self.category_id = category_id
        self.item_type = item_type
        self.brand_id = brand_id
        self.description = description
        self.is_serialized = is_serialized
        self._validate()
    
    def _validate(self):
        """Validate item master business rules."""
        if not self.item_code or not self.item_code.strip():
            raise ValueError("Item code is required")
        
        if not self.item_name or not self.item_name.strip():
            raise ValueError("Item name is required")
        
        if not self.category_id:
            raise ValueError("Category is required")
        
        if self.item_type not in ItemType:
            raise ValueError(f"Invalid item type: {self.item_type}")
        
        # Bundles cannot be serialized
        if self.item_type == ItemType.BUNDLE and self.is_serialized:
            raise ValueError("Bundle items cannot be serialized")
        
        # Services cannot be serialized
        if self.item_type == ItemType.SERVICE and self.is_serialized:
            raise ValueError("Service items cannot be serialized")
    
    def update_basic_info(
        self,
        item_name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update basic item information."""
        if item_name is not None:
            if not item_name.strip():
                raise ValueError("Item name cannot be empty")
            self.item_name = item_name
        
        if description is not None:
            self.description = description
        
        self.update_timestamp(updated_by)
        self._validate()
    
    def update_category(self, category_id: UUID, updated_by: Optional[str] = None):
        """Update item category."""
        if not category_id:
            raise ValueError("Category ID is required")
        
        self.category_id = category_id
        self.update_timestamp(updated_by)
    
    def update_brand(self, brand_id: Optional[UUID], updated_by: Optional[str] = None):
        """Update item brand."""
        self.brand_id = brand_id
        self.update_timestamp(updated_by)
    
    def enable_serialization(self, updated_by: Optional[str] = None):
        """Enable serial number tracking for this item."""
        if self.item_type in [ItemType.BUNDLE, ItemType.SERVICE]:
            raise ValueError(f"{self.item_type.value} items cannot be serialized")
        
        self.is_serialized = True
        self.update_timestamp(updated_by)
    
    def disable_serialization(self, updated_by: Optional[str] = None):
        """Disable serial number tracking for this item."""
        self.is_serialized = False
        self.update_timestamp(updated_by)
    
    def deactivate(self, updated_by: Optional[str] = None):
        """Deactivate the item master."""
        self.is_active = False
        self.update_timestamp(updated_by)
    
    def activate(self, updated_by: Optional[str] = None):
        """Activate the item master."""
        self.is_active = True
        self.update_timestamp(updated_by)
    
    def __str__(self) -> str:
        """String representation of item master."""
        return f"ItemMaster({self.item_code}: {self.item_name})"
    
    def __repr__(self) -> str:
        """Developer representation of item master."""
        return (
            f"ItemMaster(id={self.id}, item_code='{self.item_code}', "
            f"item_name='{self.item_name}', item_type={self.item_type.value})"
        )