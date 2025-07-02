# Rental Management System - API Documentation for Frontend Developers

## Table of Contents
1. [Overview](#overview)
2. [Authentication & Headers](#authentication--headers)
3. [Base URL & Versioning](#base-url--versioning)
4. [Common Response Formats](#common-response-formats)
5. [API Endpoints](#api-endpoints)
   - [User Management](#user-management)
   - [Customer Management](#customer-management)
   - [Location Management](#location-management)
   - [Product Catalog](#product-catalog)
   - [Inventory Management](#inventory-management)
   - [Rental Transactions](#rental-transactions)
   - [Sales Transactions](#sales-transactions)
   - [Rental Returns](#rental-returns)
6. [Business Workflows](#business-workflows)
7. [Error Handling](#error-handling)
8. [Pagination & Filtering](#pagination--filtering)

## Overview

This API powers a comprehensive rental and inventory management system supporting:
- Multi-location inventory tracking
- Rental operations with partial returns
- Sales transactions
- Customer management with tiers and credit limits
- Serial number tracking for high-value items
- Damage assessment and late fee calculations

## Authentication & Headers

```http
Headers:
Content-Type: application/json
Accept: application/json
Authorization: Bearer {jwt_token}  // When authentication is implemented
```

## Base URL & Versioning

```
Base URL: http://localhost:8000/api/v1
```

All endpoints are prefixed with `/api/v1` for versioning.

## Common Response Formats

### Success Response
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "is_active": true,
  "created_by": "user_id",
  "updated_by": "user_id"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Paginated Response
```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 10
}
```

## API Endpoints

### User Management

#### Create User
```http
POST /users
```
**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "securepassword123",  // Min 8 characters
  "is_superuser": false
}
```
**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "is_superuser": false,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Get User by ID
```http
GET /users/{user_id}
```
**Response:** `200 OK` - Returns user object

#### List Users
```http
GET /users?skip=0&limit=10
```
**Response:** `200 OK` - Returns paginated list

#### Update User
```http
PATCH /users/{user_id}
```
**Request Body:** Any fields to update (email, name, password, is_superuser)

#### Delete User (Soft Delete)
```http
DELETE /users/{user_id}
```
**Response:** `204 No Content`

### Customer Management

#### Create Customer
```http
POST /customers
```
**Request Body:**
```json
{
  "customer_code": "CUST001",  // Unique, 1-20 chars
  "customer_type": "INDIVIDUAL",  // INDIVIDUAL or BUSINESS
  "first_name": "John",
  "last_name": "Doe",
  "business_name": null,  // Required if customer_type is BUSINESS
  "tax_id": "123456789",
  "customer_tier": "BRONZE",  // BRONZE, SILVER, GOLD, PLATINUM
  "credit_limit": 5000.00  // For business customers
}
```
**Response:** `201 Created` - Returns customer object with display_name

#### Get Customer
```http
GET /customers/{customer_id}
GET /customers/code/{customer_code}
```

#### List Customers
```http
GET /customers?skip=0&limit=10&customer_type=INDIVIDUAL&customer_tier=GOLD&is_blacklisted=false
```
**Query Parameters:**
- `skip`: Offset for pagination
- `limit`: Number of results
- `customer_type`: Filter by type
- `customer_tier`: Filter by tier
- `is_blacklisted`: Filter blacklisted customers

#### Blacklist/Unblacklist Customer
```http
POST /customers/{customer_id}/blacklist
```
**Request Body:**
```json
{
  "action": "blacklist",  // or "unblacklist"
  "reason": "Repeated payment defaults"
}
```

#### Update Credit Limit
```http
PUT /customers/{customer_id}/credit-limit
```
**Request Body:**
```json
{
  "credit_limit": 10000.00,
  "reason": "Good payment history"
}
```

#### Update Customer Tier
```http
PUT /customers/{customer_id}/tier
```
**Request Body:**
```json
{
  "customer_tier": "GOLD",
  "reason": "High lifetime value"
}
```

### Location Management

#### Create Location
```http
POST /locations
```
**Request Body:**
```json
{
  "location_code": "LOC001",
  "location_name": "Downtown Store",
  "location_type": "STORE",  // STORE, WAREHOUSE, SERVICE_CENTER
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "postal_code": "10001",
  "contact_number": "+1234567890",
  "email": "downtown@example.com",
  "manager_user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Get Location
```http
GET /locations/{location_id}
GET /locations/code/{location_code}
```

#### List Locations
```http
GET /locations?location_type=STORE&is_active=true
```

#### Assign/Remove Manager
```http
POST /locations/{location_id}/assign-manager
POST /locations/{location_id}/remove-manager
```
**Request Body:**
```json
{
  "manager_user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Product Catalog

#### Categories

##### Create Category
```http
POST /categories
```
**Request Body:**
```json
{
  "category_name": "Laptops",
  "parent_category_id": "550e8400-e29b-41d4-a716-446655440000",  // Optional
  "display_order": 1
}
```

##### Get Category Tree
```http
GET /categories/tree
```
**Response:** Hierarchical tree structure with children

##### Get Category by Path
```http
GET /categories/path/Electronics/Computers/Laptops
```

##### Get Category Breadcrumb
```http
GET /categories/{category_id}/breadcrumb
```
**Response:** Array of categories from root to current

#### Brands

##### Create Brand
```http
POST /brands
```
**Request Body:**
```json
{
  "brand_name": "Apple",
  "brand_code": "APPLE",  // Alphanumeric with hyphens/underscores
  "description": "Premium electronics manufacturer"
}
```

##### Search Brands
```http
GET /brands?search=apple
GET /brands/by-name/{brand_name}
GET /brands/by-code/{brand_code}
```

#### Item Masters

##### Create Item Master
```http
POST /item-masters
```
**Request Body:**
```json
{
  "item_code": "ITEM001",
  "item_name": "MacBook Pro 16\"",
  "category_id": "550e8400-e29b-41d4-a716-446655440000",
  "brand_id": "550e8400-e29b-41d4-a716-446655440000",
  "item_type": "LAPTOP",
  "description": "High-performance laptop",
  "is_serialized": true
}
```

##### Get Items by Category/Brand
```http
GET /item-masters/category/{category_id}/items
GET /item-masters/brand/{brand_id}/items
```

#### SKUs (Stock Keeping Units)

##### Create SKU
```http
POST /skus
```
**Request Body:**
```json
{
  "sku_code": "MBP16-2023-512GB",
  "sku_name": "MacBook Pro 16\" 2023 512GB",
  "item_id": "550e8400-e29b-41d4-a716-446655440000",
  "barcode": "1234567890123",
  "model_number": "A2991",
  "weight": 2.1,
  "dimensions": {
    "length": 35.57,
    "width": 24.81,
    "height": 1.68,
    "unit": "cm"
  },
  "is_rentable": true,
  "rental_base_price": 150.00,
  "min_rental_days": 1,
  "max_rental_days": 365,
  "is_saleable": true,
  "sale_base_price": 2499.00
}
```

##### Configure Rental Settings
```http
PUT /skus/{sku_id}/rental
```
**Request Body:**
```json
{
  "is_rentable": true,
  "rental_base_price": 175.00,
  "min_rental_days": 3,
  "max_rental_days": 180
}
```

##### Get Rentable/Saleable SKUs
```http
GET /skus/rentable
GET /skus/saleable
```

### Inventory Management

#### Inventory Units

##### Create Inventory Unit
```http
POST /inventory/units
```
**Request Body:**
```json
{
  "inventory_code": "INV001",
  "sku_id": "550e8400-e29b-41d4-a716-446655440000",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "serial_number": "C02X1234567",  // Required if SKU is serialized
  "status": "AVAILABLE_RENT",
  "condition_grade": "A",  // A, B, C, D
  "purchase_cost": 2000.00,
  "purchase_date": "2024-01-01",
  "warranty_expiry": "2025-01-01"
}
```

##### Update Inventory Status
```http
PUT /inventory/units/{unit_id}/status
```
**Request Body:**
```json
{
  "new_status": "MAINTENANCE_REQUIRED",
  "reason": "Customer reported malfunction"
}
```
**Valid Status Transitions:**
- Sales flow: `AVAILABLE_SALE` → `RESERVED_SALE` → `SOLD`
- Rental flow: `AVAILABLE_RENT` → `RESERVED_RENT` → `RENTED` → `INSPECTION_PENDING` → `CLEANING_REQUIRED`/`MAINTENANCE_REQUIRED` → `AVAILABLE_RENT`

##### Perform Inspection
```http
POST /inventory/units/{unit_id}/inspect
```
**Request Body:**
```json
{
  "condition_grade": "B",
  "inspection_notes": "Minor scratches on surface",
  "passed_inspection": true,
  "photos": ["photo1.jpg", "photo2.jpg"]
}
```

##### Transfer Inventory
```http
POST /inventory/units/{unit_id}/transfer
```
**Request Body:**
```json
{
  "to_location_id": "550e8400-e29b-41d4-a716-446655440000",
  "transfer_reason": "Stock balancing"
}
```

#### Stock Levels

##### Check Availability
```http
POST /inventory/availability/check
```
**Request Body:**
```json
{
  "sku_id": "550e8400-e29b-41d4-a716-446655440000",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "quantity": 5,
  "start_date": "2024-02-01",  // For rentals
  "end_date": "2024-02-07"     // For rentals
}
```
**Response:**
```json
{
  "is_available": true,
  "available_quantity": 8,
  "available_units": [
    {
      "unit_id": "550e8400-e29b-41d4-a716-446655440000",
      "serial_number": "C02X1234567",
      "condition_grade": "A"
    }
  ]
}
```

##### Get Low Stock Alerts
```http
GET /inventory/stock-levels/low-stock/alerts
```
**Response:** List of SKUs below reorder point

### Rental Transactions

#### Create Rental Booking
```http
POST /rental-transactions/bookings
```
**Request Body:**
```json
{
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "rental_start_date": "2024-02-01",
  "rental_end_date": "2024-02-07",
  "items": [
    {
      "sku_id": "550e8400-e29b-41d4-a716-446655440000",
      "quantity": 2,
      "unit_price": 150.00,
      "discount_percentage": 10.0
    }
  ],
  "deposit_percentage": 30.0,
  "tax_rate": 8.0,
  "special_instructions": "Handle with care"
}
```
**Response:** `201 Created`
```json
{
  "transaction": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "transaction_number": "RNT-20240201-0001",
    "status": "DRAFT",
    "total_amount": 324.00,
    "deposit_amount": 97.20,
    "balance_due": 324.00
  },
  "booking_summary": {
    "rental_days": 7,
    "items_count": 2,
    "subtotal": 270.00,
    "tax_amount": 21.60,
    "deposit_required": 97.20
  }
}
```

#### Process Checkout
```http
POST /rental-transactions/{transaction_id}/checkout
```
**Request Body:**
```json
{
  "payment_amount": 97.20,  // Deposit only or full amount
  "payment_method": "CREDIT_CARD",
  "payment_reference": "ch_1234567890"
}
```
**Flow:** Updates status to `CONFIRMED`, reserves inventory

#### Process Pickup
```http
POST /rental-transactions/{transaction_id}/pickup
```
**Request Body:**
```json
{
  "pickup_date": "2024-02-01T10:00:00Z",
  "picked_up_by": "John Doe",
  "pickup_items": [
    {
      "transaction_line_id": "550e8400-e29b-41d4-a716-446655440000",
      "serial_number": "C02X1234567",
      "condition_notes": "Perfect condition",
      "photos": ["pre-rental-photo1.jpg"]
    }
  ]
}
```
**Flow:** Creates pre-rental inspection, updates inventory to `RENTED`

#### Complete Return
```http
POST /rental-transactions/{transaction_id}/return
```
**Request Body:**
```json
{
  "return_date": "2024-02-08T15:00:00Z",
  "returned_by": "John Doe",
  "return_items": [
    {
      "transaction_line_id": "550e8400-e29b-41d4-a716-446655440000",
      "quantity_returned": 2,
      "condition_assessment": {
        "condition_grade": "B",
        "damage_description": "Minor scratches",
        "cleaning_required": true,
        "photos": ["return-photo1.jpg"]
      }
    }
  ],
  "late_fee_waived": false,
  "damage_fee": 50.00,
  "cleaning_fee": 25.00,
  "refund_method": "ORIGINAL_PAYMENT"
}
```
**Flow:** Calculates fees, processes deposit release, updates inventory status

#### Extend Rental Period
```http
POST /rental-transactions/{transaction_id}/extend
```
**Request Body:**
```json
{
  "new_end_date": "2024-02-14",
  "extension_reason": "Customer needs more time",
  "payment_amount": 150.00,
  "payment_method": "CREDIT_CARD",
  "payment_reference": "ch_0987654321"
}
```

### Sales Transactions

#### Create Sale
```http
POST /transactions/sales
```
**Request Body:**
```json
{
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "sku_id": "550e8400-e29b-41d4-a716-446655440000",
      "quantity": 1,
      "unit_price": 2499.00,
      "discount_percentage": 5.0
    }
  ],
  "tax_rate": 8.0,
  "auto_reserve_inventory": true
}
```
**Response:** Transaction with status `PENDING` if auto-reserved

#### Process Payment
```http
POST /transactions/{transaction_id}/payment
```
**Request Body:**
```json
{
  "payment_amount": 2499.00,
  "payment_method": "CREDIT_CARD",
  "payment_reference": "ch_1234567890"
}
```
**Flow:** Updates status to `COMPLETED`, marks inventory as `SOLD`

### Rental Returns

#### Initiate Return
```http
POST /rental-returns
```
**Request Body:**
```json
{
  "rental_transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "return_date": "2024-02-08T15:00:00Z",
  "return_items": [
    {
      "transaction_line_id": "550e8400-e29b-41d4-a716-446655440000",
      "quantity_returned": 1  // Partial return supported
    }
  ]
}
```

#### Process Partial Return
```http
POST /rental-returns/{return_id}/process-partial
```
**Request Body:**
```json
{
  "line_updates": [
    {
      "return_line_id": "550e8400-e29b-41d4-a716-446655440000",
      "quantity_returned": 1,
      "condition_grade": "B",
      "damage_notes": "Minor wear"
    }
  ]
}
```
**Flow:** Updates return quantities, maintains outstanding items

#### Calculate Late Fees
```http
POST /rental-returns/{return_id}/calculate-late-fee
```
**Response:**
```json
{
  "days_late": 1,
  "total_late_fee": 30.00,
  "fee_breakdown": [
    {
      "sku_name": "MacBook Pro 16\"",
      "quantity": 2,
      "daily_rate": 15.00,
      "days_late": 1,
      "total_fee": 30.00
    }
  ]
}
```

#### Assess Damage
```http
POST /rental-returns/{return_id}/assess-damage
```
**Request Body:**
```json
{
  "inspector_id": "550e8400-e29b-41d4-a716-446655440000",
  "damage_assessments": [
    {
      "return_line_id": "550e8400-e29b-41d4-a716-446655440000",
      "finding_type": "DAMAGE",  // DAMAGE, MISSING_PARTS, WEAR_TEAR
      "severity": "MINOR",       // MINOR, MAJOR, TOTAL_LOSS
      "description": "Screen has minor scratches",
      "liability_percentage": 50,
      "estimated_cost": 200.00,
      "photos": ["damage1.jpg", "damage2.jpg"]
    }
  ]
}
```

#### Finalize Return
```http
POST /rental-returns/{return_id}/finalize
```
**Request Body:**
```json
{
  "finalized_by": "550e8400-e29b-41d4-a716-446655440000",
  "force_finalize": false  // Skip validation checks if true
}
```
**Flow:** Completes return, calculates final fees, updates transaction

#### Release Deposit
```http
POST /rental-returns/{return_id}/release-deposit
```
**Request Body:**
```json
{
  "processed_by": "550e8400-e29b-41d4-a716-446655440000",
  "override_amount": null  // Optional override
}
```
**Response:**
```json
{
  "original_deposit": 97.20,
  "total_deductions": 75.00,
  "amount_to_release": 22.20,
  "deduction_breakdown": {
    "late_fees": 30.00,
    "damage_fees": 50.00,
    "cleaning_fees": 25.00
  }
}
```

## Business Workflows

### Complete Rental Flow

1. **Check Availability**
   ```http
   POST /inventory/availability/check
   ```

2. **Create Booking**
   ```http
   POST /rental-transactions/bookings
   ```

3. **Process Payment (Deposit)**
   ```http
   POST /rental-transactions/{id}/checkout
   ```

4. **Customer Pickup**
   ```http
   POST /rental-transactions/{id}/pickup
   ```

5. **Customer Return**
   ```http
   POST /rental-returns
   ```

6. **Inspect Items**
   ```http
   POST /rental-returns/{id}/assess-damage
   ```

7. **Calculate Fees**
   ```http
   POST /rental-returns/{id}/calculate-late-fee
   ```

8. **Finalize Return**
   ```http
   POST /rental-returns/{id}/finalize
   ```

9. **Release Deposit**
   ```http
   POST /rental-returns/{id}/release-deposit
   ```

### Partial Return Flow

1. **Initial Return (Partial)**
   ```http
   POST /rental-returns
   ```
   - Return only some items

2. **Process First Batch**
   ```http
   POST /rental-returns/{id}/process-partial
   ```

3. **Later Return (Remaining Items)**
   ```http
   POST /rental-returns/{id}/process-partial
   ```
   - Return remaining items

4. **Finalize When Complete**
   ```http
   POST /rental-returns/{id}/finalize
   ```

## Error Handling

### HTTP Status Codes
- `200 OK`: Successful GET, PUT
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `409 Conflict`: Business rule violation
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Common Error Responses

**Validation Error (422)**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Business Rule Violation (400)**
```json
{
  "detail": "Cannot rent item for less than minimum rental period of 3 days"
}
```

**Not Found (404)**
```json
{
  "detail": "Customer with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

## Pagination & Filtering

### Pagination Parameters
All list endpoints support:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 10, max: 100)

### Common Filters
- `is_active`: Filter active/inactive records
- `created_after`: Filter by creation date
- `created_before`: Filter by creation date
- `search`: Text search (where applicable)

### Example
```http
GET /customers?skip=20&limit=10&customer_type=BUSINESS&is_active=true&search=tech
```

## Best Practices

1. **Always check availability** before creating rentals
2. **Use transaction pattern** for multi-step operations
3. **Handle partial returns** - don't assume all items return together
4. **Validate business rules** on frontend to improve UX
5. **Use proper status transitions** - follow the defined flow
6. **Include photos** for inspections and damage assessment
7. **Cache reference data** (categories, brands, locations)
8. **Implement retry logic** for payment operations
9. **Show loading states** during long operations
10. **Display meaningful errors** based on API responses

## Additional Resources

- OpenAPI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`
- WebSocket support: Coming soon for real-time inventory updates