from uuid import UUID

from ....domain.repositories.item_master_repository import ItemMasterRepository


class DeleteItemMasterUseCase:
    """Use case for deleting item master."""
    
    def __init__(self, repository: ItemMasterRepository):
        """Initialize use case with repository."""
        self.repository = repository
    
    async def execute(self, item_id: UUID) -> bool:
        """Soft delete item master."""
        # Check if item has SKUs
        if await self.repository.has_skus(item_id):
            raise ValueError("Cannot delete item with existing SKUs")
        
        # Delete the item
        return await self.repository.delete(item_id)