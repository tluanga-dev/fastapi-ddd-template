from typing import List, Optional, Tuple
from uuid import UUID

from ....domain.entities.sku import SKU
from ....domain.repositories.sku_repository import SKURepository


class ListSKUsUseCase:
    """Use case for listing SKUs."""
    
    def __init__(self, repository: SKURepository):
        """Initialize use case with repository."""
        self.repository = repository
    
    async def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        item_id: Optional[UUID] = None,
        is_rentable: Optional[bool] = None,
        is_saleable: Optional[bool] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[SKU], int]:
        """List SKUs with filters."""
        return await self.repository.list(
            skip=skip,
            limit=limit,
            item_id=item_id,
            is_rentable=is_rentable,
            is_saleable=is_saleable,
            search=search,
            is_active=is_active
        )
    
    async def get_by_item(
        self,
        item_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SKU], int]:
        """Get SKUs by item master."""
        return await self.repository.get_by_item(item_id, skip, limit)
    
    async def get_rentable_skus(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SKU], int]:
        """Get all rentable SKUs."""
        return await self.repository.get_rentable_skus(skip, limit)
    
    async def get_saleable_skus(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SKU], int]:
        """Get all saleable SKUs."""
        return await self.repository.get_saleable_skus(skip, limit)