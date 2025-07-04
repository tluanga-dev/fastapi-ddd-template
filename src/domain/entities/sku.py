from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ..entities.base import BaseEntity


class SKU(BaseEntity):
    """Stock Keeping Unit entity representing a specific product variant."""
    
    def __init__(
        self,
        sku_code: str,
        sku_name: str,
        item_id: UUID,
        barcode: Optional[str] = None,
        model_number: Optional[str] = None,
        weight: Optional[Decimal] = None,
        dimensions: Optional[Dict[str, Decimal]] = None,
        is_rentable: bool = False,
        is_saleable: bool = True,
        min_rental_days: int = 1,
        max_rental_days: Optional[int] = None,
        rental_base_price: Optional[Decimal] = None,
        sale_base_price: Optional[Decimal] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Initialize SKU entity."""
        super().__init__(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            is_active=is_active,
            created_by=created_by,
            updated_by=updated_by
        )
        self.sku_code = sku_code
        self.sku_name = sku_name
        self.item_id = item_id
        self.barcode = barcode
        self.model_number = model_number
        self.weight = weight
        self.dimensions = dimensions or {}
        self.is_rentable = is_rentable
        self.is_saleable = is_saleable
        self.min_rental_days = min_rental_days
        self.max_rental_days = max_rental_days
        self.rental_base_price = rental_base_price
        self.sale_base_price = sale_base_price
        self._validate()
    
    def _validate(self):
        """Validate SKU business rules."""
        if not self.sku_code or not self.sku_code.strip():
            raise ValueError("SKU code is required")
        
        if not self.sku_name or not self.sku_name.strip():
            raise ValueError("SKU name is required")
        
        if not self.item_id:
            raise ValueError("Item ID is required")
        
        # At least one of rentable or saleable must be true
        if not self.is_rentable and not self.is_saleable:
            raise ValueError("SKU must be either rentable or saleable")
        
        # Rental validation
        if self.is_rentable:
            if self.min_rental_days < 1:
                raise ValueError("Minimum rental days must be at least 1")
            
            if self.max_rental_days is not None and self.max_rental_days < self.min_rental_days:
                raise ValueError("Maximum rental days must be greater than or equal to minimum")
            
            if self.rental_base_price is not None and self.rental_base_price < 0:
                raise ValueError("Rental base price cannot be negative")
        
        # Sale validation
        if self.is_saleable:
            if self.sale_base_price is not None and self.sale_base_price < 0:
                raise ValueError("Sale base price cannot be negative")
        
        # Weight validation
        if self.weight is not None and self.weight < 0:
            raise ValueError("Weight cannot be negative")
        
        # Dimensions validation
        if self.dimensions:
            for key, value in self.dimensions.items():
                if value < 0:
                    raise ValueError(f"Dimension {key} cannot be negative")
    
    def update_basic_info(
        self,
        sku_name: Optional[str] = None,
        barcode: Optional[str] = None,
        model_number: Optional[str] = None,
        updated_by: Optional[str] = None
    ):
        """Update basic SKU information."""
        if sku_name is not None:
            if not sku_name.strip():
                raise ValueError("SKU name cannot be empty")
            self.sku_name = sku_name
        
        if barcode is not None:
            self.barcode = barcode
        
        if model_number is not None:
            self.model_number = model_number
        
        self.update_timestamp(updated_by)
        self._validate()
    
    def update_physical_specs(
        self,
        weight: Optional[Decimal] = None,
        dimensions: Optional[Dict[str, Decimal]] = None,
        updated_by: Optional[str] = None
    ):
        """Update physical specifications."""
        if weight is not None:
            if weight < 0:
                raise ValueError("Weight cannot be negative")
            self.weight = weight
        
        if dimensions is not None:
            for key, value in dimensions.items():
                if value < 0:
                    raise ValueError(f"Dimension {key} cannot be negative")
            self.dimensions = dimensions
        
        self.update_timestamp(updated_by)
    
    def update_rental_settings(
        self,
        is_rentable: Optional[bool] = None,
        min_rental_days: Optional[int] = None,
        max_rental_days: Optional[int] = None,
        rental_base_price: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ):
        """Update rental settings."""
        if is_rentable is not None:
            self.is_rentable = is_rentable
        
        if self.is_rentable:
            if min_rental_days is not None:
                if min_rental_days < 1:
                    raise ValueError("Minimum rental days must be at least 1")
                self.min_rental_days = min_rental_days
            
            if max_rental_days is not None:
                if max_rental_days < self.min_rental_days:
                    raise ValueError("Maximum rental days must be >= minimum")
                self.max_rental_days = max_rental_days
            
            if rental_base_price is not None:
                if rental_base_price < 0:
                    raise ValueError("Rental base price cannot be negative")
                self.rental_base_price = rental_base_price
        
        self.update_timestamp(updated_by)
        self._validate()
    
    def update_sale_settings(
        self,
        is_saleable: Optional[bool] = None,
        sale_base_price: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ):
        """Update sale settings."""
        if is_saleable is not None:
            self.is_saleable = is_saleable
        
        if self.is_saleable and sale_base_price is not None:
            if sale_base_price < 0:
                raise ValueError("Sale base price cannot be negative")
            self.sale_base_price = sale_base_price
        
        self.update_timestamp(updated_by)
        self._validate()
    
    def enable_rental(self, min_days: int = 1, base_price: Optional[Decimal] = None, updated_by: Optional[str] = None):
        """Enable rental for this SKU."""
        self.is_rentable = True
        self.min_rental_days = min_days
        if base_price is not None:
            self.rental_base_price = base_price
        self.update_timestamp(updated_by)
        self._validate()
    
    def disable_rental(self, updated_by: Optional[str] = None):
        """Disable rental for this SKU."""
        if not self.is_saleable:
            raise ValueError("Cannot disable rental when sale is also disabled")
        
        self.is_rentable = False
        self.update_timestamp(updated_by)
    
    def enable_sale(self, base_price: Optional[Decimal] = None, updated_by: Optional[str] = None):
        """Enable sale for this SKU."""
        self.is_saleable = True
        if base_price is not None:
            self.sale_base_price = base_price
        self.update_timestamp(updated_by)
        self._validate()
    
    def disable_sale(self, updated_by: Optional[str] = None):
        """Disable sale for this SKU."""
        if not self.is_rentable:
            raise ValueError("Cannot disable sale when rental is also disabled")
        
        self.is_saleable = False
        self.update_timestamp(updated_by)
    
    def deactivate(self, updated_by: Optional[str] = None):
        """Deactivate the SKU."""
        self.is_active = False
        self.update_timestamp(updated_by)
    
    def activate(self, updated_by: Optional[str] = None):
        """Activate the SKU."""
        self.is_active = True
        self.update_timestamp(updated_by)
    
    def __str__(self) -> str:
        """String representation of SKU."""
        return f"SKU({self.sku_code}: {self.sku_name})"
    
    def __repr__(self) -> str:
        """Developer representation of SKU."""
        return (
            f"SKU(id={self.id}, sku_code='{self.sku_code}', "
            f"sku_name='{self.sku_name}', rentable={self.is_rentable}, "
            f"saleable={self.is_saleable})"
        )