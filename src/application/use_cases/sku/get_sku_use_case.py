from typing import Optional
from uuid import UUID

from ....domain.entities.sku import SKU
from ....domain.repositories.sku_repository import SKURepository


class GetSKUUseCase:
    """Use case for retrieving SKU."""
    
    def __init__(self, repository: SKURepository):
        """Initialize use case with repository."""
        self.repository = repository
    
    async def execute(self, sku_id: UUID) -> Optional[SKU]:
        """Get SKU by ID."""
        return await self.repository.get_by_id(sku_id)
    
    async def get_by_code(self, sku_code: str) -> Optional[SKU]:
        """Get SKU by code."""
        return await self.repository.get_by_code(sku_code)
    
    async def get_by_barcode(self, barcode: str) -> Optional[SKU]:
        """Get SKU by barcode."""
        return await self.repository.get_by_barcode(barcode)