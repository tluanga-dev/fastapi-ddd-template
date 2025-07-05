import time
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ....domain.entities.item_master import ItemMaster
from ....domain.entities.sku import SKU
from ....domain.entities.transaction_header import TransactionHeader
from ....domain.repositories.customer_repository import CustomerRepository
from ....domain.repositories.item_master_repository import ItemMasterRepository
from ....domain.repositories.inventory_unit_repository import InventoryUnitRepository
from ....domain.repositories.sku_repository import SKURepository
from ....domain.repositories.stock_level_repository import StockLevelRepository
from ....domain.repositories.transaction_header_repository import (
    TransactionHeaderRepository,
)
from ....domain.repositories.transaction_line_repository import (
    TransactionLineRepository,
)
from ....domain.value_objects.transaction_type import TransactionType
from ..item_master.create_item_master_use_case import CreateItemMasterUseCase
from ..sku.create_sku_use_case import CreateSKUUseCase
from .record_completed_purchase_use_case import RecordCompletedPurchaseUseCase


class CreateBatchPurchaseUseCase:
    """
    Use case for creating a purchase transaction with embedded item master and SKU creation.

    This use case handles the complex workflow of:
    1. Creating new item masters if needed
    2. Creating new SKUs if needed
    3. Creating the purchase transaction
    4. Handling rollbacks if any step fails
    """

    def __init__(
        self,
        transaction_repo: TransactionHeaderRepository,
        line_repo: TransactionLineRepository,
        item_master_repo: ItemMasterRepository,
        sku_repo: SKURepository,
        customer_repo: CustomerRepository,
        inventory_repo: InventoryUnitRepository,
        stock_repo: StockLevelRepository,
    ):
        self.transaction_repo = transaction_repo
        self.line_repo = line_repo
        self.item_master_repo = item_master_repo
        self.sku_repo = sku_repo
        self.customer_repo = customer_repo
        self.inventory_repo = inventory_repo
        self.stock_repo = stock_repo

        # Initialize child use cases
        self.create_item_master_use_case = CreateItemMasterUseCase(item_master_repo)
        self.create_sku_use_case = CreateSKUUseCase(sku_repo, item_master_repo)
        self.purchase_use_case = RecordCompletedPurchaseUseCase(
            transaction_repo,
            line_repo,
            sku_repo,
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
            "skus_to_create": 0,
            "existing_skus": 0,
            "generated_item_codes": [],
            "generated_sku_codes": [],
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

            if item_data.get("sku_id"):
                # Validate existing SKU
                sku = await self.sku_repo.get_by_id(item_data["sku_id"])
                if not sku:
                    validation_errors.append(
                        f"{item_prefix}SKU with ID {item_data['sku_id']} not found"
                    )
                else:
                    preview_info["existing_skus"] += 1

            elif item_data.get("new_item_master") and item_data.get("new_sku"):
                # Validate new item master and SKU creation
                new_item_data = item_data["new_item_master"]
                new_sku_data = item_data["new_sku"]

                # Generate codes if needed
                if auto_generate_codes:
                    if not new_item_data.get("item_code"):
                        generated_code = await self._generate_item_code(
                            new_item_data["item_name"]
                        )
                        new_item_data["item_code"] = generated_code
                        preview_info["generated_item_codes"].append(generated_code)

                    if not new_sku_data.get("sku_code"):
                        generated_code = await self._generate_sku_code(
                            new_sku_data["sku_name"]
                        )
                        new_sku_data["sku_code"] = generated_code
                        preview_info["generated_sku_codes"].append(generated_code)

                # Validate item master data
                if not new_item_data.get("item_code"):
                    validation_errors.append(f"{item_prefix}Item code is required")
                else:
                    # Check if item code already exists
                    existing_item = await self.item_master_repo.get_by_code(
                        new_item_data["item_code"]
                    )
                    if existing_item:
                        validation_errors.append(
                            f"{item_prefix}Item code '{new_item_data['item_code']}' already exists"
                        )

                # Validate SKU data
                if not new_sku_data.get("sku_code"):
                    validation_errors.append(f"{item_prefix}SKU code is required")
                else:
                    # Check if SKU code already exists
                    existing_sku = await self.sku_repo.get_by_code(
                        new_sku_data["sku_code"]
                    )
                    if existing_sku:
                        validation_errors.append(
                            f"{item_prefix}SKU code '{new_sku_data['sku_code']}' already exists"
                        )

                # Validate rental settings
                if new_sku_data.get("is_rentable"):
                    if not new_sku_data.get("rental_base_price"):
                        warnings.append(
                            f"{item_prefix}Rentable SKU should have a rental base price"
                        )

                    max_days = new_sku_data.get("max_rental_days")
                    min_days = new_sku_data.get("min_rental_days", 1)
                    if max_days and max_days < min_days:
                        validation_errors.append(
                            f"{item_prefix}Maximum rental days must be >= minimum rental days"
                        )

                # Validate sale settings
                if new_sku_data.get("is_saleable"):
                    if not new_sku_data.get("sale_base_price"):
                        warnings.append(
                            f"{item_prefix}Saleable SKU should have a sale base price"
                        )

                preview_info["items_to_create"] += 1
                preview_info["skus_to_create"] += 1

            else:
                validation_errors.append(
                    f"{item_prefix}Must specify either existing sku_id or both new_item_master and new_sku"
                )

        return len(validation_errors) == 0, validation_errors, preview_info

    async def execute(
        self,
        supplier_id: UUID,
        location_id: UUID,
        items: List[Dict],
        purchase_date: date,
        tax_rate: Decimal = Decimal("0"),
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
            items: List of purchase items with optional item master/SKU creation
            purchase_date: Date of the purchase
            tax_rate: Tax rate for the purchase
            invoice_number: External invoice number
            invoice_date: Date of the external invoice
            notes: Additional notes
            auto_generate_codes: Whether to auto-generate item/SKU codes
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
        created_item_masters: List[UUID] = []
        created_skus: List[UUID] = []
        used_existing_skus: List[UUID] = []

        try:
            # Process each item to create item masters and SKUs as needed
            processed_items = []

            for item_data in items:
                if item_data.get("sku_id"):
                    # Use existing SKU
                    sku_id = item_data["sku_id"]
                    used_existing_skus.append(sku_id)

                    processed_items.append(
                        {
                            "sku_id": sku_id,
                            "quantity": item_data["quantity"],
                            "unit_cost": item_data["unit_cost"],
                            "serial_numbers": item_data.get("serial_numbers"),
                            "condition_notes": item_data.get("condition_notes"),
                            "notes": item_data.get("notes"),
                        }
                    )

                else:
                    # Create new item master and SKU
                    item_master_data = item_data["new_item_master"]
                    sku_data = item_data["new_sku"]

                    # Generate codes if needed
                    if auto_generate_codes:
                        if not item_master_data.get("item_code"):
                            item_master_data["item_code"] = (
                                await self._generate_item_code(
                                    item_master_data["item_name"]
                                )
                            )

                        if not sku_data.get("sku_code"):
                            sku_data["sku_code"] = await self._generate_sku_code(
                                sku_data["sku_name"]
                            )

                    # Create item master
                    item_master = await self.create_item_master_use_case.execute(
                        item_code=item_master_data["item_code"],
                        item_name=item_master_data["item_name"],
                        category_id=item_master_data["category_id"],
                        brand_id=item_master_data.get("brand_id"),
                        item_type=item_master_data.get("item_type"),
                        description=item_master_data.get("description"),
                        is_serialized=item_master_data.get("is_serialized", False),
                    )
                    created_item_masters.append(item_master.id)

                    # Create SKU
                    sku = await self.create_sku_use_case.execute(
                        sku_code=sku_data["sku_code"],
                        sku_name=sku_data["sku_name"],
                        item_id=item_master.id,
                        barcode=sku_data.get("barcode"),
                        model_number=sku_data.get("model_number"),
                        weight=sku_data.get("weight"),
                        dimensions=sku_data.get("dimensions"),
                        is_rentable=sku_data.get("is_rentable", False),
                        is_saleable=sku_data.get("is_saleable", True),
                        min_rental_days=sku_data.get("min_rental_days", 1),
                        max_rental_days=sku_data.get("max_rental_days"),
                        rental_base_price=sku_data.get("rental_base_price"),
                        sale_base_price=sku_data.get("sale_base_price"),
                    )
                    created_skus.append(sku.id)

                    processed_items.append(
                        {
                            "sku_id": sku.id,
                            "quantity": item_data["quantity"],
                            "unit_cost": item_data["unit_cost"],
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
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                notes=notes,
            )

            processing_time = int((time.time() - start_time) * 1000)

            return {
                "transaction_id": transaction.id,
                "transaction_number": transaction.transaction_number,
                "created_item_masters": created_item_masters,
                "created_skus": created_skus,
                "used_existing_skus": used_existing_skus,
                "total_amount": transaction.total_amount,
                "total_items": len(processed_items),
                "processing_time_ms": processing_time,
            }

        except Exception as e:
            # Rollback created entities
            await self._rollback_created_entities(created_item_masters, created_skus)
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
            existing = await self.item_master_repo.get_by_code(candidate_code)
            if not existing:
                return candidate_code
            counter += 1

            # Prevent infinite loop
            if counter > 999:
                candidate_code = f"{base_code}-{uuid4().hex[:6].upper()}"
                existing = await self.item_master_repo.get_by_code(candidate_code)
                if not existing:
                    return candidate_code
                break

        # Fallback to UUID
        return f"{base_code}-{uuid4().hex[:8].upper()}"

    async def _generate_sku_code(self, sku_name: str) -> str:
        """Generate a unique SKU code based on SKU name."""
        # Create base code from SKU name
        base_code = "".join(c.upper() for c in sku_name[:10] if c.isalnum())
        if not base_code:
            base_code = "SKU"

        # Find unique code
        counter = 1
        while True:
            candidate_code = f"{base_code}-{counter:03d}"
            existing = await self.sku_repo.get_by_code(candidate_code)
            if not existing:
                return candidate_code
            counter += 1

            # Prevent infinite loop
            if counter > 999:
                candidate_code = f"{base_code}-{uuid4().hex[:6].upper()}"
                existing = await self.sku_repo.get_by_code(candidate_code)
                if not existing:
                    return candidate_code
                break

        # Fallback to UUID
        return f"{base_code}-{uuid4().hex[:8].upper()}"

    async def _rollback_created_entities(
        self, created_item_masters: List[UUID], created_skus: List[UUID]
    ) -> None:
        """Rollback (soft delete) created entities in case of failure."""
        try:
            # Soft delete created SKUs first (due to foreign key constraints)
            for sku_id in created_skus:
                await self.sku_repo.delete(sku_id)

            # Then soft delete created item masters
            for item_id in created_item_masters:
                await self.item_master_repo.delete(item_id)

        except Exception:
            # Log the rollback failure but don't raise - the original error is more important
            pass
