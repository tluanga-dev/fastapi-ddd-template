from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.item_master import ItemMaster
from ...domain.repositories.item_master_repository import ItemMasterRepository
from ...domain.value_objects.item_type import ItemType
from ..models.item_master_model import ItemMasterModel
from ..models.sku_model import SKUModel


class SQLAlchemyItemMasterRepository(ItemMasterRepository):
    """SQLAlchemy implementation of ItemMasterRepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, item: ItemMaster) -> ItemMaster:
        """Create a new item master."""
        db_item = ItemMasterModel.from_entity(item)
        self.session.add(db_item)
        await self.session.commit()
        await self.session.refresh(db_item)
        return db_item.to_entity()
    
    async def get_by_id(self, item_id: UUID) -> Optional[ItemMaster]:
        """Get item master by ID."""
        query = select(ItemMasterModel).where(ItemMasterModel.id == item_id)
        result = await self.session.execute(query)
        db_item = result.scalar_one_or_none()
        
        if db_item:
            return db_item.to_entity()
        return None
    
    async def get_by_code(self, item_code: str) -> Optional[ItemMaster]:
        """Get item master by item code."""
        query = select(ItemMasterModel).where(ItemMasterModel.item_code == item_code)
        result = await self.session.execute(query)
        db_item = result.scalar_one_or_none()
        
        if db_item:
            return db_item.to_entity()
        return None
    
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
        # Base query
        query = select(ItemMasterModel)
        count_query = select(func.count()).select_from(ItemMasterModel)
        
        # Apply filters
        filters = []
        
        if is_active is not None:
            filters.append(ItemMasterModel.is_active == is_active)
        
        if category_id:
            filters.append(ItemMasterModel.category_id == category_id)
        
        if brand_id:
            filters.append(ItemMasterModel.brand_id == brand_id)
        
        if item_type:
            filters.append(ItemMasterModel.item_type == item_type)
        
        if is_serialized is not None:
            filters.append(ItemMasterModel.is_serialized == is_serialized)
        
        if search:
            search_term = f"%{search}%"
            search_filter = or_(
                ItemMasterModel.item_code.ilike(search_term),
                ItemMasterModel.item_name.ilike(search_term),
                ItemMasterModel.description.ilike(search_term)
            )
            filters.append(search_filter)
        
        # Apply all filters
        if filters:
            where_clause = and_(*filters)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(ItemMasterModel.item_code).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        return [item.to_entity() for item in items], total_count
    
    async def update(self, item: ItemMaster) -> ItemMaster:
        """Update existing item master."""
        query = select(ItemMasterModel).where(ItemMasterModel.id == item.id)
        result = await self.session.execute(query)
        db_item = result.scalar_one_or_none()
        
        if not db_item:
            raise ValueError(f"Item with id {item.id} not found")
        
        # Update fields
        db_item.item_code = item.item_code
        db_item.item_name = item.item_name
        db_item.category_id = item.category_id
        db_item.brand_id = item.brand_id
        db_item.item_type = item.item_type
        db_item.description = item.description
        db_item.is_serialized = item.is_serialized
        db_item.updated_at = item.updated_at
        db_item.updated_by = item.updated_by
        db_item.is_active = item.is_active
        
        await self.session.commit()
        await self.session.refresh(db_item)
        
        return db_item.to_entity()
    
    async def delete(self, item_id: UUID) -> bool:
        """Soft delete item master by setting is_active to False."""
        query = select(ItemMasterModel).where(ItemMasterModel.id == item_id)
        result = await self.session.execute(query)
        db_item = result.scalar_one_or_none()
        
        if not db_item:
            return False
        
        db_item.is_active = False
        await self.session.commit()
        
        return True
    
    async def exists_by_code(self, item_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if an item with the given code exists."""
        query = select(func.count()).select_from(ItemMasterModel).where(
            ItemMasterModel.item_code == item_code
        )
        
        if exclude_id:
            query = query.where(ItemMasterModel.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def get_by_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[ItemMaster], int]:
        """Get items by category."""
        # Base query
        query = select(ItemMasterModel).where(
            and_(
                ItemMasterModel.category_id == category_id,
                ItemMasterModel.is_active == True
            )
        )
        
        # Count query
        count_query = select(func.count()).select_from(ItemMasterModel).where(
            and_(
                ItemMasterModel.category_id == category_id,
                ItemMasterModel.is_active == True
            )
        )
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(ItemMasterModel.item_name).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        return [item.to_entity() for item in items], total_count
    
    async def get_by_brand(self, brand_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[ItemMaster], int]:
        """Get items by brand."""
        # Base query
        query = select(ItemMasterModel).where(
            and_(
                ItemMasterModel.brand_id == brand_id,
                ItemMasterModel.is_active == True
            )
        )
        
        # Count query
        count_query = select(func.count()).select_from(ItemMasterModel).where(
            and_(
                ItemMasterModel.brand_id == brand_id,
                ItemMasterModel.is_active == True
            )
        )
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(ItemMasterModel.item_name).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        return [item.to_entity() for item in items], total_count
    
    async def count_by_type(self) -> dict:
        """Get count of items by type."""
        query = select(
            ItemMasterModel.item_type,
            func.count(ItemMasterModel.id)
        ).where(
            ItemMasterModel.is_active == True
        ).group_by(
            ItemMasterModel.item_type
        )
        
        result = await self.session.execute(query)
        counts = result.all()
        
        return {
            item_type.value: count
            for item_type, count in counts
        }
    
    async def has_skus(self, item_id: UUID) -> bool:
        """Check if item has any SKUs."""
        query = select(func.count()).select_from(SKUModel).where(
            SKUModel.item_id == item_id
        )
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def list_with_relationships(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[UUID] = None,
        brand_id: Optional[UUID] = None,
        item_type: Optional[ItemType] = None,
        is_serialized: Optional[bool] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[ItemMasterModel], int]:
        """List item masters with category and brand relationships loaded."""
        # Base query with eager loading
        query = select(ItemMasterModel).options(
            selectinload(ItemMasterModel.category),
            selectinload(ItemMasterModel.brand)
        )
        count_query = select(func.count()).select_from(ItemMasterModel)
        
        # Apply filters
        filters = []
        
        if is_active is not None:
            filters.append(ItemMasterModel.is_active == is_active)
        
        if category_id:
            filters.append(ItemMasterModel.category_id == category_id)
        
        if brand_id:
            filters.append(ItemMasterModel.brand_id == brand_id)
        
        if item_type:
            filters.append(ItemMasterModel.item_type == item_type)
        
        if is_serialized is not None:
            filters.append(ItemMasterModel.is_serialized == is_serialized)
        
        if search:
            search_term = f"%{search}%"
            search_filter = or_(
                ItemMasterModel.item_code.ilike(search_term),
                ItemMasterModel.item_name.ilike(search_term),
                ItemMasterModel.description.ilike(search_term)
            )
            filters.append(search_filter)
        
        # Apply all filters
        if filters:
            where_clause = and_(*filters)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(ItemMasterModel.item_code).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        items = result.scalars().all()
        
        return items, total_count