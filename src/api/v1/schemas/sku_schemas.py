from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ....domain.entities.sku import SKU


class SKUBase(BaseModel):
    """Base schema for SKU."""
    sku_code: str = Field(..., min_length=1, max_length=50, description="Unique SKU code")
    sku_name: str = Field(..., min_length=1, max_length=200, description="SKU name")
    item_id: UUID = Field(..., description="Parent item ID")
    barcode: Optional[str] = Field(None, max_length=50, description="Barcode/UPC")
    model_number: Optional[str] = Field(None, max_length=100, description="Model number")
    weight: Optional[Decimal] = Field(None, ge=0, description="Weight in kg")
    dimensions: Optional[Dict[str, Decimal]] = Field(None, description="Dimensions in cm")
    is_rentable: bool = Field(False, description="Available for rent")
    is_saleable: bool = Field(True, description="Available for sale")
    min_rental_days: int = Field(1, ge=1, description="Minimum rental days")
    max_rental_days: Optional[int] = Field(None, ge=1, description="Maximum rental days")
    rental_base_price: Optional[Decimal] = Field(None, ge=0, description="Base rental price per day")
    sale_base_price: Optional[Decimal] = Field(None, ge=0, description="Base sale price")
    
    @field_validator('dimensions')
    def validate_dimensions(cls, v):
        if v:
            for key, value in v.items():
                if value < 0:
                    raise ValueError(f"Dimension {key} cannot be negative")
        return v
    
    @field_validator('max_rental_days')
    def validate_max_rental_days(cls, v, values):
        if v is not None and 'min_rental_days' in values and v < values['min_rental_days']:
            raise ValueError("Maximum rental days must be >= minimum rental days")
        return v


class SKUCreate(SKUBase):
    """Schema for creating SKU."""
    pass


class SKUUpdate(BaseModel):
    """Schema for updating SKU."""
    sku_name: Optional[str] = Field(None, min_length=1, max_length=200)
    barcode: Optional[str] = Field(None, max_length=50)
    model_number: Optional[str] = Field(None, max_length=100)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Decimal]] = None
    
    @field_validator('dimensions')
    def validate_dimensions(cls, v):
        if v:
            for key, value in v.items():
                if value < 0:
                    raise ValueError(f"Dimension {key} cannot be negative")
        return v


class SKURentalUpdate(BaseModel):
    """Schema for updating SKU rental settings."""
    is_rentable: Optional[bool] = None
    min_rental_days: Optional[int] = Field(None, ge=1)
    max_rental_days: Optional[int] = Field(None, ge=1)
    rental_base_price: Optional[Decimal] = Field(None, ge=0)
    
    @field_validator('max_rental_days')
    def validate_max_rental_days(cls, v, values):
        if v is not None and 'min_rental_days' in values.data and values.data['min_rental_days'] is not None:
            if v < values.data['min_rental_days']:
                raise ValueError("Maximum rental days must be >= minimum rental days")
        return v


class SKUSaleUpdate(BaseModel):
    """Schema for updating SKU sale settings."""
    is_saleable: Optional[bool] = None
    sale_base_price: Optional[Decimal] = Field(None, ge=0)


class SKUResponse(SKUBase):
    """Schema for SKU response."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_entity(cls, entity: SKU) -> "SKUResponse":
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            sku_code=entity.sku_code,
            sku_name=entity.sku_name,
            item_id=entity.item_id,
            barcode=entity.barcode,
            model_number=entity.model_number,
            weight=entity.weight,
            dimensions=entity.dimensions,
            is_rentable=entity.is_rentable,
            is_saleable=entity.is_saleable,
            min_rental_days=entity.min_rental_days,
            max_rental_days=entity.max_rental_days,
            rental_base_price=entity.rental_base_price,
            sale_base_price=entity.sale_base_price,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )


class SKUListResponse(BaseModel):
    """Schema for paginated SKU list response."""
    items: List[SKUResponse]
    total: int
    skip: int
    limit: int