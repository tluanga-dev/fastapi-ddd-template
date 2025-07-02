from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.repositories.transaction_header_repository import TransactionHeaderRepository
from ....domain.repositories.transaction_line_repository import TransactionLineRepository
from ....domain.repositories.sku_repository import SKURepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.value_objects.transaction_type import (
    TransactionType, TransactionStatus, PaymentStatus, LineItemType
)
from ....domain.value_objects.item_type import InventoryStatus


class CreateSaleTransactionUseCase:
    """Use case for creating a sale transaction."""
    
    def __init__(
        self,
        transaction_repository: TransactionHeaderRepository,
        line_repository: TransactionLineRepository,
        sku_repository: SKURepository,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository,
        customer_repository: CustomerRepository
    ):
        """Initialize use case with repositories."""
        self.transaction_repository = transaction_repository
        self.line_repository = line_repository
        self.sku_repository = sku_repository
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository
        self.customer_repository = customer_repository
    
    async def execute(
        self,
        customer_id: UUID,
        location_id: UUID,
        items: List[Dict],
        sales_person_id: Optional[UUID] = None,
        discount_amount: Decimal = Decimal("0.00"),
        tax_rate: Decimal = Decimal("0.00"),
        notes: Optional[str] = None,
        auto_reserve: bool = True,
        created_by: Optional[str] = None
    ) -> TransactionHeader:
        """Execute the use case to create a sale transaction."""
        # Validate customer exists
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")
        
        # Check if customer is active
        if not customer.is_active:
            raise ValueError("Cannot create transaction for inactive customer")
        
        # Generate transaction number
        transaction_number = await self.transaction_repository.generate_transaction_number(
            TransactionType.SALE,
            location_id
        )
        
        # Create transaction header
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.utcnow(),
            customer_id=customer_id,
            location_id=location_id,
            sales_person_id=sales_person_id,
            status=TransactionStatus.DRAFT,
            payment_status=PaymentStatus.PENDING,
            notes=notes,
            created_by=created_by
        )
        
        # Create lines for each item
        lines = []
        line_number = 1
        subtotal = Decimal("0.00")
        
        for item in items:
            sku_id = item.get('sku_id')
            quantity = Decimal(str(item.get('quantity', 1)))
            unit_price = item.get('unit_price')
            discount_percentage = Decimal(str(item.get('discount_percentage', 0)))
            
            # Validate SKU
            sku = await self.sku_repository.get_by_id(sku_id)
            if not sku:
                raise ValueError(f"SKU with id {sku_id} not found")
            
            if not sku.is_saleable:
                raise ValueError(f"SKU {sku.sku_code} is not available for sale")
            
            # Check stock availability
            is_available, available_qty = await self.stock_repository.check_availability(
                sku_id=sku_id,
                quantity=int(quantity),
                location_id=location_id
            )
            
            if not is_available:
                raise ValueError(
                    f"Insufficient stock for SKU {sku.sku_code}. "
                    f"Requested: {quantity}, Available: {available_qty}"
                )
            
            # Use SKU price if not provided
            if unit_price is None:
                unit_price = sku.sale_price
            else:
                unit_price = Decimal(str(unit_price))
            
            # Create line
            line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.PRODUCT,
                sku_id=sku_id,
                description=f"{sku.sku_code} - {sku.sku_name}",
                quantity=quantity,
                unit_price=unit_price,
                discount_percentage=discount_percentage,
                created_by=created_by
            )
            
            # Calculate line total
            line.calculate_line_total()
            subtotal += line.line_total
            
            lines.append(line)
            line_number += 1
            
            # Auto-reserve inventory if requested
            if auto_reserve:
                stock_level = await self.stock_repository.get_by_sku_location(sku_id, location_id)
                if stock_level:
                    stock_level.reserve_stock(int(quantity), created_by)
                    await self.stock_repository.update(stock_level)
        
        # Apply discount if provided
        if discount_amount > 0:
            discount_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.DISCOUNT,
                description="Sale discount",
                quantity=Decimal("1"),
                unit_price=-discount_amount,
                created_by=created_by
            )
            discount_line.calculate_line_total()
            lines.append(discount_line)
            line_number += 1
        
        # Calculate tax
        taxable_amount = subtotal - discount_amount
        if tax_rate > 0 and taxable_amount > 0:
            tax_amount = taxable_amount * (tax_rate / 100)
            tax_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.TAX,
                description=f"Sales tax ({tax_rate}%)",
                quantity=Decimal("1"),
                unit_price=tax_amount,
                created_by=created_by
            )
            tax_line.calculate_line_total()
            lines.append(tax_line)
        
        # Update transaction totals
        transaction.subtotal = subtotal
        transaction.discount_amount = discount_amount
        transaction.tax_amount = tax_amount if tax_rate > 0 else Decimal("0.00")
        transaction.total_amount = taxable_amount + transaction.tax_amount
        
        # Save transaction
        created_transaction = await self.transaction_repository.create(transaction)
        
        # Save lines
        for line in lines:
            line.transaction_id = created_transaction.id
        
        created_lines = await self.line_repository.create_batch(lines)
        created_transaction._lines = created_lines
        
        # Update status to pending if auto-reserve
        if auto_reserve:
            created_transaction.update_status(TransactionStatus.PENDING, created_by)
            await self.transaction_repository.update(created_transaction)
        
        return created_transaction