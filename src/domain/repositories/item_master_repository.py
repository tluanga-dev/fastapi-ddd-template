from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities.item_master import ItemMaster
from ..value_objects.item_type import ItemType


class ItemMasterRepository(ABC):
    """Abstract repository interface for ItemMaster entity."""
    
    @abstractmethod
    async def create(self, item: ItemMaster) -> ItemMaster:
        """Create a new item master."""
        pass
    
    @abstractmethod
    async def get_by_id(self, item_id: UUID) -> Optional[ItemMaster]:
        """Get item master by ID."""
        pass
    
    @abstractmethod
    async def get_by_code(self, item_code: str) -> Optional[ItemMaster]:
        """Get item master by item code."""
        pass
    
    @abstractmethod
    async def list(
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
        """List item masters with filters and pagination."""
        pass
    
    @abstractmethod
    async def update(self, item: ItemMaster) -> ItemMaster:
        """Update existing item master."""
        pass
    
    @abstractmethod
    async def delete(self, item_id: UUID) -> bool:
        """Soft delete item master."""
        pass
    
    @abstractmethod
    async def exists_by_code(self, item_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if an item with the given code exists."""
        pass
    
    @abstractmethod
    async def get_by_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[ItemMaster], int]:
        """Get items by category."""
        pass
    
    @abstractmethod
    async def get_by_brand(self, brand_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[ItemMaster], int]:
        """Get items by brand."""
        pass
    
    @abstractmethod
    async def count_by_type(self) -> dict:
        """Get count of items by type."""
        pass
    
    @abstractmethod
    async def has_skus(self, item_id: UUID) -> bool:
        """Check if item has any SKUs."""
        pass