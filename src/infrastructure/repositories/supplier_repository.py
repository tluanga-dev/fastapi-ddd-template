from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, desc
from sqlalchemy.orm import selectinload

from ...domain.entities.supplier import Supplier
from ...domain.repositories.supplier_repository import SupplierRepository as ISupplierRepository
from ...domain.value_objects.supplier_type import SupplierType, SupplierTier, PaymentTerms
from ..models.supplier_model import SupplierModel


class SQLAlchemySupplierRepository(ISupplierRepository):
    """SQLAlchemy implementation of supplier repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, supplier: Supplier) -> Supplier:
        """Create a new supplier."""
        model = SupplierModel.from_entity(supplier)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def get_by_id(self, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID."""
        stmt = select(SupplierModel).where(
            and_(SupplierModel.id == supplier_id, SupplierModel.is_active == True)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_code(self, supplier_code: str) -> Optional[Supplier]:
        """Get supplier by supplier code."""
        stmt = select(SupplierModel).where(
            and_(SupplierModel.supplier_code == supplier_code, SupplierModel.is_active == True)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def update(self, supplier: Supplier) -> Supplier:
        """Update an existing supplier."""
        stmt = select(SupplierModel).where(SupplierModel.id == supplier.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Supplier with id {supplier.id} not found")
        
        model.update_from_entity(supplier)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def delete(self, supplier_id: UUID) -> bool:
        """Soft delete a supplier."""
        stmt = select(SupplierModel).where(SupplierModel.id == supplier_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.is_active = False
        await self.session.flush()
        return True

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        supplier_type: Optional[SupplierType] = None,
        supplier_tier: Optional[SupplierTier] = None,
        payment_terms: Optional[PaymentTerms] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Supplier], int]:
        """List suppliers with pagination and filters."""
        # Build base query
        conditions = []
        
        if is_active is not None:
            conditions.append(SupplierModel.is_active == is_active)
        else:
            conditions.append(SupplierModel.is_active == True)
            
        if supplier_type:
            conditions.append(SupplierModel.supplier_type == supplier_type.value)
            
        if supplier_tier:
            conditions.append(SupplierModel.supplier_tier == supplier_tier.value)
            
        if payment_terms:
            conditions.append(SupplierModel.payment_terms == payment_terms.value)
            
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    SupplierModel.company_name.ilike(search_pattern),
                    SupplierModel.supplier_code.ilike(search_pattern),
                    SupplierModel.contact_person.ilike(search_pattern),
                    SupplierModel.email.ilike(search_pattern)
                )
            )

        # Count query
        count_stmt = select(func.count(SupplierModel.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Data query
        stmt = (
            select(SupplierModel)
            .where(and_(*conditions))
            .order_by(SupplierModel.company_name)
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        suppliers = [model.to_entity() for model in models]
        
        return suppliers, total

    async def search_by_name(self, name: str, limit: int = 10) -> List[Supplier]:
        """Search suppliers by company name."""
        search_pattern = f"%{name}%"
        stmt = (
            select(SupplierModel)
            .where(
                and_(
                    SupplierModel.is_active == True,
                    SupplierModel.company_name.ilike(search_pattern)
                )
            )
            .order_by(SupplierModel.company_name)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [model.to_entity() for model in models]

    async def get_by_tier(
        self, 
        tier: SupplierTier, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Supplier], int]:
        """Get suppliers by tier."""
        return await self.list(
            skip=skip,
            limit=limit,
            supplier_tier=tier,
            is_active=True
        )

    async def get_active_suppliers(
        self, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Supplier], int]:
        """Get all active suppliers."""
        return await self.list(skip=skip, limit=limit, is_active=True)

    async def get_top_suppliers_by_spend(self, limit: int = 10) -> List[Supplier]:
        """Get top suppliers by total spend."""
        stmt = (
            select(SupplierModel)
            .where(SupplierModel.is_active == True)
            .order_by(desc(SupplierModel.total_spend))
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [model.to_entity() for model in models]

    async def supplier_code_exists(self, supplier_code: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if supplier code already exists."""
        conditions = [SupplierModel.supplier_code == supplier_code]
        
        if exclude_id:
            conditions.append(SupplierModel.id != exclude_id)
            
        stmt = select(func.count(SupplierModel.id)).where(and_(*conditions))
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def company_name_exists(self, company_name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if company name already exists."""
        conditions = [
            SupplierModel.company_name == company_name,
            SupplierModel.is_active == True
        ]
        
        if exclude_id:
            conditions.append(SupplierModel.id != exclude_id)
            
        stmt = select(func.count(SupplierModel.id)).where(and_(*conditions))
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0

    async def get_supplier_analytics(self) -> dict:
        """Get supplier analytics data."""
        # Total suppliers
        total_result = await self.session.execute(
            select(func.count(SupplierModel.id)).where(SupplierModel.is_active == True)
        )
        total_suppliers = total_result.scalar() or 0

        # Active suppliers (those with orders in last 6 months)
        active_result = await self.session.execute(
            select(func.count(SupplierModel.id)).where(
                and_(
                    SupplierModel.is_active == True,
                    SupplierModel.last_order_date >= func.now() - text("INTERVAL '6 months'")
                )
            )
        )
        active_suppliers = active_result.scalar() or 0

        # Supplier type distribution
        type_result = await self.session.execute(
            select(SupplierModel.supplier_type, func.count(SupplierModel.id))
            .where(SupplierModel.is_active == True)
            .group_by(SupplierModel.supplier_type)
        )
        
        type_distribution = {}
        for supplier_type, count in type_result.fetchall():
            type_distribution[supplier_type.lower()] = count

        # Supplier tier distribution
        tier_result = await self.session.execute(
            select(SupplierModel.supplier_tier, func.count(SupplierModel.id))
            .where(SupplierModel.is_active == True)
            .group_by(SupplierModel.supplier_tier)
        )
        
        tier_distribution = {}
        for tier, count in tier_result.fetchall():
            tier_distribution[tier.lower()] = count

        # Payment terms distribution
        terms_result = await self.session.execute(
            select(SupplierModel.payment_terms, func.count(SupplierModel.id))
            .where(SupplierModel.is_active == True)
            .group_by(SupplierModel.payment_terms)
        )
        
        payment_terms_distribution = {}
        for terms, count in terms_result.fetchall():
            payment_terms_distribution[terms.lower()] = count

        # Top suppliers by spend
        top_suppliers_result = await self.session.execute(
            select(SupplierModel)
            .where(SupplierModel.is_active == True)
            .order_by(desc(SupplierModel.total_spend))
            .limit(10)
        )
        
        top_suppliers = []
        for model in top_suppliers_result.scalars().all():
            supplier = model.to_entity()
            top_suppliers.append({
                "supplier": {
                    "id": str(supplier.id),
                    "supplier_code": supplier.supplier_code,
                    "company_name": supplier.company_name,
                    "supplier_type": supplier.supplier_type.value,
                    "supplier_tier": supplier.supplier_tier.value,
                    "total_spend": float(supplier.total_spend),
                    "total_orders": supplier.total_orders,
                    "quality_rating": float(supplier.quality_rating)
                },
                "total_spend": float(supplier.total_spend)
            })

        # Monthly new suppliers (last 12 months)
        monthly_new = []
        for i in range(12):
            month_start = text(f"date_trunc('month', now() - interval '{i} months')")
            month_end = text(f"date_trunc('month', now() - interval '{i} months') + interval '1 month'")
            
            month_result = await self.session.execute(
                select(func.count(SupplierModel.id))
                .where(
                    and_(
                        SupplierModel.created_at >= month_start,
                        SupplierModel.created_at < month_end
                    )
                )
            )
            count = month_result.scalar() or 0
            
            # Get month string
            month_str_result = await self.session.execute(
                select(func.to_char(month_start, 'YYYY-MM'))
            )
            month_str = month_str_result.scalar()
            
            monthly_new.append({
                "month": month_str,
                "count": count
            })

        monthly_new.reverse()  # Show oldest first

        return {
            "total_suppliers": total_suppliers,
            "active_suppliers": active_suppliers,
            "supplier_type_distribution": type_distribution,
            "supplier_tier_distribution": tier_distribution,
            "payment_terms_distribution": payment_terms_distribution,
            "monthly_new_suppliers": monthly_new,
            "top_suppliers_by_spend": top_suppliers,
            "total_spend": float(sum(s["total_spend"] for s in top_suppliers)),
            "average_quality_rating": float(
                sum(s["supplier"]["quality_rating"] for s in top_suppliers) / 
                len(top_suppliers) if top_suppliers else 0
            )
        }