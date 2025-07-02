from typing import Optional, List, Dict
from uuid import UUID

from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.sku_repository import SKURepository
from ....domain.repositories.location_repository import LocationRepository
from ....domain.value_objects.item_type import InventoryStatus, ConditionGrade


class CheckStockAvailabilityUseCase:
    """Use case for checking stock availability."""
    
    def __init__(
        self,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository,
        sku_repository: SKURepository,
        location_repository: LocationRepository
    ):
        """Initialize use case with repositories."""
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
        self.sku_repository = sku_repository
        self.location_repository = location_repository
    
    async def execute(
        self,
        sku_id: UUID,
        quantity: int,
        location_id: Optional[UUID] = None,
        for_sale: bool = True,
        min_condition_grade: Optional[ConditionGrade] = None
    ) -> Dict:
        """Check if requested quantity is available."""
        # Verify SKU exists
        sku = await self.sku_repository.get_by_id(sku_id)
        if not sku:
            raise ValueError(f"SKU with id {sku_id} not found")
        
        # Check if SKU supports requested operation
        if for_sale and not sku.is_saleable:
            raise ValueError(f"SKU {sku.sku_code} is not available for sale")
        
        if not for_sale and not sku.is_rentable:
            raise ValueError(f"SKU {sku.sku_code} is not available for rent")
        
        # Determine target status
        target_status = InventoryStatus.AVAILABLE_SALE if for_sale else InventoryStatus.AVAILABLE_RENT
        
        # Get availability information
        if location_id:
            # Check specific location
            location = await self.location_repository.get_by_id(location_id)
            if not location:
                raise ValueError(f"Location with id {location_id} not found")
            
            availability = await self._check_location_availability(
                sku_id, location_id, quantity, target_status, min_condition_grade
            )
        else:
            # Check across all locations
            availability = await self._check_global_availability(
                sku_id, quantity, target_status, min_condition_grade
            )
        
        return availability
    
    async def check_multiple_skus(
        self,
        items: List[Dict[str, any]],
        location_id: Optional[UUID] = None,
        for_sale: bool = True
    ) -> Dict[str, Dict]:
        """Check availability for multiple SKUs at once."""
        results = {}
        
        for item in items:
            sku_id = item.get('sku_id')
            quantity = item.get('quantity', 1)
            min_condition = item.get('min_condition_grade')
            
            try:
                availability = await self.execute(
                    sku_id=sku_id,
                    quantity=quantity,
                    location_id=location_id,
                    for_sale=for_sale,
                    min_condition_grade=min_condition
                )
                results[str(sku_id)] = availability
            except ValueError as e:
                results[str(sku_id)] = {
                    'available': False,
                    'error': str(e)
                }
        
        return results
    
    async def _check_location_availability(
        self,
        sku_id: UUID,
        location_id: UUID,
        quantity: int,
        target_status: InventoryStatus,
        min_condition_grade: Optional[ConditionGrade] = None
    ) -> Dict:
        """Check availability at a specific location."""
        # Get stock level
        stock_level = await self.stock_repository.get_by_sku_location(sku_id, location_id)
        
        if not stock_level:
            return {
                'available': False,
                'requested_quantity': quantity,
                'available_quantity': 0,
                'location_id': str(location_id),
                'stock_details': None,
                'available_units': []
            }
        
        # Get available units
        available_units = await self.inventory_repository.get_available_units(
            sku_id=sku_id,
            location_id=location_id,
            condition_grade=min_condition_grade
        )
        
        # Filter by target status
        available_units = [
            unit for unit in available_units 
            if unit.current_status == target_status
        ]
        
        available_quantity = len(available_units)
        
        return {
            'available': available_quantity >= quantity,
            'requested_quantity': quantity,
            'available_quantity': available_quantity,
            'location_id': str(location_id),
            'stock_details': {
                'total_on_hand': stock_level.quantity_on_hand,
                'total_available': stock_level.quantity_available,
                'reserved': stock_level.quantity_reserved,
                'damaged': stock_level.quantity_damaged
            },
            'available_units': [
                {
                    'inventory_id': str(unit.id),
                    'inventory_code': unit.inventory_code,
                    'condition_grade': unit.condition_grade.value,
                    'serial_number': unit.serial_number
                }
                for unit in available_units[:quantity]  # Return only requested quantity
            ]
        }
    
    async def _check_global_availability(
        self,
        sku_id: UUID,
        quantity: int,
        target_status: InventoryStatus,
        min_condition_grade: Optional[ConditionGrade] = None
    ) -> Dict:
        """Check availability across all locations."""
        # Get total stock
        total_stock = await self.stock_repository.get_total_stock_by_sku(sku_id)
        
        # Get all locations with stock
        locations_with_stock = []
        total_available = 0
        
        # Get all stock levels for this SKU
        stock_levels, _ = await self.stock_repository.list(sku_id=sku_id)
        
        for stock_level in stock_levels:
            if stock_level.quantity_available > 0:
                # Get available units at this location
                available_units = await self.inventory_repository.get_available_units(
                    sku_id=sku_id,
                    location_id=stock_level.location_id,
                    condition_grade=min_condition_grade
                )
                
                # Filter by target status
                available_units = [
                    unit for unit in available_units 
                    if unit.current_status == target_status
                ]
                
                if available_units:
                    location = await self.location_repository.get_by_id(stock_level.location_id)
                    locations_with_stock.append({
                        'location_id': str(stock_level.location_id),
                        'location_name': location.location_name if location else 'Unknown',
                        'available_quantity': len(available_units),
                        'units': [
                            {
                                'inventory_id': str(unit.id),
                                'inventory_code': unit.inventory_code,
                                'condition_grade': unit.condition_grade.value,
                                'serial_number': unit.serial_number
                            }
                            for unit in available_units
                        ]
                    })
                    total_available += len(available_units)
        
        return {
            'available': total_available >= quantity,
            'requested_quantity': quantity,
            'available_quantity': total_available,  # Add this field
            'total_available_quantity': total_available,
            'stock_summary': total_stock,
            'locations_with_stock': locations_with_stock
        }
    
    async def get_low_stock_alerts(
        self,
        location_id: Optional[UUID] = None,
        include_zero_stock: bool = True
    ) -> List[Dict]:
        """Get items that are low on stock."""
        low_stock_items = await self.stock_repository.get_low_stock_items(
            location_id=location_id,
            include_zero=include_zero_stock
        )
        
        alerts = []
        for stock_level in low_stock_items:
            sku = await self.sku_repository.get_by_id(stock_level.sku_id)
            location = await self.location_repository.get_by_id(stock_level.location_id)
            
            alerts.append({
                'sku_id': str(stock_level.sku_id),
                'sku_code': sku.sku_code if sku else 'Unknown',
                'sku_name': sku.sku_name if sku else 'Unknown',
                'location_id': str(stock_level.location_id),
                'location_name': location.location_name if location else 'Unknown',
                'quantity_available': stock_level.quantity_available,
                'reorder_point': stock_level.reorder_point,
                'reorder_quantity': stock_level.reorder_quantity,
                'urgency': 'critical' if stock_level.quantity_available == 0 else 'warning'
            })
        
        return alerts