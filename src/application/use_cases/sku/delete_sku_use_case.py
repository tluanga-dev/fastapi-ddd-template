from uuid import UUID

from ....domain.repositories.sku_repository import SKURepository


class DeleteSKUUseCase:
    """Use case for deleting SKU."""
    
    def __init__(self, repository: SKURepository):
        """Initialize use case with repository."""
        self.repository = repository
    
    async def execute(self, sku_id: UUID) -> bool:
        """Soft delete SKU."""
        # Check if SKU has inventory
        if await self.repository.has_inventory(sku_id):
            raise ValueError("Cannot delete SKU with existing inventory")
        
        # Delete the SKU
        return await self.repository.delete(sku_id)