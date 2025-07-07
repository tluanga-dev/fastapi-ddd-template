from typing import Optional, List, Dict, Union
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from .item_schemas import ItemCreate
from .purchase_transaction import CompletedPurchaseItemRecord, CompletedPurchaseRecord


class NewItemMasterForPurchase(BaseModel):
    """Schema for creating a new item master within a purchase workflow."""

    # Override to allow generation if not provided
    item_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Unique item code (auto-generated if not provided)",
    )
    item_name: str = Field(..., min_length=1, max_length=200, description="Item name")
    category_id: UUID = Field(..., description="Category ID")
    brand_id: Optional[UUID] = Field(None, description="Brand ID")
    description: Optional[str] = Field(None, description="Item description")
    is_serialized: bool = Field(False, description="Whether item requires serial tracking")


class NewSKUForPurchase(BaseModel):
    """Schema for creating a new SKU within a purchase workflow."""

    # Core SKU fields - item_id will be set from newly created item master
    sku_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Unique SKU code (auto-generated if not provided)",
    )
    sku_name: str = Field(..., min_length=1, max_length=200, description="SKU name")
    barcode: Optional[str] = Field(None, max_length=50, description="Barcode/UPC")
    model_number: Optional[str] = Field(
        None, max_length=100, description="Model number"
    )
    weight: Optional[Decimal] = Field(None, ge=0, description="Weight in kg")
    dimensions: Optional[Dict[str, Decimal]] = Field(
        None, description="Dimensions in cm"
    )

    # Business settings
    is_rentable: bool = Field(False, description="Available for rent")
    is_saleable: bool = Field(True, description="Available for sale")
    min_rental_days: int = Field(1, ge=1, description="Minimum rental days")
    max_rental_days: Optional[int] = Field(
        None, ge=1, description="Maximum rental days"
    )
    rental_base_price: Optional[Decimal] = Field(
        None, ge=0, description="Base rental price per day"
    )
    sale_base_price: Optional[Decimal] = Field(
        None, ge=0, description="Base sale price"
    )

    @field_validator("dimensions")
    def validate_dimensions(cls, v):
        if v:
            for key, value in v.items():
                if value < 0:
                    raise ValueError(f"Dimension {key} cannot be negative")
        return v

    @field_validator("max_rental_days")
    def validate_max_rental_days(cls, v, values):
        if (
            v is not None
            and "min_rental_days" in values
            and v < values["min_rental_days"]
        ):
            raise ValueError("Maximum rental days must be >= minimum rental days")
        return v


class BatchPurchaseItemRecord(BaseModel):
    """Schema for a purchase item that may include item master and SKU creation."""

    # Purchase line item details
    quantity: Decimal = Field(..., gt=0, description="Quantity purchased")
    unit_cost: Decimal = Field(..., ge=0, description="Cost per unit")
    tax_rate: Optional[Decimal] = Field(
        Decimal("0"), ge=0, le=100, description="Item-specific tax rate percentage"
    )
    tax_amount: Optional[Decimal] = Field(
        Decimal("0"), ge=0, description="Item-specific tax amount (calculated field)"
    )
    discount_amount: Optional[Decimal] = Field(
        Decimal("0"), ge=0, description="Item-specific discount amount"
    )
    serial_numbers: Optional[List[str]] = Field(
        None, description="Serial numbers for serialized items"
    )
    condition_notes: Optional[str] = Field(
        None, description="Condition/quality notes for received items"
    )
    notes: Optional[str] = Field(None, description="Additional line item notes")

    # Item/SKU reference or creation
    sku_id: Optional[UUID] = Field(None, description="Existing SKU ID")
    new_item_master: Optional[NewItemMasterForPurchase] = Field(
        None, description="Create new item master for this purchase"
    )
    new_sku: Optional[NewSKUForPurchase] = Field(
        None, description="Create new SKU for this purchase"
    )

    @field_validator("sku_id")
    def validate_sku_reference(cls, v, values):
        """Ensure either existing SKU or new item/SKU creation is provided."""
        has_sku_id = v is not None
        has_new_item = values.get("new_item_master") is not None
        has_new_sku = values.get("new_sku") is not None

        if has_sku_id and (has_new_item or has_new_sku):
            raise ValueError(
                "Cannot specify both existing sku_id and new item/SKU creation"
            )

        if not has_sku_id and not (has_new_item and has_new_sku):
            raise ValueError(
                "Must specify either existing sku_id or both new_item_master and new_sku"
            )

        return v


