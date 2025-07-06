from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from ....domain.value_objects.item_type import ItemType
from ....domain.entities.item_master import ItemMaster


class ItemMasterBase(BaseModel):
    """Base schema for Item Master."""
    item_code: str = Field(..., min_length=1, max_length=50, description="Unique item code")
    item_name: str = Field(..., min_length=1, max_length=200, description="Item name")
    category_id: UUID = Field(..., description="Category ID")
    brand_id: Optional[UUID] = Field(None, description="Brand ID")
    item_type: ItemType = Field(ItemType.PRODUCT, description="Item type")
    description: Optional[str] = Field(None, description="Item description")
    is_serialized: bool = Field(False, description="Whether item requires serial tracking")


class ItemMasterCreate(ItemMasterBase):
    """Schema for creating Item Master."""
    pass


class ItemMasterUpdate(BaseModel):
    """Schema for updating Item Master."""
    item_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    brand_id: Optional[UUID] = None
    

class ItemMasterResponse(ItemMasterBase):
    """Schema for Item Master response."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_entity(cls, entity: ItemMaster) -> "ItemMasterResponse":
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            item_code=entity.item_code,
            item_name=entity.item_name,
            category_id=entity.category_id,
            brand_id=entity.brand_id,
            item_type=entity.item_type,
            description=entity.description,
            is_serialized=entity.is_serialized,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )


class ItemMasterListResponse(BaseModel):
    """Schema for paginated Item Master list response."""
    items: List[ItemMasterResponse]
    total: int
    skip: int
    limit: int


class ItemMasterSerializationUpdate(BaseModel):
    """Schema for updating item serialization settings."""
    enable: bool = Field(..., description="Enable or disable serialization")


class ItemTypeCount(BaseModel):
    """Schema for item type count."""
    item_type: ItemType
    count: int


class ItemMasterDropdownOption(BaseModel):
    """Minimal item master data for dropdown selection."""
    id: UUID
    item_code: str
    item_name: str
    item_type: ItemType
    is_serialized: bool
    category_id: UUID
    brand_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class ItemMasterDropdownResponse(BaseModel):
    """Response schema for item master dropdown endpoint."""
    options: List[ItemMasterDropdownOption]
    total: int
    limit: int


class ItemMasterEnrichedResponse(ItemMasterResponse):
    """Schema for Item Master response with related entity names."""
    category_name: Optional[str] = Field(None, description="Category name")
    brand_name: Optional[str] = Field(None, description="Brand name")
    
    @classmethod
    def from_model_with_relations(cls, model) -> "ItemMasterEnrichedResponse":
        """Create enriched response from SQLAlchemy model with loaded relationships."""
        return cls(
            id=model.id,
            item_code=model.item_code,
            item_name=model.item_name,
            category_id=model.category_id,
            category_name=model.category.category_name if model.category else None,
            brand_id=model.brand_id,
            brand_name=model.brand.brand_name if model.brand else None,
            item_type=model.item_type,
            description=model.description,
            is_serialized=model.is_serialized,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )


class ItemMasterEnrichedListResponse(BaseModel):
    """Schema for paginated Item Master list response with enriched data."""
    items: List[ItemMasterEnrichedResponse]
    total: int
    skip: int
    limit: int