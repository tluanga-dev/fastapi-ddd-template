from typing import Optional, List
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

from .transaction import TransactionHeaderBase


class CompletedPurchaseItemRecord(BaseModel):
    """Schema for recording a completed purchase line item."""

    sku_id: UUID = Field(..., description="SKU that was purchased")
    quantity: Decimal = Field(..., gt=0, description="Quantity purchased")
    unit_cost: Decimal = Field(..., ge=0, description="Cost per unit")
    serial_numbers: Optional[List[str]] = Field(
        None, description="Serial numbers for serialized items"
    )
    condition_notes: Optional[str] = Field(
        None, description="Condition/quality notes for received items"
    )
    notes: Optional[str] = Field(None, description="Additional line item notes")


class CompletedPurchaseRecord(TransactionHeaderBase):
    """Schema for recording a completed purchase transaction."""

    supplier_id: UUID = Field(
        ..., description="Supplier ID (customer with type=BUSINESS)"
    )
    purchase_date: date = Field(
        ..., description="Actual date when purchase was completed"
    )
    items: List[CompletedPurchaseItemRecord] = Field(
        ..., description="List of items that were purchased"
    )
    tax_rate: Decimal = Field(Decimal("0"), ge=0, description="Tax rate percentage")
    invoice_number: Optional[str] = Field(
        None, description="External supplier invoice number"
    )
    invoice_date: Optional[date] = Field(None, description="Date of supplier invoice")


# Legacy schemas kept for backward compatibility (marked as deprecated)
class PurchaseItemCreate(CompletedPurchaseItemRecord):
    """
    DEPRECATED: Use CompletedPurchaseItemRecord instead.
    Schema for purchase line item.
    """

    pass


class PurchaseTransactionCreate(CompletedPurchaseRecord):
    """
    DEPRECATED: Use CompletedPurchaseRecord instead.
    Schema for creating purchase transaction.
    """

    # Map new field to old field for compatibility
    expected_delivery_date: Optional[date] = Field(
        None, description="DEPRECATED: Use purchase_date instead"
    )

    def __init__(self, **data):
        # Handle backward compatibility
        if "expected_delivery_date" in data and "purchase_date" not in data:
            data["purchase_date"] = data["expected_delivery_date"]
        super().__init__(**data)


# Placeholder schemas for deprecated endpoints
# These are only used by deprecated endpoints that return HTTP 410


class GoodsReceiptRequest(BaseModel):
    """
    DEPRECATED: Placeholder schema for deprecated goods receipt endpoint.
    This endpoint returns HTTP 410 Gone.
    """

    pass


class PurchaseOrderApprovalRequest(BaseModel):
    """
    DEPRECATED: Placeholder schema for deprecated purchase order approval endpoint.
    This endpoint returns HTTP 410 Gone.
    """

    pass
