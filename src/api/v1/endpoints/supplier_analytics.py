from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....infrastructure.repositories.supplier_repository import SQLAlchemySupplierRepository
from ..dependencies.database import get_db
from ..schemas.supplier_schemas import SupplierAnalytics

router = APIRouter(prefix="/analytics", tags=["supplier-analytics"])


@router.get("/suppliers")
async def get_supplier_analytics(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get supplier analytics data."""
    try:
        repository = SQLAlchemySupplierRepository(db)
        analytics = await repository.get_supplier_analytics()
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate supplier analytics: {str(e)}"
        )


@router.get("/suppliers/{supplier_id}/performance")
async def get_supplier_performance_history(
    supplier_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get supplier performance history and trends."""
    try:
        repository = SQLAlchemySupplierRepository(db)
        
        # Get the supplier
        from uuid import UUID
        supplier = await repository.get_by_id(UUID(supplier_id))
        
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with id {supplier_id} not found"
            )
        
        # For now, return basic performance data
        # In a full implementation, this would include historical trends
        return {
            "supplier": {
                "id": str(supplier.id),
                "supplier_code": supplier.supplier_code,
                "company_name": supplier.company_name,
                "supplier_type": supplier.supplier_type.value,
                "supplier_tier": supplier.supplier_tier.value
            },
            "performance_metrics": {
                "total_orders": supplier.total_orders,
                "total_spend": float(supplier.total_spend),
                "average_delivery_days": supplier.average_delivery_days,
                "quality_rating": float(supplier.quality_rating),
                "performance_score": float(supplier.get_performance_score()),
                "last_order_date": supplier.last_order_date.isoformat() if supplier.last_order_date else None
            },
            "trends": {
                "delivery_trend": "stable",  # Would be calculated from historical data
                "quality_trend": "improving",  # Would be calculated from historical data
                "spend_trend": "increasing"  # Would be calculated from historical data
            },
            "recommendations": [
                "Consider increasing order frequency for better pricing",
                "Supplier shows consistent quality delivery",
                "Good candidate for preferred supplier status"
            ] if supplier.get_performance_score() > 70 else [
                "Monitor delivery performance closely",
                "Consider quality improvement discussions",
                "Evaluate alternative suppliers"
            ]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supplier performance data: {str(e)}"
        )