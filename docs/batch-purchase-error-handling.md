# Batch Purchase Error Handling and Rollback Strategy

## Overview

The batch purchase feature requires sophisticated error handling due to its multi-step nature involving:
1. Item Master creation
2. SKU creation  
3. Purchase transaction creation
4. Inventory record creation

## Error Categories

### 1. Validation Errors (HTTP 400)
**When:** Invalid input data before any database operations
**Response:** Structured validation errors with field-specific messages
**Rollback:** None needed (no data created)

Examples:
- Missing required fields
- Invalid data types or formats
- Business rule violations (e.g., max rental days < min rental days)
- Duplicate codes that already exist

### 2. Business Logic Errors (HTTP 400)
**When:** Valid input but violates business constraints
**Response:** Business-specific error messages
**Rollback:** Clean up any partially created entities

Examples:
- Supplier not found or not a business customer
- Category or brand references don't exist
- SKU codes already in use
- Item codes already in use

### 3. Database Constraint Errors (HTTP 409)
**When:** Database-level constraint violations
**Response:** Conflict error with suggested resolution
**Rollback:** Clean up any partially created entities

Examples:
- Unique constraint violations
- Foreign key constraint violations
- Check constraint violations

### 4. System Errors (HTTP 500)
**When:** Unexpected errors or system failures
**Response:** Generic error message (don't expose internals)
**Rollback:** Clean up any partially created entities

Examples:
- Database connection failures
- Unexpected exceptions
- Memory or resource exhaustion

## Rollback Strategy

### Soft Delete Approach
- All entities support soft deletion via `is_active` flag
- Rollback sets `is_active = False` instead of hard deletion
- Preserves audit trail and prevents constraint violations
- Allows for manual recovery if needed

### Rollback Order
Due to foreign key constraints, rollback must occur in reverse dependency order:

1. **Inventory Units** (if created)
2. **Stock Levels** (if created)
3. **Transaction Lines** (if created)
4. **Transaction Header** (if created)
5. **SKUs** (if created)
6. **Item Masters** (if created)

### Rollback Implementation
```python
async def _rollback_created_entities(
    self, 
    created_item_masters: List[UUID], 
    created_skus: List[UUID]
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
```

## Error Response Structure

### Validation Error Response
```json
{
    "error_type": "BatchPurchaseValidationError",
    "error_message": "Batch purchase validation failed: Item 1: SKU code 'LAPTOP-001' already exists",
    "failed_at_step": "validation",
    "validation_errors": [
        "Item 1: SKU code 'LAPTOP-001' already exists",
        "Item 2: Category ID does not exist"
    ],
    "suggested_actions": [
        "Check that all required fields are provided",
        "Ensure SKU codes and item codes are unique",
        "Verify that category and brand IDs exist"
    ]
}
```

### Runtime Error Response
```json
{
    "error_type": "BatchPurchaseInternalError",
    "error_message": "Failed to create SKU: Database connection lost",
    "failed_at_step": "sku_creation",
    "created_entities_rolled_back": {
        "item_masters": ["uuid1", "uuid2"],
        "skus": ["uuid3"]
    },
    "suggested_actions": [
        "Retry the request",
        "Contact support if the issue persists"
    ]
}
```

## Frontend Error Handling

### Error Display Strategy
1. **Validation Errors:** Show inline field errors immediately
2. **Business Logic Errors:** Show form-level error messages
3. **System Errors:** Show generic error with retry option
4. **Network Errors:** Show connectivity issues with retry

### Recovery Actions
1. **Auto-retry:** For transient system errors (max 3 attempts)
2. **Manual Retry:** For user-correctable errors
3. **Draft Save:** Auto-save form state for recovery
4. **Error Logging:** Log errors for debugging and monitoring

## Monitoring and Alerting

### Error Metrics
- Track error rates by error type
- Monitor rollback frequency
- Alert on high error rates
- Track performance of rollback operations

### Logging Strategy
```python
# Log validation errors for analytics
logger.info("Batch purchase validation failed", extra={
    "supplier_id": supplier_id,
    "error_count": len(validation_errors),
    "errors": validation_errors
})

# Log rollback operations
logger.warning("Batch purchase rollback performed", extra={
    "transaction_attempt_id": attempt_id,
    "rolled_back_items": len(created_item_masters),
    "rolled_back_skus": len(created_skus),
    "original_error": str(original_error)
})
```

## Best Practices

### 1. Fail Fast
- Validate everything upfront before creating any entities
- Use the validation endpoint for preview/checking
- Don't start creating entities until all validation passes

### 2. Atomic Operations
- Use database transactions where possible
- Implement compensating transactions for cross-service operations
- Track all created entities for rollback

### 3. User Experience
- Provide clear, actionable error messages
- Show progress during long operations
- Allow users to save drafts and resume later
- Implement optimistic locking for concurrent edits

### 4. Error Recovery
- Log enough detail for debugging
- Provide self-service recovery options
- Implement circuit breakers for external dependencies
- Use retry with exponential backoff for transient errors

## Testing Strategy

### Error Scenario Testing
1. **Validation Errors:** Test each validation rule
2. **Constraint Violations:** Test database constraints
3. **Partial Failures:** Test rollback at each step
4. **Network Failures:** Test timeout and retry logic
5. **Race Conditions:** Test concurrent access scenarios

### Load Testing
- Test error handling under high load
- Verify rollback performance doesn't degrade
- Test error reporting system capacity
- Monitor memory usage during rollback operations