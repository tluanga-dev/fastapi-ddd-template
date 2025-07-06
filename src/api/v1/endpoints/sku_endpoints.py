from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....application.use_cases.sku import (
    CreateSKUUseCase,
    GetSKUUseCase,
    UpdateSKUUseCase,
    DeleteSKUUseCase,
    ListSKUsUseCase
)
from ....infrastructure.repositories.sku_repository import SQLAlchemySKURepository
from ....infrastructure.repositories.item_master_repository import SQLAlchemyItemMasterRepository
from ..schemas.sku_schemas import (
    SKUCreate,
    SKUUpdate,
    SKURentalUpdate,
    SKUSaleUpdate,
    SKUResponse,
    SKUListResponse,
    SKUDropdownOption,
    SKUDropdownResponse
)
from ..dependencies.database import get_db

router = APIRouter(tags=["skus"])


async def get_sku_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemySKURepository:
    """Get SKU repository instance."""
    return SQLAlchemySKURepository(db)


async def get_item_master_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyItemMasterRepository:
    """Get item master repository instance."""
    return SQLAlchemyItemMasterRepository(db)


@router.post("/", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
async def create_sku(
    sku_data: SKUCreate,
    sku_repository: SQLAlchemySKURepository = Depends(get_sku_repository),
    item_repository: SQLAlchemyItemMasterRepository = Depends(get_item_master_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Create a new SKU."""
    use_case = CreateSKUUseCase(sku_repository, item_repository)
    
    try:
        sku = await use_case.execute(
            sku_code=sku_data.sku_code,
            sku_name=sku_data.sku_name,
            item_id=sku_data.item_id,
            barcode=sku_data.barcode,
            model_number=sku_data.model_number,
            weight=sku_data.weight,
            dimensions=sku_data.dimensions,
            is_rentable=sku_data.is_rentable,
            is_saleable=sku_data.is_saleable,
            min_rental_days=sku_data.min_rental_days,
            max_rental_days=sku_data.max_rental_days,
            rental_base_price=sku_data.rental_base_price,
            sale_base_price=sku_data.sale_base_price,
            created_by=current_user_id
        )
        return SKUResponse.from_entity(sku)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{sku_id}", response_model=SKUResponse)
async def get_sku(
    sku_id: UUID,
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get a SKU by ID."""
    use_case = GetSKUUseCase(repository)
    sku = await use_case.execute(sku_id)
    
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with id {sku_id} not found"
        )
    
    return SKUResponse.from_entity(sku)


@router.get("/code/{sku_code}", response_model=SKUResponse)
async def get_sku_by_code(
    sku_code: str,
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get a SKU by code."""
    use_case = GetSKUUseCase(repository)
    sku = await use_case.get_by_code(sku_code)
    
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with code '{sku_code}' not found"
        )
    
    return SKUResponse.from_entity(sku)


@router.get("/barcode/{barcode}", response_model=SKUResponse)
async def get_sku_by_barcode(
    barcode: str,
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get a SKU by barcode."""
    use_case = GetSKUUseCase(repository)
    sku = await use_case.get_by_barcode(barcode)
    
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with barcode '{barcode}' not found"
        )
    
    return SKUResponse.from_entity(sku)


@router.get("/", response_model=SKUListResponse)
async def list_skus(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    item_id: Optional[UUID] = Query(None, description="Filter by item"),
    is_rentable: Optional[bool] = Query(None, description="Filter by rentable"),
    is_saleable: Optional[bool] = Query(None, description="Filter by saleable"),
    search: Optional[str] = Query(None, description="Search in code, name, barcode, or model"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """List SKUs with pagination and filters."""
    use_case = ListSKUsUseCase(repository)
    skus, total_count = await use_case.execute(
        skip=skip,
        limit=limit,
        item_id=item_id,
        is_rentable=is_rentable,
        is_saleable=is_saleable,
        search=search,
        is_active=is_active
    )
    
    return SKUListResponse(
        items=[SKUResponse.from_entity(sku) for sku in skus],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.put("/{sku_id}", response_model=SKUResponse)
async def update_sku(
    sku_id: UUID,
    sku_data: SKUUpdate,
    repository: SQLAlchemySKURepository = Depends(get_sku_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update SKU information."""
    use_case = UpdateSKUUseCase(repository)
    
    try:
        # Update basic info
        sku = await use_case.update_basic_info(
            sku_id=sku_id,
            sku_name=sku_data.sku_name,
            barcode=sku_data.barcode,
            model_number=sku_data.model_number,
            updated_by=current_user_id
        )
        
        # Update physical specs if provided
        if sku_data.weight is not None or sku_data.dimensions is not None:
            sku = await use_case.update_physical_specs(
                sku_id=sku_id,
                weight=sku_data.weight,
                dimensions=sku_data.dimensions,
                updated_by=current_user_id
            )
        
        return SKUResponse.from_entity(sku)
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


@router.put("/{sku_id}/rental", response_model=SKUResponse)
async def update_sku_rental_settings(
    sku_id: UUID,
    request: SKURentalUpdate,
    repository: SQLAlchemySKURepository = Depends(get_sku_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update SKU rental settings."""
    use_case = UpdateSKUUseCase(repository)
    
    try:
        sku = await use_case.update_rental_settings(
            sku_id=sku_id,
            is_rentable=request.is_rentable,
            min_rental_days=request.min_rental_days,
            max_rental_days=request.max_rental_days,
            rental_base_price=request.rental_base_price,
            updated_by=current_user_id
        )
        return SKUResponse.from_entity(sku)
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


@router.put("/{sku_id}/sale", response_model=SKUResponse)
async def update_sku_sale_settings(
    sku_id: UUID,
    request: SKUSaleUpdate,
    repository: SQLAlchemySKURepository = Depends(get_sku_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Update SKU sale settings."""
    use_case = UpdateSKUUseCase(repository)
    
    try:
        sku = await use_case.update_sale_settings(
            sku_id=sku_id,
            is_saleable=request.is_saleable,
            sale_base_price=request.sale_base_price,
            updated_by=current_user_id
        )
        return SKUResponse.from_entity(sku)
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


@router.delete("/{sku_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sku(
    sku_id: UUID,
    repository: SQLAlchemySKURepository = Depends(get_sku_repository),
    current_user_id: Optional[str] = None  # TODO: Get from auth
):
    """Soft delete a SKU."""
    use_case = DeleteSKUUseCase(repository)
    
    try:
        success = await use_case.execute(sku_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SKU with id {sku_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/item/{item_id}/skus", response_model=SKUListResponse)
async def get_skus_by_item(
    item_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get all SKUs for an item."""
    use_case = ListSKUsUseCase(repository)
    skus, total_count = await use_case.get_by_item(item_id, skip, limit)
    
    return SKUListResponse(
        items=[SKUResponse.from_entity(sku) for sku in skus],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/rentable/", response_model=SKUListResponse)
async def get_rentable_skus(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get all rentable SKUs."""
    use_case = ListSKUsUseCase(repository)
    skus, total_count = await use_case.get_rentable_skus(skip, limit)
    
    return SKUListResponse(
        items=[SKUResponse.from_entity(sku) for sku in skus],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/saleable/", response_model=SKUListResponse)
async def get_saleable_skus(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get all saleable SKUs."""
    use_case = ListSKUsUseCase(repository)
    skus, total_count = await use_case.get_saleable_skus(skip, limit)
    
    return SKUListResponse(
        items=[SKUResponse.from_entity(sku) for sku in skus],
        total=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/dropdown", response_model=SKUDropdownResponse)
async def get_sku_dropdown(
    search: Optional[str] = Query(None, description="Search in code, name, barcode, or model"),
    item_id: Optional[UUID] = Query(None, description="Filter by item"),
    is_rentable: Optional[bool] = Query(None, description="Filter by rentable"),
    is_saleable: Optional[bool] = Query(None, description="Filter by saleable"),
    is_active: bool = Query(True, description="Include only active SKUs"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get SKUs optimized for dropdown selection.
    
    Returns minimal data needed for dropdown display:
    - id, sku_code, sku_name, item_id, barcode, model_number
    - is_rentable, is_saleable, rental_base_price, sale_base_price
    
    Use this endpoint for:
    - SKU selection dropdowns
    - Search-as-you-type components
    - Filtered SKU lists
    """
    use_case = ListSKUsUseCase(repository)
    skus, total_count = await use_case.execute(
        skip=0,
        limit=limit,
        item_id=item_id,
        is_rentable=is_rentable,
        is_saleable=is_saleable,
        search=search,
        is_active=is_active
    )
    
    options = [
        SKUDropdownOption(
            id=sku.id,
            sku_code=sku.sku_code,
            sku_name=sku.sku_name,
            item_id=sku.item_id,
            barcode=sku.barcode,
            model_number=sku.model_number,
            is_rentable=sku.is_rentable,
            is_saleable=sku.is_saleable,
            rental_base_price=sku.rental_base_price,
            sale_base_price=sku.sale_base_price
        )
        for sku in skus
    ]
    
    return SKUDropdownResponse(
        options=options,
        total=total_count,
        limit=limit
    )


@router.get("/item/{item_id}/dropdown", response_model=SKUDropdownResponse)
async def get_sku_dropdown_by_item(
    item_id: UUID,
    search: Optional[str] = Query(None, description="Search in code, name, barcode, or model"),
    is_rentable: Optional[bool] = Query(None, description="Filter by rentable"),
    is_saleable: Optional[bool] = Query(None, description="Filter by saleable"),
    is_active: bool = Query(True, description="Include only active SKUs"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get SKUs for a specific item optimized for dropdown selection.
    
    Returns minimal data needed for dropdown display, filtered by item.
    """
    use_case = ListSKUsUseCase(repository)
    skus, total_count = await use_case.execute(
        skip=0,
        limit=limit,
        item_id=item_id,
        is_rentable=is_rentable,
        is_saleable=is_saleable,
        search=search,
        is_active=is_active
    )
    
    options = [
        SKUDropdownOption(
            id=sku.id,
            sku_code=sku.sku_code,
            sku_name=sku.sku_name,
            item_id=sku.item_id,
            barcode=sku.barcode,
            model_number=sku.model_number,
            is_rentable=sku.is_rentable,
            is_saleable=sku.is_saleable,
            rental_base_price=sku.rental_base_price,
            sale_base_price=sku.sale_base_price
        )
        for sku in skus
    ]
    
    return SKUDropdownResponse(
        options=options,
        total=total_count,
        limit=limit
    )


@router.get("/rentable/dropdown", response_model=SKUDropdownResponse)
async def get_rentable_sku_dropdown(
    search: Optional[str] = Query(None, description="Search in code, name, barcode, or model"),
    item_id: Optional[UUID] = Query(None, description="Filter by item"),
    is_active: bool = Query(True, description="Include only active SKUs"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get rentable SKUs optimized for dropdown selection.
    
    Returns only SKUs where is_rentable=True.
    """
    use_case = ListSKUsUseCase(repository)
    skus, total_count = await use_case.execute(
        skip=0,
        limit=limit,
        item_id=item_id,
        is_rentable=True,
        is_saleable=None,
        search=search,
        is_active=is_active
    )
    
    options = [
        SKUDropdownOption(
            id=sku.id,
            sku_code=sku.sku_code,
            sku_name=sku.sku_name,
            item_id=sku.item_id,
            barcode=sku.barcode,
            model_number=sku.model_number,
            is_rentable=sku.is_rentable,
            is_saleable=sku.is_saleable,
            rental_base_price=sku.rental_base_price,
            sale_base_price=sku.sale_base_price
        )
        for sku in skus
    ]
    
    return SKUDropdownResponse(
        options=options,
        total=total_count,
        limit=limit
    )


@router.get("/saleable/dropdown", response_model=SKUDropdownResponse)
async def get_saleable_sku_dropdown(
    search: Optional[str] = Query(None, description="Search in code, name, barcode, or model"),
    item_id: Optional[UUID] = Query(None, description="Filter by item"),
    is_active: bool = Query(True, description="Include only active SKUs"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    repository: SQLAlchemySKURepository = Depends(get_sku_repository)
):
    """Get saleable SKUs optimized for dropdown selection.
    
    Returns only SKUs where is_saleable=True.
    """
    use_case = ListSKUsUseCase(repository)
    skus, total_count = await use_case.execute(
        skip=0,
        limit=limit,
        item_id=item_id,
        is_rentable=None,
        is_saleable=True,
        search=search,
        is_active=is_active
    )
    
    options = [
        SKUDropdownOption(
            id=sku.id,
            sku_code=sku.sku_code,
            sku_name=sku.sku_name,
            item_id=sku.item_id,
            barcode=sku.barcode,
            model_number=sku.model_number,
            is_rentable=sku.is_rentable,
            is_saleable=sku.is_saleable,
            rental_base_price=sku.rental_base_price,
            sale_base_price=sku.sale_base_price
        )
        for sku in skus
    ]
    
    return SKUDropdownResponse(
        options=options,
        total=total_count,
        limit=limit
    )