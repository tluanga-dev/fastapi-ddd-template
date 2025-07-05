from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from ....domain.entities.transaction_header import TransactionHeader
from ....domain.entities.transaction_line import TransactionLine
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.sku_repository import SKURepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.transaction_header_repository import (
    TransactionHeaderRepository,
)
from ....domain.repositories.transaction_line_repository import (
    TransactionLineRepository,
)
from ....domain.value_objects.item_type import InventoryStatus
from ....domain.value_objects.transaction_type import (
    LineItemType,
    PaymentStatus,
    TransactionStatus,
    TransactionType,
)


class RecordCompletedSaleUseCase:
    """Use case for recording a completed sale transaction and processing inventory."""

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
        customer_id: UUID,
        location_id: UUID,
        items: List[Dict],
        sale_date: date,
        tax_rate: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        receipt_number: Optional[str] = None,
        receipt_date: Optional[date] = None,
        notes: Optional[str] = None,
        sales_person_id: Optional[UUID] = None,
        created_by: Optional[str] = None,
    ) -> TransactionHeader:
        """Execute the use case to record a completed sale transaction."""
        # Validate customer exists and is active
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with id {customer_id} not found")

        if not customer.is_active:
            raise ValueError("Cannot record sale for inactive customer")

        # Validate stock availability for all items before processing
        await self._validate_sale_items(items, location_id)

        # Generate sale transaction number
        transaction_number = (
            await self.transaction_repository.generate_transaction_number(
                TransactionType.SALE, location_id
            )
        )

        # Create transaction header
        transaction = TransactionHeader(
            transaction_number=transaction_number,
            transaction_type=TransactionType.SALE,
            transaction_date=datetime.combine(sale_date, datetime.min.time()),
            customer_id=customer_id,
            location_id=location_id,
            sales_person_id=sales_person_id,
            status=TransactionStatus.COMPLETED,  # Immediately completed
            payment_status=PaymentStatus.PAID,  # Sale is already paid
            notes=notes,
            created_by=created_by,
        )

        # Add receipt information to notes if provided
        receipt_info = []
        if receipt_number:
            receipt_info.append(f"Receipt: {receipt_number}")
        if receipt_date:
            receipt_info.append(f"Receipt Date: {receipt_date.strftime('%Y-%m-%d')}")

        if receipt_info:
            receipt_note = " | ".join(receipt_info)
            transaction.notes = f"{notes}\n{receipt_note}" if notes else receipt_note

        # Create lines for each item and process inventory immediately
        lines = []
        line_number = 1
        subtotal = Decimal("0.00")

        for item in items:
            sku_id = item.get("sku_id")
            quantity = Decimal(str(item.get("quantity", 1)))
            unit_price = Decimal(str(item.get("unit_price", 0)))
            discount_percentage = Decimal(str(item.get("discount_percentage", 0)))
            serial_numbers = item.get("serial_numbers", [])
            condition_notes = item.get("condition_notes")
            item_notes = item.get("notes")

            # Get SKU details
            sku = await self.sku_repository.get_by_id(sku_id)
            if not sku:
                raise ValueError(f"SKU with id {sku_id} not found")

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
                unit_price=unit_price,
                discount_percentage=discount_percentage,
                created_by=created_by,
            )

            # Calculate line total
            line.calculate_line_total()
            subtotal += line.line_total

            lines.append(line)
            line_number += 1

            # Process inventory immediately
            await self._process_inventory_sale(
                sku=sku,
                quantity=quantity,
                unit_price=unit_price,
                location_id=location_id,
                sale_date=sale_date,
                customer_id=customer_id,
                serial_numbers=serial_numbers,
                condition_notes=condition_notes,
                created_by=created_by,
            )

            # Update stock levels immediately
            await self._update_stock_levels(
                sku_id=sku_id,
                location_id=location_id,
                quantity_decrease=int(quantity),
                updated_by=created_by,
            )

        # Apply overall discount if provided
        if discount_amount > 0:
            discount_line = TransactionLine(
                transaction_id=transaction.id,
                line_number=line_number,
                line_type=LineItemType.DISCOUNT,
                description="Sale discount",
                quantity=Decimal("1"),
                unit_price=-discount_amount,
                created_by=created_by,
            )
            discount_line.calculate_line_total()
            lines.append(discount_line)
            line_number += 1

        # Calculate tax on subtotal minus discount
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
                created_by=created_by,
            )
            tax_line.calculate_line_total()
            lines.append(tax_line)
        else:
            tax_amount = Decimal("0.00")

        # Update transaction totals
        transaction.subtotal = subtotal
        transaction.discount_amount = discount_amount
        transaction.tax_amount = tax_amount
        transaction.total_amount = taxable_amount + tax_amount
        transaction.paid_amount = transaction.total_amount  # Sale is already paid

        # Save transaction
        created_transaction = await self.transaction_repository.create(transaction)

        # Save lines
        for line in lines:
            line.transaction_id = created_transaction.id

        created_lines = await self.line_repository.create_batch(lines)
        created_transaction._lines = created_lines

        return created_transaction

    async def _validate_sale_items(self, items: List[Dict], location_id: UUID):
        """Validate that all items can be sold (stock availability check)."""
        for item in items:
            sku_id = item.get("sku_id")
            quantity = Decimal(str(item.get("quantity", 1)))
            serial_numbers = item.get("serial_numbers", [])

            # Validate SKU exists and is saleable
            sku = await self.sku_repository.get_by_id(sku_id)
            if not sku:
                raise ValueError(f"SKU with id {sku_id} not found")

            if not sku.is_active:
                raise ValueError(f"SKU {sku.sku_code} is not active")

            if not sku.is_saleable:
                raise ValueError(f"SKU {sku.sku_code} is not available for sale")

            # Check stock availability
            is_available, available_qty = (
                await self.stock_repository.check_availability(
                    sku_id=sku_id, quantity=int(quantity), location_id=location_id
                )
            )

            if not is_available:
                raise ValueError(
                    f"Insufficient stock for SKU {sku.sku_code}. "
                    f"Requested: {quantity}, Available: {available_qty}"
                )

            # For serialized items, validate serial numbers
            if sku.is_serialized:
                if not serial_numbers:
                    raise ValueError(
                        f"Serial numbers required for serialized SKU {sku.sku_code}"
                    )

                if len(serial_numbers) != int(quantity):
                    raise ValueError(
                        f"Number of serial numbers ({len(serial_numbers)}) "
                        f"must match quantity ({quantity})"
                    )

                # Validate each serial number exists and is available
                for serial_number in serial_numbers:
                    inventory_unit = (
                        await self.inventory_repository.get_by_serial_number(
                            serial_number
                        )
                    )
                    if not inventory_unit:
                        raise ValueError(f"Serial number {serial_number} not found")

                    if inventory_unit.current_status != InventoryStatus.AVAILABLE_SALE:
                        raise ValueError(
                            f"Serial number {serial_number} is not available for sale "
                            f"(current status: {inventory_unit.current_status})"
                        )

    async def _process_inventory_sale(
        self,
        sku,
        quantity: Decimal,
        unit_price: Decimal,
        location_id: UUID,
        sale_date: date,
        customer_id: UUID,
        serial_numbers: List[str] = None,
        condition_notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ):
        """Process inventory for sold items."""

        if sku.is_serialized:
            # Mark specific inventory units as sold
            for serial_number in serial_numbers:
                inventory_unit = await self.inventory_repository.get_by_serial_number(
                    serial_number
                )
                if inventory_unit:
                    inventory_unit.mark_as_sold(
                        sale_date=sale_date,
                        customer_id=customer_id,
                        sale_price=unit_price,
                        updated_by=created_by,
                    )
                    if condition_notes:
                        inventory_unit.notes = (
                            f"{inventory_unit.notes}\nSale condition: {condition_notes}"
                            if inventory_unit.notes
                            else f"Sale condition: {condition_notes}"
                        )

                    await self.inventory_repository.update(inventory_unit)
        else:
            # For non-serialized items, inventory is managed through stock levels
            # No individual inventory units to mark as sold
            pass

    async def _update_stock_levels(
        self,
        sku_id: UUID,
        location_id: UUID,
        quantity_decrease: int,
        updated_by: Optional[str] = None,
    ):
        """Update stock levels for sold items."""

        # Get existing stock level
        stock_level = await self.stock_repository.get_by_sku_location(
            sku_id, location_id
        )

        if stock_level:
            # Confirm sale (this will decrease available quantities)
            stock_level.confirm_sale(quantity_decrease, updated_by)
            stock_level.last_updated = datetime.utcnow()
            await self.stock_repository.update(stock_level)
        else:
            # This should not happen if validation passed, but handle gracefully
            raise ValueError(
                f"No stock level found for SKU {sku_id} at location {location_id}"
            )
