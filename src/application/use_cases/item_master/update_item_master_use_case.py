from typing import Optional
from uuid import UUID

from ....domain.entities.item_master import ItemMaster
from ....domain.repositories.item_master_repository import ItemMasterRepository


class UpdateItemMasterUseCase:
    """Use case for updating item master."""
    
    def __init__(self, repository: ItemMasterRepository):
        """Initialize use case with repository."""
        self.repository = repository
    
    async def update_basic_info(
        self,
        item_id: UUID,
        item_name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> ItemMaster:
        """Update basic item information."""
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found")
        
        item.update_basic_info(
            item_name=item_name,
            description=description,
            updated_by=updated_by
        )
        
        return await self.repository.update(item)
    
    async def update_category(
        self,
        item_id: UUID,
        category_id: UUID,
        updated_by: Optional[str] = None
    ) -> ItemMaster:
        """Update item category."""
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found")
        
        item.update_category(category_id, updated_by)
        
        return await self.repository.update(item)
    
    async def update_brand(
        self,
        item_id: UUID,
        brand_id: Optional[UUID],
        updated_by: Optional[str] = None
    ) -> ItemMaster:
        """Update item brand."""
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found")
        
        item.update_brand(brand_id, updated_by)
        
        return await self.repository.update(item)
    
    async def toggle_serialization(
        self,
        item_id: UUID,
        enable: bool,
        updated_by: Optional[str] = None
    ) -> ItemMaster:
        """Enable or disable serialization for item."""
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found")
        
        if enable:
            item.enable_serialization(updated_by)
        else:
            item.disable_serialization(updated_by)
        
        return await self.repository.update(item)