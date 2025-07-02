from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import uuid

from ...domain.entities.item_master import ItemMaster
from ...domain.value_objects.item_type import ItemType
from .base import BaseModel, UUID
from ..database import Base


class ItemMasterModel(Base, BaseModel):
    """SQLAlchemy model for Item Master."""
    
    __tablename__ = "item_masters"
    
    item_code = Column(String(50), unique=True, nullable=False, index=True)
    item_name = Column(String(200), nullable=False)
    category_id = Column(UUID(), ForeignKey("categories.id"), nullable=False)
    brand_id = Column(UUID(), ForeignKey("brands.id"), nullable=True)
    item_type = Column(Enum(ItemType), nullable=False, default=ItemType.PRODUCT)
    description = Column(Text, nullable=True)
    is_serialized = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    category = relationship("CategoryModel", back_populates="items")
    brand = relationship("BrandModel", back_populates="items")
    skus = relationship("SKUModel", back_populates="item", cascade="all, delete-orphan")
    
    def to_entity(self) -> ItemMaster:
        """Convert SQLAlchemy model to domain entity."""
        return ItemMaster(
            id=self.id,
            item_code=self.item_code,
            item_name=self.item_name,
            category_id=self.category_id,
            brand_id=self.brand_id,
            item_type=self.item_type,
            description=self.description,
            is_serialized=self.is_serialized,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by
        )
    
    @classmethod
    def from_entity(cls, entity: ItemMaster) -> "ItemMasterModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id if entity.id else uuid.uuid4(),
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