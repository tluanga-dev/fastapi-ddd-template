from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from ..entities.sku import SKU


class SKURepository(ABC):
    """Abstract repository interface for SKU entity."""
    
    @abstractmethod
    async def create(self, sku: SKU) -> SKU:
        """Create a new SKU."""
        pass
    
    @abstractmethod
    async def get_by_id(self, sku_id: UUID) -> Optional[SKU]:
        """Get SKU by ID."""
        pass
    
    @abstractmethod
    async def get_by_code(self, sku_code: str) -> Optional[SKU]:
        """Get SKU by SKU code."""
        pass
    
    @abstractmethod
    async def get_by_barcode(self, barcode: str) -> Optional[SKU]:
        """Get SKU by barcode."""
        pass
    
    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        item_id: Optional[UUID] = None,
        is_rentable: Optional[bool] = None,
        is_saleable: Optional[bool] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[SKU], int]:
        """List SKUs with filters and pagination."""
        pass
    
    @abstractmethod
    async def update(self, sku: SKU) -> SKU:
        """Update existing SKU."""
        pass
    
    @abstractmethod
    async def delete(self, sku_id: UUID) -> bool:
        """Soft delete SKU."""
        pass
    
    @abstractmethod
    async def exists_by_code(self, sku_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a SKU with the given code exists."""
        pass
    
    @abstractmethod
    async def exists_by_barcode(self, barcode: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a SKU with the given barcode exists."""
        pass
    
    @abstractmethod
    async def get_by_item(self, item_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[SKU], int]:
        """Get SKUs by item master."""
        pass
    
    @abstractmethod
    async def get_rentable_skus(self, skip: int = 0, limit: int = 100) -> Tuple[List[SKU], int]:
        """Get all rentable SKUs."""
        pass
    
    @abstractmethod
    async def get_saleable_skus(self, skip: int = 0, limit: int = 100) -> Tuple[List[SKU], int]:
        """Get all saleable SKUs."""
        pass
    
    @abstractmethod
    async def count_by_item(self, item_id: UUID) -> int:
        """Get count of SKUs for an item."""
        pass
    
    @abstractmethod
    async def has_inventory(self, sku_id: UUID) -> bool:
        """Check if SKU has any inventory units."""
        pass