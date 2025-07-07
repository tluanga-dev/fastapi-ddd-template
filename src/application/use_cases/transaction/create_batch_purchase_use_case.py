import time
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ....domain.entities.item import Item
from ....domain.entities.transaction_header import TransactionHeader
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.repositories.item_repository import ItemRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.transaction_header_repository import (
    TransactionHeaderRepository,
)
from ....domain.repositories.transaction_line_repository import (
    TransactionLineRepository,
)
from ....domain.value_objects.transaction_type import TransactionType
from ..item.create_item_use_case import CreateItemUseCase
from .record_completed_purchase_use_case import RecordCompletedPurchaseUseCase


class CreateBatchPurchaseUseCase:
    """
    Use case for creating a purchase transaction with embedded item creation.

    This use case handles the complex workflow of:
    1. Creating new items if needed
    2. Creating the purchase transaction
    3. Handling rollbacks if any step fails
    """

    def __init__(
        self,
        transaction_repo: TransactionHeaderRepository,
        line_repo: TransactionLineRepository,
        item_repo: ItemRepository,
        customer_repo: CustomerRepository,
        inventory_repo: InventoryUnitRepository,
        stock_repo: StockLevelRepository,
    ):
        self.transaction_repo = transaction_repo
        self.line_repo = line_repo
        self.item_repo = item_repo
        self.customer_repo = customer_repo
        self.inventory_repo = inventory_repo
        self.stock_repo = stock_repo

        # Initialize child use cases
        self.create_item_use_case = CreateItemUseCase(item_repo)
        self.purchase_use_case = RecordCompletedPurchaseUseCase(
            transaction_repo,
            line_repo,
            item_repo,
            customer_repo,
            inventory_repo,
            stock_repo,
        )

    async def validate_batch_purchase(
        self,
        supplier_id: UUID,
        location_id: UUID,
        items: List[Dict],
        auto_generate_codes: bool = True,
    ) -> Tuple[bool, List[str], Dict]:
        """
        Validate a batch purchase request without creating any records.

        Returns:
            Tuple of (is_valid, validation_errors, preview_info)
        """
        validation_errors = []
        warnings = []
        preview_info: Dict[str, Any] = {
            "items_to_create": 0,
            "existing_items": 0,
            "generated_item_codes": [],
        }

        # Validate supplier exists and is a business customer
        supplier = await self.customer_repo.get_by_id(supplier_id)
        if not supplier:
            validation_errors.append(f"Supplier with ID {supplier_id} not found")
        elif supplier.customer_type.value != "BUSINESS":
            validation_errors.append("Supplier must be a business customer")

        # Validate each item
        for i, item_data in enumerate(items):
            item_prefix = f"Item {i + 1}: "

            if item_data.get("item_id"):
                # Validate existing Item
                item = await self.item_repo.get_by_id(item_data["item_id"])
                if not item:
                    validation_errors.append(
                        f"{item_prefix}Item with ID {item_data['item_id']} not found"
                    )
                else:
                    preview_info["existing_items"] += 1

            elif item_data.get("new_item"):
                # Validate new item creation
                new_item_data = item_data["new_item"]

                # Generate codes if needed
                if auto_generate_codes:
                    if not new_item_data.get("item_code"):
                        generated_code = await self._generate_item_code(
                            new_item_data["item_name"]
                        )
                        new_item_data["item_code"] = generated_code
                        preview_info["generated_item_codes"].append(generated_code)

                # Validate item data
                if not new_item_data.get("item_code"):
                    validation_errors.append(f"{item_prefix}Item code is required")
                else:
                    # Check if item code already exists
                    existing_item = await self.item_repo.get_by_code(
                        new_item_data["item_code"]
                    )
                    if existing_item:
                        validation_errors.append(
                            f"{item_prefix}Item code '{new_item_data['item_code']}' already exists"
                        )

                # Validate rental settings
                if new_item_data.get("is_rentable"):
                    if not new_item_data.get("rental_base_price"):
                        warnings.append(
                            f"{item_prefix}Rentable Item should have a rental base price"
                        )

                    max_days = new_item_data.get("max_rental_days")
                    min_days = new_item_data.get("min_rental_days", 1)
                    if max_days and max_days < min_days:
                        validation_errors.append(
                            f"{item_prefix}Maximum rental days must be >= minimum rental days"
                        )

                # Validate sale settings
                if new_item_data.get("is_saleable"):
                    if not new_item_data.get("sale_base_price"):
                        warnings.append(
                            f"{item_prefix}Saleable Item should have a sale base price"
                        )

                preview_info["items_to_create"] += 1

            else:
                validation_errors.append(
                    f"{item_prefix}Must specify either existing item_id or new_item"
                )

        return len(validation_errors) == 0, validation_errors, preview_info

    async def execute(
        self,
        supplier_id: UUID,
        location_id: UUID,
        items: List[Dict],
        purchase_date: date,
        tax_rate: Decimal = Decimal("0"),
        tax_amount: Optional[Decimal] = None,
        discount_amount: Decimal = Decimal("0"),
        invoice_number: Optional[str] = None,
        invoice_date: Optional[date] = None,
        notes: Optional[str] = None,
        auto_generate_codes: bool = True,
        validate_only: bool = False,
    ) -> Dict:
        """
        Execute the batch purchase creation workflow.

        Args:
            supplier_id: ID of the supplier (business customer)
            location_id: ID of the location where items will be stored
            items: List of purchase items with optional item creation
            purchase_date: Date of the purchase
            tax_rate: Tax rate for the purchase
            invoice_number: External invoice number
            invoice_date: Date of the external invoice
            notes: Additional notes
            auto_generate_codes: Whether to auto-generate item codes
            validate_only: Only validate without creating records

        Returns:
            Dictionary with transaction details and created entity IDs

        Raises:
            ValueError: If validation fails or creation fails
        """
        start_time = time.time()

        # Validate the entire batch first
        is_valid, validation_errors, preview_info = await self.validate_batch_purchase(
            supplier_id, location_id, items, auto_generate_codes
        )

        if not is_valid:
            raise ValueError(
                f"Batch purchase validation failed: {'; '.join(validation_errors)}"
            )

        if validate_only:
            return {
                "validation_only": True,
                "is_valid": True,
                "preview_info": preview_info,
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }

        # Track created entities for rollback
        created_items: List[UUID] = []
        used_existing_items: List[UUID] = []

        try:
            # Process each item to create item masters and SKUs as needed
            processed_items = []

            for item_data in items:
                if item_data.get("item_id"):
                    # Use existing Item
                    item_id = item_data["item_id"]
                    used_existing_items.append(item_id)

                    processed_items.append(
                        {
                            "item_id": item_id,
                            "quantity": item_data["quantity"],
                            "unit_cost": item_data["unit_cost"],
                            "tax_rate": item_data.get("tax_rate", Decimal("0")),
                            "tax_amount": item_data.get("tax_amount", Decimal("0")),
                            "discount_amount": item_data.get("discount_amount", Decimal("0")),
                            "serial_numbers": item_data.get("serial_numbers"),
                            "condition_notes": item_data.get("condition_notes"),
                            "notes": item_data.get("notes"),
                        }
                    )

                else:
                    # Create new item
                    new_item_data = item_data["new_item"]

                    # Generate codes if needed
                    if auto_generate_codes:
                        if not new_item_data.get("item_code"):
                            new_item_data["item_code"] = (
                                await self._generate_item_code(
                                    new_item_data["item_name"]
                                )
                            )

                    # Create item
                    item = await self.create_item_use_case.execute(
                        item_code=new_item_data["item_code"],
                        item_name=new_item_data["item_name"],
                        category_id=new_item_data["category_id"],
                        brand_id=new_item_data.get("brand_id"),
                        item_type=new_item_data.get("item_type"),
                        description=new_item_data.get("description"),
                        barcode=new_item_data.get("barcode"),
                        model_number=new_item_data.get("model_number"),
                        weight=new_item_data.get("weight"),
                        dimensions=new_item_data.get("dimensions"),
                        is_serialized=new_item_data.get("is_serialized", False),
                        is_rentable=new_item_data.get("is_rentable", False),
                        is_saleable=new_item_data.get("is_saleable", True),
                        min_rental_days=new_item_data.get("min_rental_days", 1),
                        max_rental_days=new_item_data.get("max_rental_days"),
                        rental_base_price=new_item_data.get("rental_base_price"),
                        sale_base_price=new_item_data.get("sale_base_price"),
                    )
                    created_items.append(item.id)

                    processed_items.append(
                        {
                            "item_id": item.id,
                            "quantity": item_data["quantity"],
                            "unit_cost": item_data["unit_cost"],
                            "tax_rate": item_data.get("tax_rate", Decimal("0")),
                            "tax_amount": item_data.get("tax_amount", Decimal("0")),
                            "discount_amount": item_data.get("discount_amount", Decimal("0")),
                            "serial_numbers": item_data.get("serial_numbers"),
                            "condition_notes": item_data.get("condition_notes"),
                            "notes": item_data.get("notes"),
                        }
                    )

            # Create the purchase transaction
            transaction = await self.purchase_use_case.execute(
                supplier_id=supplier_id,
                location_id=location_id,
                items=processed_items,
                purchase_date=purchase_date,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                notes=notes,
            )

            processing_time = int((time.time() - start_time) * 1000)

            return {
                "transaction_id": transaction.id,
                "transaction_number": transaction.transaction_number,
                "created_items": created_items,
                "used_existing_items": used_existing_items,
                "total_amount": transaction.total_amount,
                "total_items": len(processed_items),
                "processing_time_ms": processing_time,
            }

        except Exception as e:
            # Rollback created entities
            await self._rollback_created_entities(created_items)
            raise ValueError(f"Batch purchase creation failed: {str(e)}")

    async def _generate_item_code(self, item_name: str) -> str:
        """Generate a unique item code based on item name."""
        # Create base code from item name
        base_code = "".join(c.upper() for c in item_name[:10] if c.isalnum())
        if not base_code:
            base_code = "ITEM"

        # Find unique code
        counter = 1
        while True:
            candidate_code = f"{base_code}-{counter:03d}"
            existing = await self.item_repo.get_by_code(candidate_code)
            if not existing:
                return candidate_code
            counter += 1

            # Prevent infinite loop
            if counter > 999:
                candidate_code = f"{base_code}-{uuid4().hex[:6].upper()}"
                existing = await self.item_repo.get_by_code(candidate_code)
                if not existing:
                    return candidate_code
                break

        # Fallback to UUID
        return f"{base_code}-{uuid4().hex[:8].upper()}"


    async def _rollback_created_entities(
        self, created_items: List[UUID]
    ) -> None:
        """Rollback (soft delete) created entities in case of failure."""
        try:
            # Soft delete created items
            for item_id in created_items:
                await self.item_repo.delete(item_id)

        except Exception:
            # Log the rollback failure but don't raise - the original error is more important
            pass
