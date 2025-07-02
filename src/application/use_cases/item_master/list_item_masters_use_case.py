from typing import List, Optional, Tuple
from uuid import UUID

from ....domain.entities.item_master import ItemMaster
from ....domain.repositories.item_master_repository import ItemMasterRepository
from ....domain.value_objects.item_type import ItemType


class ListItemMastersUseCase:
    """Use case for listing item masters."""
    
    def __init__(self, repository: ItemMasterRepository):
        """Initialize use case with repository."""
        self.repository = repository
    
    async def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[UUID] = None,
        brand_id: Optional[UUID] = None,
        item_type: Optional[ItemType] = None,
        is_serialized: Optional[bool] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[ItemMaster], int]:
        """List item masters with filters."""
        return await self.repository.list(
            skip=skip,
            limit=limit,
            category_id=category_id,
            brand_id=brand_id,
            item_type=item_type,
            is_serialized=is_serialized,
            search=search,
            is_active=is_active
        )
    
    async def get_by_category(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ItemMaster], int]:
        """Get items by category."""
        return await self.repository.get_by_category(category_id, skip, limit)
    
    async def get_by_brand(
        self,
        brand_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ItemMaster], int]:
        """Get items by brand."""
        return await self.repository.get_by_brand(brand_id, skip, limit)