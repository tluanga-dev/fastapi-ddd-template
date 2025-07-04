from typing import Optional
from uuid import UUID

from ....domain.entities.item_master import ItemMaster
from ....domain.repositories.item_master_repository import ItemMasterRepository


class GetItemMasterUseCase:
    """Use case for retrieving item master."""
    
    def __init__(self, repository: ItemMasterRepository):
        """Initialize use case with repository."""
        self.repository = repository
    
    async def execute(self, item_id: UUID) -> Optional[ItemMaster]:
        """Get item master by ID."""
        return await self.repository.get_by_id(item_id)
    
    async def get_by_code(self, item_code: str) -> Optional[ItemMaster]:
        """Get item master by code."""
        return await self.repository.get_by_code(item_code)