class BatchPurchaseRecord(BaseModel):
    """Schema for batch purchase creation with embedded item master and SKU creation."""

    # Core purchase details (inherited from CompletedPurchaseRecord)
    supplier_id: UUID = Field(
        ..., description="Supplier ID (customer with type=BUSINESS)"
    )
    location_id: UUID = Field(..., description="Location where items will be stored")
    purchase_date: date = Field(
        ..., description="Actual date when purchase was completed"
    )
    tax_rate: Optional[Decimal] = Field(Decimal("0"), ge=0, le=100, description="Purchase-level tax rate percentage")
    tax_amount: Optional[Decimal] = Field(Decimal("0"), ge=0, description="Purchase-level tax amount (calculated field)")
    discount_amount: Optional[Decimal] = Field(Decimal("0"), ge=0, description="Purchase-level fixed discount amount")
    invoice_number: Optional[str] = Field(
        None, description="External supplier invoice number"
    )
    invoice_date: Optional[date] = Field(None, description="Date of supplier invoice")
    notes: Optional[str] = Field(None, description="Transaction notes")

    # Enhanced purchase items that can create new items/SKUs
    items: List[BatchPurchaseItemRecord] = Field(
        ..., min_length=1, description="List of items that were purchased"
    )

    # Workflow options
    auto_generate_codes: bool = Field(
        True, description="Auto-generate item codes and SKU codes if not provided"
    )
    validate_only: bool = Field(
        False, description="Only validate the request without creating records"
    )


class BatchPurchaseValidationResponse(BaseModel):
    """Response schema for batch purchase validation."""

    is_valid: bool = Field(
        ..., description="Whether the batch purchase request is valid"
    )
    validation_errors: List[str] = Field(
        default=[], description="List of validation errors"
    )
    warnings: List[str] = Field(default=[], description="List of warnings")

    # Preview of what would be created
    items_to_create: int = Field(0, description="Number of new item masters to create")
    skus_to_create: int = Field(0, description="Number of new SKUs to create")
    existing_skus: int = Field(0, description="Number of existing SKUs to use")

    # Generated codes preview
    generated_item_codes: List[str] = Field(
        default=[], description="Preview of auto-generated item codes"
    )
    generated_sku_codes: List[str] = Field(
        default=[], description="Preview of auto-generated SKU codes"
    )


class BatchPurchaseResponse(BaseModel):
    """Response schema for successful batch purchase creation."""

    # Transaction details
    transaction_id: UUID = Field(..., description="ID of created purchase transaction")
    transaction_number: str = Field(..., description="Generated transaction number")

    # Created entities summary
    created_item_masters: List[UUID] = Field(
        default=[], description="IDs of newly created item masters"
    )
    created_skus: List[UUID] = Field(
        default=[], description="IDs of newly created SKUs"
    )
    used_existing_skus: List[UUID] = Field(
        default=[], description="IDs of existing SKUs used"
    )

    # Purchase summary
    total_amount: Decimal = Field(..., description="Total purchase amount")
    total_items: int = Field(..., description="Total number of line items")

    # Performance metrics
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class BatchPurchaseErrorResponse(BaseModel):
    """Response schema for batch purchase errors with rollback information."""

    error_type: str = Field(..., description="Type of error that occurred")
    error_message: str = Field(..., description="Detailed error message")
    failed_at_step: str = Field(
        ...,
        description="Which step failed (item_creation, sku_creation, purchase_creation)",
    )

    # Rollback information
    created_entities_rolled_back: Dict[str, List[UUID]] = Field(
        default={}, description="Entities that were created and then rolled back"
    )

    # Validation details for the failure
    validation_errors: List[str] = Field(
        default=[], description="Validation errors that led to failure"
    )

    # Recovery suggestions
    suggested_actions: List[str] = Field(
        default=[], description="Suggested actions to fix the issue"
    )
