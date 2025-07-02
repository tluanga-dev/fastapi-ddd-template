from typing import Optional, Dict
from decimal import Decimal
from uuid import UUID

from ....domain.entities.sku import SKU
from ....domain.repositories.sku_repository import SKURepository


class UpdateSKUUseCase:
    """Use case for updating SKU."""
    
    def __init__(self, repository: SKURepository):
        """Initialize use case with repository."""
        self.repository = repository
    
    async def update_basic_info(
        self,
        sku_id: UUID,
        sku_name: Optional[str] = None,
        barcode: Optional[str] = None,
        model_number: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> SKU:
        """Update basic SKU information."""
        sku = await self.repository.get_by_id(sku_id)
        if not sku:
            raise ValueError(f"SKU with id {sku_id} not found")
        
        # Check barcode uniqueness if changed
        if barcode and barcode != sku.barcode:
            if await self.repository.exists_by_barcode(barcode, exclude_id=sku_id):
                raise ValueError(f"SKU with barcode '{barcode}' already exists")
        
        sku.update_basic_info(
            sku_name=sku_name,
            barcode=barcode,
            model_number=model_number,
            updated_by=updated_by
        )
        
        return await self.repository.update(sku)
    
    async def update_physical_specs(
        self,
        sku_id: UUID,
        weight: Optional[Decimal] = None,
        dimensions: Optional[Dict[str, Decimal]] = None,
        updated_by: Optional[str] = None
    ) -> SKU:
        """Update physical specifications."""
        sku = await self.repository.get_by_id(sku_id)
        if not sku:
            raise ValueError(f"SKU with id {sku_id} not found")
        
        sku.update_physical_specs(
            weight=weight,
            dimensions=dimensions,
            updated_by=updated_by
        )
        
        return await self.repository.update(sku)
    
    async def update_rental_settings(
        self,
        sku_id: UUID,
        is_rentable: Optional[bool] = None,
        min_rental_days: Optional[int] = None,
        max_rental_days: Optional[int] = None,
        rental_base_price: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ) -> SKU:
        """Update rental settings."""
        sku = await self.repository.get_by_id(sku_id)
        if not sku:
            raise ValueError(f"SKU with id {sku_id} not found")
        
        sku.update_rental_settings(
            is_rentable=is_rentable,
            min_rental_days=min_rental_days,
            max_rental_days=max_rental_days,
            rental_base_price=rental_base_price,
            updated_by=updated_by
        )
        
        return await self.repository.update(sku)
    
    async def update_sale_settings(
        self,
        sku_id: UUID,
        is_saleable: Optional[bool] = None,
        sale_base_price: Optional[Decimal] = None,
        updated_by: Optional[str] = None
    ) -> SKU:
        """Update sale settings."""
        sku = await self.repository.get_by_id(sku_id)
        if not sku:
            raise ValueError(f"SKU with id {sku_id} not found")
        
        sku.update_sale_settings(
            is_saleable=is_saleable,
            sale_base_price=sale_base_price,
            updated_by=updated_by
        )
        
        return await self.repository.update(sku)