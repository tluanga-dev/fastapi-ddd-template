from typing import Optional
from uuid import UUID

from ....domain.entities.item_master import ItemMaster
from ....domain.repositories.item_master_repository import ItemMasterRepository
from ....domain.repositories.category_repository import CategoryRepository
from ....domain.value_objects.item_type import ItemType


class CreateItemMasterUseCase:
    """Use case for creating a new item master."""
    
    def __init__(
        self, 
        repository: ItemMasterRepository,
        category_repository: CategoryRepository
    ):
        """Initialize use case with repositories."""
        self.repository = repository
        self.category_repository = category_repository
    
    async def execute(
        self,
        item_code: str,
        item_name: str,
        category_id: UUID,
        item_type: ItemType = ItemType.PRODUCT,
        brand_id: Optional[UUID] = None,
        description: Optional[str] = None,
        is_serialized: bool = False,
        created_by: Optional[str] = None
    ) -> ItemMaster:
        """Execute the use case to create a new item master."""
        # Check if item code already exists
        if await self.repository.exists_by_code(item_code):
            raise ValueError(f"Item with code '{item_code}' already exists")
        
        # Validate category exists and is a leaf category
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID '{category_id}' not found")
        
        if not category.can_have_products():
            raise ValueError(
                f"Products can only be assigned to leaf categories. "
                f"'{category.category_name}' is a parent category with subcategories."
            )
        
        # Create item master entity
        item = ItemMaster(
            item_code=item_code,
            item_name=item_name,
            category_id=category_id,
            item_type=item_type,
            brand_id=brand_id,
            description=description,
            is_serialized=is_serialized,
            created_by=created_by
        )
        
        # Save to repository
        return await self.repository.create(item)