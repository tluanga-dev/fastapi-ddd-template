## Enhanced Rental Return Management

The system now supports complex return scenarios with the following capabilities:

### 1. Partial Returns
Customers can return items in multiple transactions:
- Return some items on time, others later
- Track which items are still outstanding
- Calculate fees per item, not per transaction

### 2. Late Return Handling
- Per-item late fee calculation
- Configurable grace periods
- Manager override capabilities
- Automatic fee calculation with multipliers

### 3. Defective Item Management
- Detailed defect classification
- Customer fault determination
- Insurance claim eligibility
- Repair vs replacement decisions

### 4. Rental Renewals/Extensions
- Renew before or at expiry
- Selective item renewal for multi-item rentals
- Special renewal pricing rules
- Availability verification
- Payment before approval

### Example: Complex Return Scenario

**Rental Transaction**: Customer rents 3 items for 5 days
- Camera (INV-001) - Daily rate: ₹1000
- Lens (INV-002) - Daily rate: ₹500  
- Tripod (INV-003) - Daily rate: ₹200

**Return Scenario**:
1. **Day 5** (On time): Returns Camera and Tripod
   - Camera: Good condition
   - Tripod: Minor scratch (cosmetic damage)
   
2. **Day 7** (2 days late): Returns Lens
   - Lens: Defective (focusing mechanism broken)

**Database Records Created**:

```sql
-- First Return Transaction
INSERT INTO RENTAL_RETURN_HEADER (
    return_number, rental_transaction_id, return_date, 
    return_type, return_status, days_late,
    total_items_in_rental, items_returned_now, 
    total_items_returned, items_pending
) VALUES (
    'RET-001', 1001, '2025-01-30 17:00:00',
    'PARTIAL', 'ON_TIME', 0,
    3, 2, 2, 1
);

-- Return Lines for First Return
INSERT INTO RENTAL_RETURN_LINE (
    return_id, transaction_line_id, inventory_id,
    return_condition, days_late_item, damage_fee_item
) VALUES 
    (1, 101, 'INV-001', 'GOOD', 0, 0),
    (1, 103, 'INV-003', 'DAMAGED', 0, 200);

-- Second Return Transaction
INSERT INTO RENTAL_RETURN_HEADER (
    return_number, rental_transaction_id, return_date,
    return_type, return_status, days_late,
    total_items_in_rental, items_returned_now,
    total_items_returned, items_pending
) VALUES (
    'RET-002', 1001, '2025-02-01 17:00:00',
    'FINAL', 'LATE', 2,
    3, 1, 3, 0
);

-- Defective Item Log
INSERT INTO DEFECTIVE_ITEM_LOG (
    return_line_id, inventory_id, defect_type,
    defect_severity, customer_fault, repair_cost_estimate
) VALUES (
    201, 'INV-002', 'FUNCTIONAL', 'MAJOR', TRUE, 2000
);

-- Late Fee Calculation
INSERT INTO LATE_FEE_CALCULATION (
    return_line_id, inventory_id, days_late,
    daily_rental_rate, late_fee_multiplier, calculated_late_fee
) VALUES (
    201, 'INV-002', 2, 500, 1.5, 1500
);
```

**Financial Summary**:
- Tripod cosmetic damage: ₹200
- Lens late fee (2 days × ₹500 × 1.5): ₹1,500
- Lens repair cost: ₹2,000
- Total deductions: ₹3,700
- Deposit refund: ₹5,000 - ₹3,700 = ₹1,300

### Example: Rental Renewal Scenario

**Initial Rental**: Customer rents 3 items for 5 days starting Jan 25
- Camera (INV-001) - Daily rate: ₹1000
- Lens (INV-002) - Daily rate: ₹500
- Tripod (INV-003) - Daily rate: ₹200

**Renewal Request**: On Jan 28 (day 4), customer wants to:
- Renew Camera for 3 more days
- Return Lens and Tripod as scheduled

**Database Records**:

