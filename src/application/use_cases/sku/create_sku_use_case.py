from typing import Optional, Dict
from decimal import Decimal
from uuid import UUID

from ....domain.entities.sku import SKU
from ....domain.repositories.sku_repository import SKURepository
from ....domain.repositories.item_master_repository import ItemMasterRepository


class CreateSKUUseCase:
    """Use case for creating a new SKU."""
    
    def __init__(self, sku_repository: SKURepository, item_repository: ItemMasterRepository):
        """Initialize use case with repositories."""
        self.sku_repository = sku_repository
        self.item_repository = item_repository
    
    async def execute(
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
        created_by: Optional[str] = None
    ) -> SKU:
        """Execute the use case to create a new SKU."""
        # Verify item exists
        item = await self.item_repository.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found")
        
        # Check if SKU code already exists
        if await self.sku_repository.exists_by_code(sku_code):
            raise ValueError(f"SKU with code '{sku_code}' already exists")
        
        # Check if barcode already exists
        if barcode and await self.sku_repository.exists_by_barcode(barcode):
            raise ValueError(f"SKU with barcode '{barcode}' already exists")
        
        # Create SKU entity
        sku = SKU(
            sku_code=sku_code,
            sku_name=sku_name,
            item_id=item_id,
            barcode=barcode,
            model_number=model_number,
            weight=weight,
            dimensions=dimensions,
            is_rentable=is_rentable,
            is_saleable=is_saleable,
            min_rental_days=min_rental_days,
            max_rental_days=max_rental_days,
            rental_base_price=rental_base_price,
            sale_base_price=sale_base_price,
            created_by=created_by
        )
        
        # Save to repository
        return await self.sku_repository.create(sku)