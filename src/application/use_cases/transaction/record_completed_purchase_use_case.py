from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
import uuid

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.entities.inventory_unit import InventoryUnit
from ....domain.entities.stock_level import StockLevel
from ....domain.repositories.transaction_header_repository import (
    TransactionHeaderRepository,
)
from ....domain.repositories.transaction_line_repository import (
    TransactionLineRepository,
)
from ....domain.repositories.sku_repository import SKURepository
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.value_objects.transaction_type import (
    TransactionType,
    TransactionStatus,
    PaymentStatus,
    LineItemType,
)
from ....domain.value_objects.customer_type import CustomerType
from ....domain.value_objects.item_type import InventoryStatus


class RecordCompletedPurchaseUseCase:
    """Use case for recording a completed purchase transaction and creating inventory records."""

    def __init__(
        self,
        transaction_repository: TransactionHeaderRepository,
        line_repository: TransactionLineRepository,
        sku_repository: SKURepository,
        customer_repository: CustomerRepository,
        inventory_repository: InventoryUnitRepository,
        stock_repository: StockLevelRepository,
    ):
        """Initialize use case with repositories."""
        self.transaction_repository = transaction_repository
        self.line_repository = line_repository
        self.sku_repository = sku_repository
        self.customer_repository = customer_repository
        self.inventory_repository = inventory_repository
        self.stock_repository = stock_repository

    async def execute(
        self,
        supplier_id: UUID,
        location_id: UUID,
        items: List[Dict],
        purchase_date: date,
        tax_rate: Decimal = Decimal("0.00"),
        invoice_number: Optional[str] = None,
        invoice_date: Optional[date] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> TransactionHeader:
        """Execute the use case to record a completed purchase transaction."""
        # Validate supplier exists and is a business
        supplier = await self.customer_repository.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")

        if supplier.customer_type != CustomerType.BUSINESS:
            raise ValueError("Supplier must be a business customer")

        # Check if supplier is active
        if not supplier.is_active:
            raise ValueError("Cannot record purchase for inactive supplier")

        # Generate purchase transaction number
        transaction_number = (
            await self.transaction_repository.generate_transaction_number(
                TransactionType.PURCHASE, location_id
            )
        )

        # Create transaction header
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.PURCHASE,
            transaction_date=datetime.combine(purchase_date, datetime.min.time()),
            customer_id=supplier_id,  # Supplier stored as customer
            location_id=location_id,
            status=TransactionStatus.COMPLETED,  # Immediately completed
            payment_status=PaymentStatus.PAID,  # Purchase is already paid
            notes=notes,
            created_by=created_by,
        )

        # Add invoice information to notes if provided
        invoice_info = []
        if invoice_number:
            invoice_info.append(f"Invoice: {invoice_number}")
        if invoice_date:
            invoice_info.append(f"Invoice Date: {invoice_date.strftime('%Y-%m-%d')}")

        if invoice_info:
            invoice_note = " | ".join(invoice_info)
            transaction.notes = f"{notes}\n{invoice_note}" if notes else invoice_note

        # Create lines for each item and process inventory immediately
        lines = []
        line_number = 1
        subtotal = Decimal("0.00")

        for item in items:
            sku_id = item.get("sku_id")
            quantity = Decimal(str(item.get("quantity", 1)))
            unit_cost = Decimal(str(item.get("unit_cost", 0)))
            serial_numbers = item.get("serial_numbers", [])
            condition_notes = item.get("condition_notes")
            item_notes = item.get("notes")

            # Validate SKU
            sku = await self.sku_repository.get_by_id(sku_id)
            if not sku:
                raise ValueError(f"SKU with id {sku_id} not found")

            if not sku.is_active:
                raise ValueError(f"SKU {sku.sku_code} is not active")

            # Create line
            description = f"{sku.sku_code} - {sku.sku_name}"
            if item_notes:
                description += f" ({item_notes})"

            line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.PRODUCT,
                sku_id=sku_id,
                description=description,
                quantity=quantity,
                unit_price=unit_cost,  # This is the purchase cost
                discount_percentage=Decimal("0"),
                created_by=created_by,
            )

            # Calculate line total
            line.calculate_line_total()
            subtotal += line.line_total

            lines.append(line)
            line_number += 1

            # Create inventory records immediately
            await self._create_inventory_units(
                sku=sku,
                quantity=quantity,
                unit_cost=unit_cost,
                location_id=location_id,
                purchase_date=purchase_date,
                serial_numbers=serial_numbers,
                condition_notes=condition_notes,
                created_by=created_by,
            )

            # Update stock levels immediately
            await self._update_stock_levels(
                sku_id=sku_id,
                location_id=location_id,
                quantity_increase=int(quantity),
                updated_by=created_by,
            )

        # Calculate tax
        if tax_rate > 0 and subtotal > 0:
            tax_amount = subtotal * (tax_rate / 100)
            tax_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.TAX,
                description=f"Purchase tax ({tax_rate}%)",
                quantity=Decimal("1"),
                unit_price=tax_amount,
                created_by=created_by,
            )
            tax_line.calculate_line_total()
            lines.append(tax_line)
        else:
            tax_amount = Decimal("0.00")

        # Update transaction totals
        transaction.subtotal = subtotal
        transaction.discount_amount = Decimal("0.00")
        transaction.tax_amount = tax_amount
        transaction.total_amount = subtotal + tax_amount
        transaction.paid_amount = transaction.total_amount  # Purchase is already paid

        # Save transaction
        created_transaction = await self.transaction_repository.create(transaction)

        # Save lines
        for line in lines:
            line.transaction_id = created_transaction.id

        created_lines = await self.line_repository.create_batch(lines)
        created_transaction._lines = created_lines

        return created_transaction

    async def _create_inventory_units(
        self,
        sku,
        quantity: Decimal,
        unit_cost: Decimal,
        location_id: UUID,
        purchase_date: date,
        serial_numbers: List[str] = None,
        condition_notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ):
        """Create inventory units for purchased goods."""

        if sku.is_serialized:
            # Create one inventory unit per serial number
            if not serial_numbers:
                raise ValueError(
                    f"Serial numbers required for serialized SKU {sku.sku_code}"
                )

            if len(serial_numbers) != int(quantity):
                raise ValueError(
                    f"Number of serial numbers ({len(serial_numbers)}) "
                    f"must match quantity ({quantity})"
                )

            for serial_number in serial_numbers:
                # Check if serial number already exists
                existing = await self.inventory_repository.get_by_serial_number(
                    serial_number
                )
                if existing:
                    raise ValueError(f"Serial number {serial_number} already exists")

                inventory_unit = InventoryUnit(
                    inventory_id=self._generate_inventory_id(),
                    sku_id=sku.id,
                    serial_number=serial_number,
                    location_id=location_id,
                    current_status=(
                        InventoryStatus.AVAILABLE_SALE
                        if sku.is_saleable
                        else InventoryStatus.AVAILABLE_RENT
                    ),
                    condition_grade="A",  # New items start with grade A
                    purchase_date=purchase_date,
                    purchase_cost=unit_cost,
                    created_by=created_by,
                )

                if condition_notes:
                    inventory_unit.notes = condition_notes

                await self.inventory_repository.create(inventory_unit)
        else:
            # For non-serialized items, we don't create individual inventory units
            # Stock levels are updated separately
            pass

    async def _update_stock_levels(
        self,
        sku_id: UUID,
        location_id: UUID,
        quantity_increase: int,
        updated_by: Optional[str] = None,
    ):
        """Update stock levels for purchased goods."""

        # Get existing stock level or create new one
        stock_level = await self.stock_repository.get_by_sku_location(
            sku_id, location_id
        )

        if stock_level:
            # Update existing stock level
            stock_level.total_quantity += quantity_increase
            stock_level.available_sale += quantity_increase
            stock_level.last_updated = datetime.utcnow()
            await self.stock_repository.update(stock_level)
        else:
            # Create new stock level
            sku = await self.sku_repository.get_by_id(sku_id)
            stock_level = StockLevel(
                sku_id=sku_id,
                location_id=location_id,
                total_quantity=quantity_increase,
                available_sale=quantity_increase if sku.is_saleable else 0,
                available_rent=quantity_increase if sku.is_rentable else 0,
                reserved=0,
                in_transit=0,
                damaged=0,
            )
            await self.stock_repository.create(stock_level)

    def _generate_inventory_id(self) -> str:
        """Generate a unique inventory ID."""
        return f"INV-{str(uuid.uuid4())[:8].upper()}"