```sql
-- Create Renewal Request
INSERT INTO RENTAL_EXTENSION (
    transacti# Comprehensive Inventory Management System - Data Model Design

## Table of Contents
1. [Core Master Tables](#core-master-tables)
2. [User & Access Management](#user--access-management)
3. [Customer Management](#customer-management)
4. [Product & SKU Management](#product--sku-management)
5. [Inventory Management](#inventory-management)
6. [Transaction Management](#transaction-management)
7. [Pricing & Discount Management](#pricing--discount-management)
8. [Payment & Financial Management](#payment--financial-management)
9. [Rental-Specific Tables](#rental-specific-tables)
10. [Sales-Specific Tables](#sales-specific-tables)
11. [Document Management](#document-management)
12. [Inspection & Quality Control](#inspection--quality-control)
13. [Analytics & Reporting](#analytics--reporting)
14. [System Configuration](#system-configuration)
15. [Entity Relationship Summary](#entity-relationship-summary)

---

## Core Master Tables

### LOCATION
**Description**: Physical locations including stores, warehouses, and service centers
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| location_id | INT | PK, AUTO_INCREMENT | Unique location identifier |
| location_code | VARCHAR(20) | UNIQUE, NOT NULL | Business location code |
| location_name | VARCHAR(100) | NOT NULL | Location display name |
| location_type | ENUM | NOT NULL | STORE, WAREHOUSE, SERVICE_CENTER |
| address | TEXT | NOT NULL | Full address |
| city | VARCHAR(50) | NOT NULL | City name |
| state | VARCHAR(50) | NOT NULL | State/Province |
| country | VARCHAR(50) | NOT NULL | Country |
| postal_code | VARCHAR(20) | | ZIP/Postal code |
| contact_number | VARCHAR(20) | | Primary phone |
| email | VARCHAR(100) | | Location email |
| manager_user_id | INT | FK → USER | Location manager |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_date | DATETIME | NOT NULL | Creation timestamp |
| modified_date | DATETIME | | Last modification |

---

## User & Access Management

### USER
**Description**: System users including employees, managers, and administrators
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| user_id | INT | PK, AUTO_INCREMENT | Unique user identifier |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Login username |
| email | VARCHAR(100) | UNIQUE, NOT NULL | User email |
| first_name | VARCHAR(50) | NOT NULL | First name |
| last_name | VARCHAR(50) | NOT NULL | Last name |
| password_hash | VARCHAR(255) | NOT NULL | Encrypted password |
| role_id | INT | FK → ROLE | User role |
| location_id | INT | FK → LOCATION | Assigned location |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| last_login | DATETIME | | Last login timestamp |
| created_date | DATETIME | NOT NULL | Account creation |
| created_by | INT | FK → USER | Creator user |

### ROLE
**Description**: User roles defining access levels
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| role_id | INT | PK, AUTO_INCREMENT | Unique role identifier |
| role_name | VARCHAR(50) | UNIQUE, NOT NULL | Role name |
| description | TEXT | | Role description |
| is_system_role | BOOLEAN | DEFAULT FALSE | System-defined role |
| created_date | DATETIME | NOT NULL | Creation date |

### USER_ROLE_PERMISSIONS
**Description**: Permissions assigned to roles
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| permission_id | INT | PK, AUTO_INCREMENT | Unique permission ID |
| role_id | INT | FK → ROLE | Associated role |
| permission_code | VARCHAR(50) | NOT NULL | Permission code |
| permission_type | VARCHAR(50) | | SALE_CREATE, RENTAL_CREATE, etc. |
| is_granted | BOOLEAN | DEFAULT TRUE | Permission status |

---

## Customer Management

### CUSTOMER
**Description**: Customer master data for individuals and businesses
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| customer_id | INT | PK, AUTO_INCREMENT | Unique customer ID |
| customer_code | VARCHAR(20) | UNIQUE | Business customer code |
| customer_type | ENUM | NOT NULL | INDIVIDUAL, BUSINESS |
| business_name | VARCHAR(200) | | Company name (if business) |
| first_name | VARCHAR(50) | | Individual first name |
| last_name | VARCHAR(50) | | Individual last name |
| tax_id | VARCHAR(50) | | GST/Tax number |
| customer_tier | ENUM | | BRONZE, SILVER, GOLD, PLATINUM |
| credit_limit | DECIMAL(15,2) | DEFAULT 0 | Credit limit |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| blacklist_status | ENUM | DEFAULT 'CLEAR' | CLEAR, BLACKLISTED |
| created_date | DATETIME | NOT NULL | Registration date |
| last_transaction_date | DATETIME | | Last activity |
| lifetime_value | DECIMAL(15,2) | DEFAULT 0 | Total purchase value |

### CUSTOMER_CONTACT_METHOD
**Description**: Multiple contact methods (phone/email) per customer
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| contact_method_id | INT | PK, AUTO_INCREMENT | Unique contact method ID |
| customer_id | INT | FK → CUSTOMER | Parent customer |
| contact_type | ENUM | NOT NULL | MOBILE, EMAIL, PHONE, FAX |
| contact_value | VARCHAR(100) | NOT NULL | Actual phone/email |
| contact_label | VARCHAR(50) | | Personal, Work, Home, etc. |
| is_primary | BOOLEAN | DEFAULT FALSE | Primary contact flag |
| is_verified | BOOLEAN | DEFAULT FALSE | Verification status |
| verified_date | DATETIME | | Verification timestamp |
| opt_in_marketing | BOOLEAN | DEFAULT TRUE | Marketing consent |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_date | DATETIME | NOT NULL | Added date |

**Constraints**:
- UNIQUE KEY `uk_customer_contact` (customer_id, contact_type, contact_value)
- CHECK constraint: Only one primary per contact_type per customer

### CUSTOMER_CONTACT
**Description**: Additional contact persons for customers (for business customers)
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| contact_id | INT | PK, AUTO_INCREMENT | Unique contact ID |
| customer_id | INT | FK → CUSTOMER | Parent customer |
| contact_name | VARCHAR(100) | NOT NULL | Contact person name |
| designation | VARCHAR(50) | | Job title |
| department | VARCHAR(50) | | Department |
| is_primary | BOOLEAN | DEFAULT FALSE | Primary contact flag |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_date | DATETIME | NOT NULL | Added date |

### CUSTOMER_CONTACT_PERSON_METHOD
**Description**: Contact methods for customer contact persons
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| contact_person_method_id | INT | PK, AUTO_INCREMENT | Unique ID |
| contact_id | INT | FK → CUSTOMER_CONTACT | Parent contact person |
| contact_type | ENUM | NOT NULL | MOBILE, EMAIL, PHONE, FAX |
| contact_value | VARCHAR(100) | NOT NULL | Actual phone/email |
| is_primary | BOOLEAN | DEFAULT FALSE | Primary for this person |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |

### CUSTOMER_ADDRESS
**Description**: Customer addresses for billing and shipping
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| address_id | INT | PK, AUTO_INCREMENT | Unique address ID |
| customer_id | INT | FK → CUSTOMER | Parent customer |
| address_type | ENUM | NOT NULL | BILLING, SHIPPING, BOTH |
| address_line1 | VARCHAR(200) | NOT NULL | Address line 1 |
| address_line2 | VARCHAR(200) | | Address line 2 |
| city | VARCHAR(50) | NOT NULL | City |
| state | VARCHAR(50) | NOT NULL | State/Province |
| country | VARCHAR(50) | NOT NULL | Country |
| postal_code | VARCHAR(20) | | ZIP/Postal code |
| is_default | BOOLEAN | DEFAULT FALSE | Default address flag |

### CUSTOMER_CREDIT
**Description**: Customer credit and payment terms
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| credit_id | INT | PK, AUTO_INCREMENT | Unique credit ID |
| customer_id | INT | FK → CUSTOMER | Parent customer |
| credit_limit | DECIMAL(15,2) | NOT NULL | Maximum credit |
| used_credit | DECIMAL(15,2) | DEFAULT 0 | Current usage |
| payment_terms | INT | DEFAULT 0 | Days for payment |
| credit_score | INT | | Internal credit score |
| last_review_date | DATE | | Last review date |

---

## Product & SKU Management

### CATEGORY
**Description**: Product categories with unlimited hierarchy levels
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| category_id | INT | PK, AUTO_INCREMENT | Unique category ID |
| category_name | VARCHAR(100) | NOT NULL | Category name |
| parent_category_id | INT | FK → CATEGORY | Parent category (NULL for root) |
| category_path | VARCHAR(500) | | Full path (e.g., "Electronics/Computers/Laptops") |
| category_level | INT | NOT NULL | Hierarchy level (1=root, 2=sub, etc.) |
| display_order | INT | DEFAULT 0 | Sort order within parent |
| is_leaf | BOOLEAN | DEFAULT TRUE | Has no child categories |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_date | DATETIME | NOT NULL | Creation timestamp |

**Indexes**: 
- IDX_parent_category (parent_category_id)
- IDX_category_path (category_path)
- IDX_active_leaf (is_active, is_leaf)

### BRAND
**Description**: Product brands
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| brand_id | INT | PK, AUTO_INCREMENT | Unique brand ID |
| brand_name | VARCHAR(100) | UNIQUE, NOT NULL | Brand name |
| brand_code | VARCHAR(20) | UNIQUE | Brand code |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |

### ITEM_MASTER
**Description**: Master product definitions
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| item_id | INT | PK, AUTO_INCREMENT | Unique item ID |
| item_code | VARCHAR(50) | UNIQUE, NOT NULL | Item code |
| item_name | VARCHAR(200) | NOT NULL | Item name |
| category_id | INT | FK → CATEGORY | Product category |
| brand_id | INT | FK → BRAND | Product brand |
| item_type | ENUM | NOT NULL | PRODUCT, SERVICE, BUNDLE |
| is_serialized | BOOLEAN | DEFAULT FALSE | Requires serial tracking |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_date | DATETIME | NOT NULL | Creation date |

### SKU
**Description**: Stock Keeping Units - specific product variants
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| sku_id | INT | PK, AUTO_INCREMENT | Unique SKU ID |
| sku_code | VARCHAR(50) | UNIQUE, NOT NULL | SKU code |
| item_id | INT | FK → ITEM_MASTER | Parent item |
| sku_name | VARCHAR(200) | NOT NULL | SKU name |
| barcode | VARCHAR(50) | UNIQUE | Barcode/UPC |
| model_number | VARCHAR(100) | | Manufacturer model |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| is_rentable | BOOLEAN | DEFAULT FALSE | Available for rent |
| is_saleable | BOOLEAN | DEFAULT TRUE | Available for sale |
| min_rental_days | INT | DEFAULT 1 | Minimum rental period |
| max_rental_days | INT | | Maximum rental period |

### PRODUCT_ATTRIBUTES
**Description**: Product specifications and attributes
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| attribute_id | INT | PK, AUTO_INCREMENT | Unique attribute ID |
| sku_id | INT | FK → SKU | Parent SKU |
| attribute_name | VARCHAR(100) | NOT NULL | Attribute name |
| attribute_value | VARCHAR(500) | | Attribute value |
| attribute_type | VARCHAR(50) | | Type classification |
| display_order | INT | | Display sequence |

---

## Inventory Management

### INVENTORY_UNIT
**Description**: Individual inventory items (for serialized products)
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| inventory_id | VARCHAR(50) | PK | Unique inventory ID |
| sku_id | INT | FK → SKU | Product SKU |
| serial_number | VARCHAR(100) | UNIQUE | Serial number |
| location_id | INT | FK → LOCATION | Current location |
| current_status | ENUM | NOT NULL | See status values below |
| condition_grade | ENUM | | A, B, C, D |
| purchase_date | DATE | | Purchase date |
| purchase_cost | DECIMAL(15,2) | | Unit cost |
| current_customer | INT | FK → CUSTOMER | If rented/sold |
| last_inspection_date | DATE | | Last QC date |
| total_rental_days | INT | DEFAULT 0 | Lifetime rental days |
| created_date | DATETIME | NOT NULL | Entry date |

**Status Values**: AVAILABLE_SALE, AVAILABLE_RENT, RESERVED_SALE, RESERVED_RENT, RENTED, SOLD, IN_TRANSIT, INSPECTION_PENDING, CLEANING, REPAIR, DAMAGED, LOST

### STOCK_LEVEL
**Description**: Aggregate inventory levels by SKU and location
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| stock_id | INT | PK, AUTO_INCREMENT | Unique stock ID |
| sku_id | INT | FK → SKU | Product SKU |
| location_id | INT | FK → LOCATION | Stock location |
| total_quantity | INT | DEFAULT 0 | Total units |
| available_sale | INT | DEFAULT 0 | Available for sale |
| available_rent | INT | DEFAULT 0 | Available for rent |
| reserved | INT | DEFAULT 0 | Reserved units |
| in_transit | INT | DEFAULT 0 | Units in transit |
| damaged | INT | DEFAULT 0 | Damaged units |
| last_updated | DATETIME | | Last update time |

### INVENTORY_STATUS_HISTORY
**Description**: Track all inventory status changes
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| history_id | INT | PK, AUTO_INCREMENT | Unique history ID |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Inventory item |
| from_status | ENUM | | Previous status |
| to_status | ENUM | NOT NULL | New status |
| changed_by | INT | FK → USER | User making change |
| change_date | DATETIME | NOT NULL | Change timestamp |
| reason | VARCHAR(500) | | Change reason |
| transaction_id | INT | FK → TRANSACTION_HEADER | Related transaction |

### INVENTORY_HOLD
**Description**: Temporary inventory holds
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| hold_id | INT | PK, AUTO_INCREMENT | Unique hold ID |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Held item |
| hold_type | ENUM | NOT NULL | SALE, RENTAL, TRANSFER |
| hold_by | INT | FK → USER | User creating hold |
| customer_id | INT | FK → CUSTOMER | For customer |
| hold_start | DATETIME | NOT NULL | Hold start time |
| hold_expiry | DATETIME | NOT NULL | Hold expiration |
| is_active | BOOLEAN | DEFAULT TRUE | Hold status |

### RENTAL_CALENDAR
**Description**: Rental availability calendar
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| calendar_id | INT | PK, AUTO_INCREMENT | Unique calendar ID |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Inventory item |
| blocked_date | DATE | NOT NULL | Blocked date |
| transaction_id | INT | FK → TRANSACTION_HEADER | Related rental |
| block_type | ENUM | | RENTAL, MAINTENANCE, HOLD |

---

## Transaction Management

### TRANSACTION_HEADER
**Description**: Master transaction table for all transaction types
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| transaction_id | INT | PK, AUTO_INCREMENT | Unique transaction ID |
| transaction_number | VARCHAR(50) | UNIQUE, NOT NULL | Business transaction # |
| transaction_type | ENUM | NOT NULL | SALE, RENTAL, RETURN, PURCHASE |
| transaction_date | DATETIME | NOT NULL | Transaction timestamp |
| customer_id | INT | FK → CUSTOMER | Customer |
| user_id | INT | FK → USER | Transaction user |
| location_id | INT | FK → LOCATION | Transaction location |
| status | ENUM | NOT NULL | IN_PROCESS, CONFIRMED, COMPLETED, CANCELLED |
| subtotal_amount | DECIMAL(15,2) | | Before tax/discount |
| discount_amount | DECIMAL(15,2) | DEFAULT 0 | Total discount |
| tax_amount | DECIMAL(15,2) | DEFAULT 0 | Total tax |
| total_amount | DECIMAL(15,2) | NOT NULL | Final amount |
| payment_status | ENUM | | PENDING, PARTIAL, PAID |
| payment_terms | VARCHAR(50) | | Payment terms |
| notes | TEXT | | Transaction notes |
| created_date | DATETIME | NOT NULL | Creation timestamp |
| modified_date | DATETIME | | Last modification |

### TRANSACTION_LINE
**Description**: Line items for each transaction
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| line_id | INT | PK, AUTO_INCREMENT | Unique line ID |
| transaction_id | INT | FK → TRANSACTION_HEADER | Parent transaction |
| line_number | INT | NOT NULL | Line sequence |
| sku_id | INT | FK → SKU | Product SKU |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Specific unit (if serialized) |
| quantity | DECIMAL(10,2) | NOT NULL | Quantity |
| unit_price | DECIMAL(15,2) | NOT NULL | Price per unit |
| discount_percent | DECIMAL(5,2) | DEFAULT 0 | Line discount % |
| discount_amount | DECIMAL(15,2) | DEFAULT 0 | Line discount amount |
| tax_rate | DECIMAL(5,2) | DEFAULT 0 | Tax rate |
| tax_amount | DECIMAL(15,2) | DEFAULT 0 | Tax amount |
| line_total | DECIMAL(15,2) | NOT NULL | Line total |
| return_status | ENUM | | NOT_RETURNED, RETURNED, PARTIAL |
| expected_return_date | DATETIME | | For rental items |
| actual_return_date | DATETIME | | When actually returned |
| is_defective | BOOLEAN | DEFAULT FALSE | Returned defective |
| notes | TEXT | | Line notes |

### RENTAL_TRANSACTION_DETAILS
**Description**: Additional details specific to rental transactions
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| rental_detail_id | INT | PK, AUTO_INCREMENT | Unique detail ID |
| transaction_id | INT | FK → TRANSACTION_HEADER | Parent transaction |
| rental_start_date | DATETIME | NOT NULL | Rental start |
| rental_end_date | DATETIME | NOT NULL | Rental end |
| actual_return_date | DATETIME | | Final return date (all items) |
| deposit_amount | DECIMAL(15,2) | | Security deposit |
| insurance_type | ENUM | | NONE, BASIC, COMPREHENSIVE |
| insurance_amount | DECIMAL(15,2) | | Insurance fee |
| late_fee | DECIMAL(15,2) | DEFAULT 0 | Total late return fee |
| damage_fee | DECIMAL(15,2) | DEFAULT 0 | Total damage charges |
| return_status | ENUM | | PENDING, PARTIAL, COMPLETED |
| allow_partial_return | BOOLEAN | DEFAULT TRUE | Partial returns allowed |
| partial_return_count | INT | DEFAULT 0 | Number of partial returns |

---

## Pricing & Discount Management

### PRICE_LIST
**Description**: Named price lists for different customer segments
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| price_list_id | INT | PK, AUTO_INCREMENT | Unique price list ID |
| price_list_name | VARCHAR(100) | NOT NULL | Price list name |
| currency_code | VARCHAR(3) | DEFAULT 'INR' | Currency |
| is_default | BOOLEAN | DEFAULT FALSE | Default list |
| valid_from | DATE | | Effective from |
| valid_to | DATE | | Effective until |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |

### PRICE_LIST_ITEM
**Description**: SKU prices in each price list
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| price_item_id | INT | PK, AUTO_INCREMENT | Unique price item ID |
| price_list_id | INT | FK → PRICE_LIST | Parent price list |
| sku_id | INT | FK → SKU | Product SKU |
| unit_price | DECIMAL(15,2) | NOT NULL | Selling price |
| min_quantity | DECIMAL(10,2) | DEFAULT 1 | Minimum quantity |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |

### RENTAL_PRICE_MASTER
**Description**: Rental pricing by SKU
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| rental_price_id | INT | PK, AUTO_INCREMENT | Unique rental price ID |
| sku_id | INT | FK → SKU | Product SKU |
| daily_rate | DECIMAL(15,2) | NOT NULL | Per day rate |
| weekly_rate | DECIMAL(15,2) | | 7-day rate |
| monthly_rate | DECIMAL(15,2) | | 30-day rate |
| weekend_surcharge | DECIMAL(15,2) | DEFAULT 0 | Weekend extra |
| peak_season_surcharge | DECIMAL(5,2) | DEFAULT 0 | Peak season % |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |

### CUSTOMER_DISCOUNT
**Description**: Customer-specific discounts
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| discount_id | INT | PK, AUTO_INCREMENT | Unique discount ID |
| customer_id | INT | FK → CUSTOMER | Customer |
| discount_type | ENUM | | PERCENTAGE, FIXED_AMOUNT |
| discount_value | DECIMAL(15,2) | NOT NULL | Discount value |
| valid_from | DATE | | Start date |
| valid_to | DATE | | End date |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |

---

## Payment & Financial Management

### PAYMENT
**Description**: All payment transactions
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| payment_id | INT | PK, AUTO_INCREMENT | Unique payment ID |
| payment_number | VARCHAR(50) | UNIQUE | Payment reference |
| transaction_id | INT | FK → TRANSACTION_HEADER | Related transaction |
| payment_date | DATETIME | NOT NULL | Payment timestamp |
| payment_method | ENUM | NOT NULL | CASH, CARD, BANK_TRANSFER, UPI |
| amount | DECIMAL(15,2) | NOT NULL | Payment amount |
| reference_number | VARCHAR(100) | | External reference |
| payment_status | ENUM | | PENDING, VERIFIED, FAILED |
| verified_by | INT | FK → USER | Verifying user |
| notes | TEXT | | Payment notes |

### DEPOSIT_TRANSACTION
**Description**: Security deposits for rentals
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| deposit_id | INT | PK, AUTO_INCREMENT | Unique deposit ID |
| transaction_id | INT | FK → TRANSACTION_HEADER | Rental transaction |
| deposit_amount | DECIMAL(15,2) | NOT NULL | Deposit amount |
| payment_id | INT | FK → PAYMENT | Deposit payment |
| status | ENUM | | HELD, PARTIALLY_REFUNDED, FULLY_REFUNDED |
| refund_amount | DECIMAL(15,2) | | Refunded amount |
| refund_date | DATETIME | | Refund date |
| deduction_reason | TEXT | | If deducted |

### REFUND_PROCESSING
**Description**: Refund transactions
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| refund_id | INT | PK, AUTO_INCREMENT | Unique refund ID |
| original_payment_id | INT | FK → PAYMENT | Original payment |
| refund_amount | DECIMAL(15,2) | NOT NULL | Refund amount |
| refund_method | ENUM | | SAME_AS_ORIGINAL, CASH, BANK_TRANSFER |
| refund_status | ENUM | | INITIATED, PROCESSING, COMPLETED |
| initiated_date | DATETIME | NOT NULL | Initiation time |
| completed_date | DATETIME | | Completion time |
| initiated_by | INT | FK → USER | Initiating user |

---

## Rental-Specific Tables

### RENTAL_RESERVATION
**Description**: Rental bookings and reservations
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| reservation_id | INT | PK, AUTO_INCREMENT | Unique reservation ID |
| reservation_number | VARCHAR(50) | UNIQUE | Reservation code |
| customer_id | INT | FK → CUSTOMER | Customer |
| created_date | DATETIME | NOT NULL | Booking time |
| expiry_date | DATETIME | | Hold expiration |
| status | ENUM | | PENDING, CONFIRMED, CONVERTED, EXPIRED |
| converted_transaction_id | INT | FK → TRANSACTION_HEADER | If converted |

### RENTAL_AGREEMENT
**Description**: Legal rental agreements
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| agreement_id | INT | PK, AUTO_INCREMENT | Unique agreement ID |
| agreement_number | VARCHAR(50) | UNIQUE | Agreement number |
| transaction_id | INT | FK → TRANSACTION_HEADER | Rental transaction |
| agreement_date | DATETIME | NOT NULL | Agreement date |
| terms_version | VARCHAR(20) | | Terms version |
| customer_signature | TEXT | | Digital signature |
| staff_signature | TEXT | | Staff signature |
| agreement_pdf_path | VARCHAR(500) | | PDF location |

### RENTAL_EXTENSION
**Description**: Rental period extensions/renewals
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| extension_id | INT | PK, AUTO_INCREMENT | Unique extension ID |
| transaction_id | INT | FK → TRANSACTION_HEADER | Original rental |
| extension_number | VARCHAR(50) | UNIQUE | Extension reference number |
| request_date | DATETIME | NOT NULL | When extension requested |
| original_end_date | DATETIME | NOT NULL | Original due date |
| new_end_date | DATETIME | NOT NULL | Extended due date |
| extension_days | INT | NOT NULL | Additional days |
| extension_type | ENUM | NOT NULL | RENEWAL, EMERGENCY_EXTENSION, LATE_EXTENSION |
| status | ENUM | NOT NULL | REQUESTED, APPROVED, REJECTED, CANCELLED |
| additional_rental_charge | DECIMAL(15,2) | NOT NULL | Rental fee for extension |
| extension_discount | DECIMAL(15,2) | DEFAULT 0 | Any discount applied |
| tax_amount | DECIMAL(15,2) | DEFAULT 0 | Tax on extension |
| total_extension_amount | DECIMAL(15,2) | NOT NULL | Total charge for extension |
| payment_status | ENUM | | PENDING, PAID, FAILED |
| payment_id | INT | FK → PAYMENT | Extension payment |
| approved_by | INT | FK → USER | Approving user |
| rejection_reason | TEXT | | If rejected, why |
| customer_comments | TEXT | | Customer's reason for extension |
| created_date | DATETIME | NOT NULL | Record creation |
| processed_date | DATETIME | | When approved/rejected |

### RENTAL_RENEWAL_LINE
**Description**: Item-level details for rental renewals
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| renewal_line_id | INT | PK, AUTO_INCREMENT | Unique renewal line ID |
| extension_id | INT | FK → RENTAL_EXTENSION | Parent extension |
| transaction_line_id | INT | FK → TRANSACTION_LINE | Original rental line |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Specific item |
| is_renewable | BOOLEAN | DEFAULT TRUE | Can this item be renewed |
| renewal_blocked_reason | VARCHAR(200) | | Why renewal blocked |
| original_daily_rate | DECIMAL(15,2) | NOT NULL | Original rate |
| renewal_daily_rate | DECIMAL(15,2) | NOT NULL | Rate for renewal period |
| renewal_days | INT | NOT NULL | Days for this item |
| line_renewal_amount | DECIMAL(15,2) | NOT NULL | Charge for this item |
| availability_confirmed | BOOLEAN | DEFAULT FALSE | Availability checked |
| conflicting_booking_id | INT | FK → TRANSACTION_HEADER | If blocked by another booking |

### RENEWAL_AVAILABILITY_CHECK
**Description**: Tracks availability checking for renewal requests
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| check_id | INT | PK, AUTO_INCREMENT | Unique check ID |
| extension_id | INT | FK → RENTAL_EXTENSION | Extension request |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Item to check |
| check_start_date | DATETIME | NOT NULL | Period start |
| check_end_date | DATETIME | NOT NULL | Period end |
| is_available | BOOLEAN | NOT NULL | Availability result |
| blocking_transaction_id | INT | FK → TRANSACTION_HEADER | What's blocking |
| check_timestamp | DATETIME | NOT NULL | When checked |
| alternative_offered | BOOLEAN | DEFAULT FALSE | Alternative item offered |
| alternative_inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Alternative item |

### RENEWAL_PRICING_RULES
**Description**: Special pricing rules for renewals
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| rule_id | INT | PK, AUTO_INCREMENT | Unique rule ID |
| rule_name | VARCHAR(100) | NOT NULL | Rule description |
| rule_type | ENUM | NOT NULL | PERCENTAGE_DISCOUNT, FIXED_DISCOUNT, SPECIAL_RATE |
| sku_id | INT | FK → SKU | Specific SKU (null for all) |
| customer_tier | ENUM | | Specific tier (null for all) |
| min_rental_days | INT | | Minimum days to qualify |
| renewal_number | INT | | 1st renewal, 2nd, etc. |
| discount_percentage | DECIMAL(5,2) | | Percentage discount |
| fixed_discount | DECIMAL(15,2) | | Fixed amount discount |
| special_daily_rate | DECIMAL(15,2) | | Special rate |
| valid_from | DATE | | Rule start date |
| valid_to | DATE | | Rule end date |
| is_active | BOOLEAN | DEFAULT TRUE | Rule active |
| priority | INT | DEFAULT 0 | Rule priority |

### RENEWAL_HISTORY
**Description**: Complete history of all renewals for analytics
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| history_id | INT | PK, AUTO_INCREMENT | Unique history ID |
| original_transaction_id | INT | FK → TRANSACTION_HEADER | Original rental |
| customer_id | INT | FK → CUSTOMER | Customer |
| total_renewals | INT | DEFAULT 0 | Number of renewals |
| original_rental_days | INT | NOT NULL | Initial rental period |
| total_extension_days | INT | DEFAULT 0 | Total days extended |
| total_rental_days | INT | NOT NULL | Total days rented |
| original_amount | DECIMAL(15,2) | NOT NULL | Original rental fee |
| total_renewal_amount | DECIMAL(15,2) | DEFAULT 0 | Total renewal fees |
| last_renewal_date | DATETIME | | Most recent renewal |
| renewal_pattern | VARCHAR(50) | | FREQUENT, OCCASIONAL, RARE |

### RENTAL_RETURN_HEADER
**Description**: Master table for rental returns supporting partial and multiple returns
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| return_id | INT | PK, AUTO_INCREMENT | Unique return ID |
| return_number | VARCHAR(50) | UNIQUE, NOT NULL | Return reference number |
| rental_transaction_id | INT | FK → TRANSACTION_HEADER | Original rental transaction |
| return_date | DATETIME | NOT NULL | Actual return timestamp |
| return_type | ENUM | NOT NULL | FULL, PARTIAL, FINAL |
| return_status | ENUM | NOT NULL | ON_TIME, LATE, EARLY |
| days_late | INT | DEFAULT 0 | Number of days late |
| received_by | INT | FK → USER | Staff receiving return |
| customer_present | BOOLEAN | DEFAULT TRUE | Customer present during return |
| location_id | INT | FK → LOCATION | Return location |
| total_items_in_rental | INT | NOT NULL | Total items rented |
| items_returned_now | INT | NOT NULL | Items returned in this transaction |
| total_items_returned | INT | NOT NULL | Cumulative items returned |
| items_pending | INT | NOT NULL | Items still to be returned |
| notes | TEXT | | Return notes |
| created_date | DATETIME | NOT NULL | Record creation time |

### RENTAL_RETURN_LINE
**Description**: Individual item returns with condition tracking
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| return_line_id | INT | PK, AUTO_INCREMENT | Unique return line ID |
| return_id | INT | FK → RENTAL_RETURN_HEADER | Parent return transaction |
| transaction_line_id | INT | FK → TRANSACTION_LINE | Original rental line item |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Specific item returned |
| return_condition | ENUM | NOT NULL | GOOD, DAMAGED, DEFECTIVE, LOST |
| actual_return_date | DATETIME | NOT NULL | When this item was returned |
| days_late_item | INT | DEFAULT 0 | Item-specific late days |
| late_fee_item | DECIMAL(15,2) | DEFAULT 0 | Item-specific late fee |
| damage_fee_item | DECIMAL(15,2) | DEFAULT 0 | Item-specific damage fee |
| cleaning_fee_item | DECIMAL(15,2) | DEFAULT 0 | Item-specific cleaning fee |
| inspection_status | ENUM | | PENDING, COMPLETED, DISPUTED |
| inspection_id | INT | FK → POST_RENTAL_INSPECTION | Link to inspection record |
| notes | TEXT | | Item-specific notes |

### PARTIAL_RETURN_TRACKING
**Description**: Tracks the status of partial returns for a rental
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| tracking_id | INT | PK, AUTO_INCREMENT | Unique tracking ID |
| rental_transaction_id | INT | FK → TRANSACTION_HEADER | Original rental |
| total_return_transactions | INT | DEFAULT 0 | Number of return transactions |
| first_return_date | DATETIME | | Date of first partial return |
| last_return_date | DATETIME | | Date of most recent return |
| expected_final_return | DATETIME | | Expected date for remaining items |
| is_fully_returned | BOOLEAN | DEFAULT FALSE | All items returned flag |
| outstanding_fees | DECIMAL(15,2) | DEFAULT 0 | Accumulated fees |
| deposit_status | ENUM | | HELD, PARTIALLY_RELEASED, FULLY_RELEASED |
| partial_deposit_released | DECIMAL(15,2) | DEFAULT 0 | Amount released so far |

### DEFECTIVE_ITEM_LOG
**Description**: Detailed tracking of defective items returned
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| defect_id | INT | PK, AUTO_INCREMENT | Unique defect ID |
| return_line_id | INT | FK → RENTAL_RETURN_LINE | Return line reference |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Defective item |
| defect_type | ENUM | NOT NULL | COSMETIC, FUNCTIONAL, MISSING_PARTS, TOTAL_FAILURE |
| defect_severity | ENUM | NOT NULL | MINOR, MAJOR, CRITICAL |
| defect_description | TEXT | NOT NULL | Detailed description |
| reported_by_customer | BOOLEAN | DEFAULT FALSE | Customer reported the defect |
| verified_by_staff | BOOLEAN | DEFAULT FALSE | Staff verified the defect |
| repair_feasible | BOOLEAN | | Can be repaired |
| repair_cost_estimate | DECIMAL(15,2) | | Estimated repair cost |
| replacement_required | BOOLEAN | DEFAULT FALSE | Needs replacement |
| customer_fault | BOOLEAN | | Customer caused the defect |
| insurance_claim_eligible | BOOLEAN | | Covered by insurance |
| photos_count | INT | DEFAULT 0 | Number of photos taken |
| created_date | DATETIME | NOT NULL | Log entry date |

---

## Sales-Specific Tables

### SALES_COMMISSION
**Description**: Sales commission calculations
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| commission_id | INT | PK, AUTO_INCREMENT | Unique commission ID |
| transaction_id | INT | FK → TRANSACTION_HEADER | Sale transaction |
| user_id | INT | FK → USER | Salesperson |
| commission_rate | DECIMAL(5,2) | | Commission % |
| commission_amount | DECIMAL(15,2) | NOT NULL | Commission amount |
| status | ENUM | | CALCULATED, APPROVED, PAID |
| payment_date | DATE | | Payment date |

### WARRANTY_ACTIVATION
**Description**: Product warranty records
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| warranty_id | INT | PK, AUTO_INCREMENT | Unique warranty ID |
| transaction_line_id | INT | FK → TRANSACTION_LINE | Sale line item |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Product unit |
| warranty_start_date | DATE | NOT NULL | Start date |
| warranty_end_date | DATE | NOT NULL | End date |
| warranty_type | ENUM | | MANUFACTURER, EXTENDED |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |

---

## Document Management

### INVOICE
**Description**: Sales and rental invoices
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| invoice_id | INT | PK, AUTO_INCREMENT | Unique invoice ID |
| invoice_number | VARCHAR(50) | UNIQUE, NOT NULL | Invoice number |
| transaction_id | INT | FK → TRANSACTION_HEADER | Transaction |
| invoice_date | DATETIME | NOT NULL | Invoice date |
| due_date | DATE | | Payment due date |
| invoice_type | ENUM | | SALES, RENTAL, CREDIT_NOTE |
| total_amount | DECIMAL(15,2) | NOT NULL | Invoice total |
| pdf_path | VARCHAR(500) | | PDF location |
| is_sent | BOOLEAN | DEFAULT FALSE | Sent to customer |

### DELIVERY_NOTE
**Description**: Delivery/pickup documentation
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| delivery_note_id | INT | PK, AUTO_INCREMENT | Unique delivery ID |
| delivery_number | VARCHAR(50) | UNIQUE | Delivery number |
| transaction_id | INT | FK → TRANSACTION_HEADER | Transaction |
| delivery_type | ENUM | | DELIVERY, PICKUP, RETURN |
| scheduled_date | DATETIME | | Scheduled time |
| actual_date | DATETIME | | Actual time |
| delivered_by | INT | FK → USER | Delivery person |
| received_by | VARCHAR(100) | | Recipient name |
| signature_path | VARCHAR(500) | | Signature image |
| delivery_photo_path | VARCHAR(500) | | Delivery proof photo |

---

## Inspection & Quality Control

### PRE_RENTAL_INSPECTION
**Description**: Inspection before rental handover
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| inspection_id | INT | PK, AUTO_INCREMENT | Unique inspection ID |
| transaction_id | INT | FK → TRANSACTION_HEADER | Rental transaction |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Item inspected |
| inspection_date | DATETIME | NOT NULL | Inspection time |
| inspector_id | INT | FK → USER | Inspector |
| condition_grade | ENUM | | A, B, C, D |
| checklist_completed | BOOLEAN | DEFAULT FALSE | Checklist done |
| notes | TEXT | | Condition notes |
| customer_acknowledged | BOOLEAN | DEFAULT FALSE | Customer agreed |

### POST_RENTAL_INSPECTION
**Description**: Inspection after rental return
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| inspection_id | INT | PK, AUTO_INCREMENT | Unique inspection ID |
| transaction_id | INT | FK → TRANSACTION_HEADER | Rental transaction |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Item inspected |
| inspection_date | DATETIME | NOT NULL | Inspection time |
| inspector_id | INT | FK → USER | Inspector |
| condition_grade | ENUM | | A, B, C, D |
| damage_found | BOOLEAN | DEFAULT FALSE | Damage flag |
| cleaning_required | BOOLEAN | DEFAULT FALSE | Needs cleaning |
| repair_required | BOOLEAN | DEFAULT FALSE | Needs repair |

### DAMAGE_ASSESSMENT
**Description**: Damage documentation and costing
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| damage_id | INT | PK, AUTO_INCREMENT | Unique damage ID |
| inspection_id | INT | FK → POST_RENTAL_INSPECTION | Related inspection |
| damage_type | ENUM | | COSMETIC, FUNCTIONAL, TOTAL_LOSS |
| damage_description | TEXT | NOT NULL | Damage details |
| repair_cost_estimate | DECIMAL(15,2) | | Repair estimate |
| customer_liable | BOOLEAN | DEFAULT TRUE | Customer liability |
| charge_amount | DECIMAL(15,2) | | Actual charge |
| insurance_covered | BOOLEAN | DEFAULT FALSE | Insurance coverage |

### INSPECTION_PHOTOS
**Description**: Photos taken during inspections
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| photo_id | INT | PK, AUTO_INCREMENT | Unique photo ID |
| inspection_id | INT | | Related inspection |
| inspection_type | ENUM | | PRE_RENTAL, POST_RENTAL |
| photo_path | VARCHAR(500) | NOT NULL | File path |
| photo_type | VARCHAR(50) | | OVERALL, DAMAGE, SERIAL |
| upload_date | DATETIME | NOT NULL | Upload time |

### LATE_FEE_CALCULATION
**Description**: Detailed late fee calculations for rental returns
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| calculation_id | INT | PK, AUTO_INCREMENT | Unique calculation ID |
| return_line_id | INT | FK → RENTAL_RETURN_LINE | Return line reference |
| rental_transaction_id | INT | FK → TRANSACTION_HEADER | Rental transaction |
| inventory_id | VARCHAR(50) | FK → INVENTORY_UNIT | Item reference |
| expected_return_date | DATETIME | NOT NULL | Original due date |
| actual_return_date | DATETIME | NOT NULL | Actual return date |
| days_late | INT | NOT NULL | Number of days late |
| daily_rental_rate | DECIMAL(15,2) | NOT NULL | Original daily rate |
| late_fee_multiplier | DECIMAL(5,2) | DEFAULT 1.5 | Late fee multiplier (150%) |
| calculated_late_fee | DECIMAL(15,2) | NOT NULL | Total late fee |
| grace_period_applied | BOOLEAN | DEFAULT FALSE | Grace period given |
| fee_waived | BOOLEAN | DEFAULT FALSE | Fee waived by manager |
| waiver_reason | TEXT | | If waived, why |
| waived_by | INT | FK → USER | Manager who waived |
| created_date | DATETIME | NOT NULL | Calculation date |

### RETURN_REASON
**Description**: Captures reasons for returns, especially for partial returns
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| reason_id | INT | PK, AUTO_INCREMENT | Unique reason ID |
| return_id | INT | FK → RENTAL_RETURN_HEADER | Return transaction |
| return_line_id | INT | FK → RENTAL_RETURN_LINE | Specific item return |
| reason_category | ENUM | NOT NULL | COMPLETED_USE, DEFECTIVE, EARLY_COMPLETION, OTHER |
| reason_description | TEXT | | Detailed reason |
| customer_initiated | BOOLEAN | DEFAULT TRUE | Customer vs company initiated |
| affects_charges | BOOLEAN | DEFAULT FALSE | Whether reason affects fees |
| created_date | DATETIME | NOT NULL | Record creation date |

---

## Analytics & Reporting

### DAILY_SALES_SUMMARY
**Description**: Aggregated daily sales metrics
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| summary_id | INT | PK, AUTO_INCREMENT | Unique summary ID |
| summary_date | DATE | NOT NULL | Summary date |
| location_id | INT | FK → LOCATION | Location |
| total_transactions | INT | | Transaction count |
| total_revenue | DECIMAL(15,2) | | Revenue amount |
| total_units_sold | INT | | Units sold |
| total_customers | INT | | Unique customers |

### RENTAL_ANALYTICS_SUMMARY
**Description**: Rental performance metrics
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| summary_id | INT | PK, AUTO_INCREMENT | Unique summary ID |
| summary_date | DATE | NOT NULL | Summary date |
| total_rentals | INT | | Rental count |
| total_revenue | DECIMAL(15,2) | | Rental revenue |
| average_duration | DECIMAL(5,2) | | Avg rental days |
| on_time_return_rate | DECIMAL(5,2) | | % on-time returns |
| damage_rate | DECIMAL(5,2) | | % with damage |

### INVENTORY_TURNOVER
**Description**: Inventory movement analytics
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| turnover_id | INT | PK, AUTO_INCREMENT | Unique turnover ID |
| sku_id | INT | FK → SKU | Product SKU |
| period_month | DATE | NOT NULL | Month |
| units_sold | INT | | Sales quantity |
| units_rented | INT | | Rental quantity |
| turnover_ratio | DECIMAL(5,2) | | Turnover rate |
| average_days_to_sell | INT | | Avg sale time |

---

## System Configuration

### SYSTEM_PARAMETER
**Description**: System-wide configuration parameters
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| parameter_id | INT | PK, AUTO_INCREMENT | Unique parameter ID |
| parameter_name | VARCHAR(100) | UNIQUE, NOT NULL | Parameter name |
| parameter_value | VARCHAR(500) | | Parameter value |
| parameter_type | VARCHAR(50) | | STRING, NUMBER, BOOLEAN |
| description | TEXT | | Parameter description |
| is_editable | BOOLEAN | DEFAULT TRUE | Can be modified |

### NUMBER_SEQUENCE
**Description**: Auto-numbering sequences
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| sequence_id | INT | PK, AUTO_INCREMENT | Unique sequence ID |
| sequence_name | VARCHAR(50) | UNIQUE | Sequence name |
| prefix | VARCHAR(20) | | Number prefix |
| current_number | INT | NOT NULL | Current value |
| increment_by | INT | DEFAULT 1 | Increment value |
| min_digits | INT | DEFAULT 4 | Minimum digits |

### AUDIT_LOG
**Description**: System-wide audit trail
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| audit_id | BIGINT | PK, AUTO_INCREMENT | Unique audit ID |
| table_name | VARCHAR(100) | NOT NULL | Affected table |
| record_id | VARCHAR(100) | NOT NULL | Affected record |
| action | ENUM | NOT NULL | INSERT, UPDATE, DELETE |
| user_id | INT | FK → USER | User performing action |
| action_date | DATETIME | NOT NULL | Action timestamp |
| old_values | JSON | | Previous values |
| new_values | JSON | | New values |
| ip_address | VARCHAR(45) | | User IP |

### TAX_CONFIGURATION
**Description**: Tax rates and rules
| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| tax_id | INT | PK, AUTO_INCREMENT | Unique tax ID |
| tax_name | VARCHAR(50) | NOT NULL | Tax name (GST, VAT) |
| tax_rate | DECIMAL(5,2) | NOT NULL | Tax percentage |
| category_id | INT | FK → CATEGORY | Product category |
| effective_from | DATE | NOT NULL | Start date |
| effective_to | DATE | | End date |

---

## Entity Relationship Summary

### Primary Relationships

1. **Customer → Transaction**
   - One customer can have many transactions (sales, rentals)
   - Relationship: CUSTOMER.customer_id → TRANSACTION_HEADER.customer_id

2. **Customer → Contact Methods**
   - One customer can have multiple phone numbers and emails
   - Relationship: CUSTOMER.customer_id → CUSTOMER_CONTACT_METHOD.customer_id

3. **Customer → Contact Persons**
   - Business customers can have multiple contact persons
   - Relationship: CUSTOMER.customer_id → CUSTOMER_CONTACT.customer_id

4. **Contact Person → Contact Methods**
   - Each contact person can have multiple contact methods
   - Relationship: CUSTOMER_CONTACT.contact_id → CUSTOMER_CONTACT_PERSON_METHOD.contact_id

5. **Transaction → Transaction Lines**
   - One transaction has multiple line items
   - Relationship: TRANSACTION_HEADER.transaction_id → TRANSACTION_LINE.transaction_id

6. **Rental Transaction → Return Transactions**
   - One rental can have multiple return transactions (partial returns)
   - Relationship: TRANSACTION_HEADER.transaction_id → RENTAL_RETURN_HEADER.rental_transaction_id

7. **Return Header → Return Lines**
   - One return transaction has multiple item returns
   - Relationship: RENTAL_RETURN_HEADER.return_id → RENTAL_RETURN_LINE.return_id

8. **Transaction Line → Return Line**
   - Rental line items can be returned across multiple returns
   - Relationship: TRANSACTION_LINE.line_id → RENTAL_RETURN_LINE.transaction_line_id

9. **SKU → Inventory Unit**
   - One SKU can have many inventory units (for serialized items)
   - Relationship: SKU.sku_id → INVENTORY_UNIT.sku_id

10. **Transaction → Payment**
    - One transaction can have multiple payments
    - Relationship: TRANSACTION_HEADER.transaction_id → PAYMENT.transaction_id

11. **Inventory Unit → Status History**
    - One inventory unit has many status changes
    - Relationship: INVENTORY_UNIT.inventory_id → INVENTORY_STATUS_HISTORY.inventory_id

12. **User → Location**
    - Users are assigned to locations
    - Relationship: LOCATION.location_id → USER.location_id

13. **Rental Transaction → Inspections**
    - One rental has pre and post inspections
    - Relationship: TRANSACTION_HEADER.transaction_id → PRE/POST_RENTAL_INSPECTION.transaction_id

14. **Return Line → Defect Log**
    - Each returned item can have defect records
    - Relationship: RENTAL_RETURN_LINE.return_line_id → DEFECTIVE_ITEM_LOG.return_line_id

### Key Business Rules

1. **Inventory Status Flow**:
   - Sale: AVAILABLE_SALE → RESERVED_SALE → SOLD
   - Rental: AVAILABLE_RENT → RESERVED_RENT → RENTED → INSPECTION_PENDING → AVAILABLE_RENT
   - Defective Return: RENTED → INSPECTION_PENDING → REPAIR → AVAILABLE_RENT (or DAMAGED if unrepairable)

2. **Transaction Types**:
   - SALE: Direct sale transactions
   - RENTAL: Rental transactions with return cycle
   - RETURN: Rental return processing (supports partial returns)
   - PURCHASE: Inventory procurement

3. **Payment Flows**:
   - Sales: Full payment required
   - Rentals: Rental fee + refundable deposit
   - Returns: Deposit refund minus deductions
   - Partial Returns: Proportional deposit release based on returned items

4. **Inspection Requirements**:
   - Pre-rental: Mandatory before handover
   - Post-rental: Mandatory before deposit settlement
   - Defective Items: Additional inspection for damage assessment

5. **Serial Tracking**:
   - Serialized items: Individual INVENTORY_UNIT records
   - Non-serialized: Quantity tracking in STOCK_LEVEL only

6. **Partial Return Rules**:
   - Each rental can have multiple return transactions
   - Deposit released proportionally after each partial return
   - Late fees calculated per item based on individual return dates
   - Final settlement after all items returned

7. **Defective Item Handling**:
   - Items assessed for defect type and severity
   - Customer liability determined based on defect cause
   - Insurance coverage checked for major damages
   - Repair vs replacement decision tracked

8. **Late Return Penalties**:
   - Calculated per item, not per transaction
   - Standard multiplier: 150% of daily rate
   - Grace period can be applied
   - Manager can waive fees with reason

9. **Return Status Tracking**:
   - PENDING: Items not yet returned
   - PARTIAL: Some items returned, others pending
   - COMPLETED: All items returned and inspected

10. **Category Assignment Rules**:
    - Products can only be assigned to leaf categories (categories with no children)
    - Category paths are automatically maintained by triggers
    - Categories cannot be deleted if products are assigned
    - Moving a category updates all child category paths

This data model supports a comprehensive inventory management system handling both sales and rental operations with complete traceability, financial management, and customer relationship tracking.