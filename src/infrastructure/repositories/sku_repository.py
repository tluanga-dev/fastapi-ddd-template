from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.sku import SKU
from ...domain.repositories.sku_repository import SKURepository
from ..models.sku_model import SKUModel


class SQLAlchemySKURepository(SKURepository):
    """SQLAlchemy implementation of SKURepository."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, sku: SKU) -> SKU:
        """Create a new SKU."""
        db_sku = SKUModel.from_entity(sku)
        self.session.add(db_sku)
        await self.session.commit()
        await self.session.refresh(db_sku)
        return db_sku.to_entity()
    
    async def get_by_id(self, sku_id: UUID) -> Optional[SKU]:
        """Get SKU by ID."""
        query = select(SKUModel).where(SKUModel.id == sku_id)
        result = await self.session.execute(query)
        db_sku = result.scalar_one_or_none()
        
        if db_sku:
            return db_sku.to_entity()
        return None
    
    async def get_by_code(self, sku_code: str) -> Optional[SKU]:
        """Get SKU by SKU code."""
        query = select(SKUModel).where(SKUModel.sku_code == sku_code)
        result = await self.session.execute(query)
        db_sku = result.scalar_one_or_none()
        
        if db_sku:
            return db_sku.to_entity()
        return None
    
    async def get_by_barcode(self, barcode: str) -> Optional[SKU]:
        """Get SKU by barcode."""
        query = select(SKUModel).where(SKUModel.barcode == barcode)
        result = await self.session.execute(query)
        db_sku = result.scalar_one_or_none()
        
        if db_sku:
            return db_sku.to_entity()
        return None
    
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
        # Base query
        query = select(SKUModel)
        count_query = select(func.count()).select_from(SKUModel)
        
        # Apply filters
        filters = []
        
        if is_active is not None:
            filters.append(SKUModel.is_active == is_active)
        
        if item_id:
            filters.append(SKUModel.item_id == item_id)
        
        if is_rentable is not None:
            filters.append(SKUModel.is_rentable == is_rentable)
        
        if is_saleable is not None:
            filters.append(SKUModel.is_saleable == is_saleable)
        
        if search:
            search_term = f"%{search}%"
            search_filter = or_(
                SKUModel.sku_code.ilike(search_term),
                SKUModel.sku_name.ilike(search_term),
                SKUModel.barcode.ilike(search_term),
                SKUModel.model_number.ilike(search_term)
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
        query = query.order_by(SKUModel.sku_code).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        skus = result.scalars().all()
        
        return [sku.to_entity() for sku in skus], total_count
    
    async def update(self, sku: SKU) -> SKU:
        """Update existing SKU."""
        query = select(SKUModel).where(SKUModel.id == sku.id)
        result = await self.session.execute(query)
        db_sku = result.scalar_one_or_none()
        
        if not db_sku:
            raise ValueError(f"SKU with id {sku.id} not found")
        
        # Update fields
        db_sku.sku_code = sku.sku_code
        db_sku.sku_name = sku.sku_name
        db_sku.item_id = sku.item_id
        db_sku.barcode = sku.barcode
        db_sku.model_number = sku.model_number
        db_sku.weight = float(sku.weight) if sku.weight else None
        db_sku.dimensions = {k: float(v) for k, v in sku.dimensions.items()} if sku.dimensions else None
        db_sku.is_rentable = sku.is_rentable
        db_sku.is_saleable = sku.is_saleable
        db_sku.min_rental_days = sku.min_rental_days
        db_sku.max_rental_days = sku.max_rental_days
        db_sku.rental_base_price = float(sku.rental_base_price) if sku.rental_base_price else None
        db_sku.sale_base_price = float(sku.sale_base_price) if sku.sale_base_price else None
        db_sku.updated_at = sku.updated_at
        db_sku.updated_by = sku.updated_by
        db_sku.is_active = sku.is_active
        
        await self.session.commit()
        await self.session.refresh(db_sku)
        
        return db_sku.to_entity()
    
    async def delete(self, sku_id: UUID) -> bool:
        """Soft delete SKU by setting is_active to False."""
        query = select(SKUModel).where(SKUModel.id == sku_id)
        result = await self.session.execute(query)
        db_sku = result.scalar_one_or_none()
        
        if not db_sku:
            return False
        
        db_sku.is_active = False
        await self.session.commit()
        
        return True
    
    async def exists_by_code(self, sku_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a SKU with the given code exists."""
        query = select(func.count()).select_from(SKUModel).where(
            SKUModel.sku_code == sku_code
        )
        
        if exclude_id:
            query = query.where(SKUModel.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def exists_by_barcode(self, barcode: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if a SKU with the given barcode exists."""
        query = select(func.count()).select_from(SKUModel).where(
            SKUModel.barcode == barcode
        )
        
        if exclude_id:
            query = query.where(SKUModel.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count > 0
    
    async def get_by_item(self, item_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[SKU], int]:
        """Get SKUs by item master."""
        # Base query
        query = select(SKUModel).where(
            and_(
                SKUModel.item_id == item_id,
                SKUModel.is_active == True
            )
        )
        
        # Count query
        count_query = select(func.count()).select_from(SKUModel).where(
            and_(
                SKUModel.item_id == item_id,
                SKUModel.is_active == True
            )
        )
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(SKUModel.sku_code).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        skus = result.scalars().all()
        
        return [sku.to_entity() for sku in skus], total_count
    
    async def get_rentable_skus(self, skip: int = 0, limit: int = 100) -> Tuple[List[SKU], int]:
        """Get all rentable SKUs."""
        # Base query
        query = select(SKUModel).where(
            and_(
                SKUModel.is_rentable == True,
                SKUModel.is_active == True
            )
        )
        
        # Count query
        count_query = select(func.count()).select_from(SKUModel).where(
            and_(
                SKUModel.is_rentable == True,
                SKUModel.is_active == True
            )
        )
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(SKUModel.sku_code).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        skus = result.scalars().all()
        
        return [sku.to_entity() for sku in skus], total_count
    
    async def get_saleable_skus(self, skip: int = 0, limit: int = 100) -> Tuple[List[SKU], int]:
        """Get all saleable SKUs."""
        # Base query
        query = select(SKUModel).where(
            and_(
                SKUModel.is_saleable == True,
                SKUModel.is_active == True
            )
        )
        
        # Count query
        count_query = select(func.count()).select_from(SKUModel).where(
            and_(
                SKUModel.is_saleable == True,
                SKUModel.is_active == True
            )
        )
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply ordering and pagination
        query = query.order_by(SKUModel.sku_code).offset(skip).limit(limit)
        
        # Execute query
        result = await self.session.execute(query)
        skus = result.scalars().all()
        
        return [sku.to_entity() for sku in skus], total_count
    
    async def count_by_item(self, item_id: UUID) -> int:
        """Get count of SKUs for an item."""
        query = select(func.count()).select_from(SKUModel).where(
            and_(
                SKUModel.item_id == item_id,
                SKUModel.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        
        return count
    
    async def has_inventory(self, sku_id: UUID) -> bool:
        """Check if SKU has any inventory units."""
        # This would check inventory tables when implemented
        # For now, return False
        return False