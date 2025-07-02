from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.item_master import (
    CreateItemMasterUseCase,
    GetItemMasterUseCase,
    UpdateItemMasterUseCase,
    DeleteItemMasterUseCase,
    ListItemMastersUseCase
)
from ....infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
from ....domain.value_objects.item_type import ItemType
from ..schemas.item_master_schemas import (
    ItemMasterCreate,
    ItemMasterUpdate,
    ItemMasterResponse,
    ItemMasterListResponse,
    ItemMasterSerializationUpdate
)
from ..dependencies.database import get_db

router = APIRouter(tags=["item-masters"])


async def get_item_master_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyItemMasterRepository:
    """Get item master repository instance."""
    return SQLAlchemyItemMasterRepository(db)


@router.post("/", response_model=ItemMasterResponse, status_code=status.HTTP_201_CREATED)
async def create_item_master(
    item_data: ItemMasterCreate,
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Create a new item master."""
    use_case = CreateItemMasterUseCase(repository)
    
    try:
        item = await use_case.execute(
            item_code=item_data.item_code,
            item_name=item_data.item_name,
            category_id=item_data.category_id,
            item_type=item_data.item_type,
            brand_id=item_data.brand_id,
            description=item_data.description,
            is_serialized=item_data.is_serialized,
            created_by=current_user_id
        )
        return ItemMasterResponse.from_entity(item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{item_id}", response_model=ItemMasterResponse)
async def get_item_master(
    item_id: UUID,
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository)
):
    """Get an item master by ID."""
    use_case = GetItemMasterUseCase(repository)
    item = await use_case.execute(item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    return ItemMasterResponse.from_entity(item)


@router.get("/code/{item_code}", response_model=ItemMasterResponse)
async def get_item_master_by_code(
    item_code: str,
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository)
):
    """Get an item master by code."""
    use_case = GetItemMasterUseCase(repository)
    item = await use_case.get_by_code(item_code)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with code '{item_code}' not found"
        )
    
    return ItemMasterResponse.from_entity(item)


@router.get("/", response_model=ItemMasterListResponse)
async def list_item_masters(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    brand_id: Optional[UUID] = Query(None, description="Filter by brand"),
    item_type: Optional[ItemType] = Query(None, description="Filter by item type"),
    is_serialized: Optional[bool] = Query(None, description="Filter by serialization"),
    search: Optional[str] = Query(None, description="Search in code, name, or description"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository)
):
    """List item masters with pagination and filters."""
    use_case = ListItemMastersUseCase(repository)
    items, total_count = await use_case.execute(
        skip=skip,
        limit=limit,
        category_id=category_id,
        brand_id=brand_id,
        item_type=item_type,
        is_serialized=is_serialized,
        search=search,
        is_active=is_active
    )
    
    return ItemMasterListResponse(
        items=[ItemMasterResponse.from_entity(item) for item in items],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.put("/{item_id}", response_model=ItemMasterResponse)
async def update_item_master(
    item_id: UUID,
    item_data: ItemMasterUpdate,
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update item master information."""
    use_case = UpdateItemMasterUseCase(repository)
    
    try:
        # Update basic info if provided
        if item_data.item_name is not None or item_data.description is not None:
            item = await use_case.update_basic_info(
                item_id=item_id,
                item_name=item_data.item_name,
                description=item_data.description,
                updated_by=current_user_id
            )
        
        # Update category if provided
        if item_data.category_id is not None:
            item = await use_case.update_category(
                item_id=item_id,
                category_id=item_data.category_id,
                updated_by=current_user_id
            )
        
        # Update brand if provided
        if item_data.brand_id is not None:
            item = await use_case.update_brand(
                item_id=item_id,
                brand_id=item_data.brand_id,
                updated_by=current_user_id
            )
        
        # Get final updated item
        get_use_case = GetItemMasterUseCase(repository)
        item = await get_use_case.execute(item_id)
        
        return ItemMasterResponse.from_entity(item)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{item_id}/serialization", response_model=ItemMasterResponse)
async def update_item_serialization(
    item_id: UUID,
    request: ItemMasterSerializationUpdate,
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Enable or disable serialization for an item."""
    use_case = UpdateItemMasterUseCase(repository)
    
    try:
        item = await use_case.toggle_serialization(
            item_id=item_id,
            enable=request.enable,
            updated_by=current_user_id
        )
        return ItemMasterResponse.from_entity(item)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_master(
    item_id: UUID,
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Soft delete an item master."""
    use_case = DeleteItemMasterUseCase(repository)
    
    try:
        success = await use_case.execute(item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/category/{category_id}/items", response_model=ItemMasterListResponse)
async def get_items_by_category(
    category_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository)
):
    """Get all items in a category."""
    use_case = ListItemMastersUseCase(repository)
    items, total_count = await use_case.get_by_category(category_id, skip, limit)
    
    return ItemMasterListResponse(
        items=[ItemMasterResponse.from_entity(item) for item in items],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/brand/{brand_id}/items", response_model=ItemMasterListResponse)
async def get_items_by_brand(
    brand_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository)
):
    """Get all items for a brand."""
    use_case = ListItemMastersUseCase(repository)
    items, total_count = await use_case.get_by_brand(brand_id, skip, limit)
    
    return ItemMasterListResponse(
        items=[ItemMasterResponse.from_entity(item) for item in items],
        total=total_count,
        skip=skip,
        limit=limit
    )