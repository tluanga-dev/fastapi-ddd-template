from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, Numeric, JSON
from sqlalchemy.orm import relationship
import uuid
from decimal import Decimal

from ...domain.entities.sku import SKU
from .base import BaseModel, UUID
from ..database import Base


class SKUModel(Base, BaseModel):
    """SQLAlchemy model for SKU."""
    
    __tablename__ = "skus"
    
    sku_code = Column(String(50), unique=True, nullable=False, index=True)
    sku_name = Column(String(200), nullable=False)
    item_id = Column(UUID(), ForeignKey("item_masters.id"), nullable=False)
    barcode = Column(String(50), unique=True, nullable=True, index=True)
    model_number = Column(String(100), nullable=True)
    weight = Column(Numeric(10, 3), nullable=True)  # Weight in kg
    dimensions = Column(JSON, nullable=True)  # {length, width, height} in cm
    is_rentable = Column(Boolean, nullable=False, default=False)
    is_saleable = Column(Boolean, nullable=False, default=True)
    min_rental_days = Column(Integer, nullable=False, default=1)
    max_rental_days = Column(Integer, nullable=True)
    rental_base_price = Column(Numeric(15, 2), nullable=True)
    sale_base_price = Column(Numeric(15, 2), nullable=True)
    
    # Relationships
    item = relationship("ItemMasterModel", back_populates="skus")
    inventory_units = relationship("InventoryUnitModel", back_populates="sku")
    stock_levels = relationship("StockLevelModel", back_populates="sku")
    
    def to_entity(self) -> SKU:
        """Convert SQLAlchemy model to domain entity."""
        return SKU(
            id=self.id,
            sku_code=self.sku_code,
            sku_name=self.sku_name,
            item_id=self.item_id,
            barcode=self.barcode,
            model_number=self.model_number,
            weight=Decimal(str(self.weight)) if self.weight else None,
            dimensions={k: Decimal(str(v)) for k, v in self.dimensions.items()} if self.dimensions else None,
            is_rentable=self.is_rentable,
            is_saleable=self.is_saleable,
            min_rental_days=self.min_rental_days,
            max_rental_days=self.max_rental_days,
            rental_base_price=Decimal(str(self.rental_base_price)) if self.rental_base_price else None,
            sale_base_price=Decimal(str(self.sale_base_price)) if self.sale_base_price else None,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by
        )
    
    @classmethod
    def from_entity(cls, entity: SKU) -> "SKUModel":
        """Create SQLAlchemy model from domain entity."""
        return cls(
            id=entity.id if entity.id else uuid.uuid4(),
            sku_code=entity.sku_code,
            sku_name=entity.sku_name,
            item_id=entity.item_id,
            barcode=entity.barcode,
            model_number=entity.model_number,
            weight=float(entity.weight) if entity.weight else None,
            dimensions={k: float(v) for k, v in entity.dimensions.items()} if entity.dimensions else None,
            is_rentable=entity.is_rentable,
            is_saleable=entity.is_saleable,
            min_rental_days=entity.min_rental_days,
            max_rental_days=entity.max_rental_days,
            rental_base_price=float(entity.rental_base_price) if entity.rental_base_price else None,
            sale_base_price=float(entity.sale_base_price) if entity.sale_base_price else None,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )