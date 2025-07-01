# Business Rules Document
## Comprehensive Inventory Management System

**Version**: 1.0  
**Date**: January 2025  
**Document Type**: Business Rules Documentation

---

## Partial Return Rules

### PRR-001: Multiple Return Transactions
- **Type**: Mandatory
- **Priority**: High
- **Description**: A single rental can have multiple return transactions
- **Conditions**: Customer returns items separately
- **Actions**: 
  - Create new RENTAL_RETURN_HEADER for each return
  - Link to original rental transaction
  - Update running totals

### PRR-002: Item-Level Tracking
- **Type**: Mandatory
- **Priority**: High
- **Description**: Each item tracked individually through returns
- **Conditions**: Partial return processing
- **Actions**: 
  - Update TRANSACTION_LINE return_status
  - Track in RENTAL_RETURN_LINE
  - Maintain item history

### PRR-003: Deposit Calculation Logic
- **Type**: Configurable
- **Priority**: High
- **Description**: Deposit released based on returned items and condition
- **Conditions**: Partial return with acceptable items
- **Actions**: 
  - Calculate item percentage (returned/total)
  - Deduct any damages or fees
  - Release proportional amount
  - Hold remainder for pending items

### PRR-004: Outstanding Item Tracking
- **Type**: Mandatory
- **Priority**: High
- **Description**: System tracks which items are still pending return
- **Conditions**: After partial return
- **Actions**: 
  - Update items_pending count
  - Send reminders for outstanding items
  - Show pending items in customer portal

### PRR-005: Mixed Condition Returns
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Handle returns with items in different conditions
- **Conditions**: Multiple items with varying conditions
- **Actions**: 
  - Process each item individually
  - Good condition: Normal processing
  - Damaged: Route to inspection
  - Defective: Create defect log

### PRR-006: Cumulative Fee Tracking
- **Type**: Mandatory
- **Priority**: High
- **Description**: Track all fees across multiple returns
- **Conditions**: Multiple return transactions
- **Actions**: 
  - Accumulate late fees
  - Sum damage charges
  - Track in PARTIAL_RETURN_TRACKING
  - Show total in final settlement

### PRR-007: Final Return Validation
- **Type**: Mandatory
- **Priority**: High
- **Description**: Validate all items returned before closing rental
- **Conditions**: Customer claims all items returned
- **Actions**: 
  - Verify items_pending = 0
  - Check all line items status
  - Mark return_type as 'FINAL'
  - Process final settlement

### PRR-008: Grace Period Application
- **Type**: Configurable
- **Priority**: Low
- **Description**: Grace period applied per item, not per return
- **Conditions**: Item returned within grace period
- **Actions**: 
  - Check item-specific return time
  - Apply grace period rules
  - Waive late fee if within grace

### PRR-009: Return Reason Tracking
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Capture reason for each return, especially partial returns
- **Conditions**: Any return transaction
- **Actions**: 
  - Record reason category
  - Capture detailed description
  - Determine if reason affects charges
  - Use for analytics and improvements

---

## Table of Contents
1. [Document Overview](#document-overview)
2. [User Access & Authentication Rules](#user-access--authentication-rules)
3. [Customer Management Rules](#customer-management-rules)
4. [Product & Category Rules](#product--category-rules)
5. [Inventory Management Rules](#inventory-management-rules)
6. [Sales Transaction Rules](#sales-transaction-rules)
7. [Rental Transaction Rules](#rental-transaction-rules)
8. [Return Processing Rules](#return-processing-rules)
9. [Partial Return Rules](#partial-return-rules)
10. [Pricing & Discount Rules](#pricing--discount-rules)
11. [Payment & Financial Rules](#payment--financial-rules)
12. [Document Generation Rules](#document-generation-rules)
13. [Inspection & Quality Control Rules](#inspection--quality-control-rules)
14. [Commission & Incentive Rules](#commission--incentive-rules)
15. [Notification & Communication Rules](#notification--communication-rules)
16. [Compliance & Audit Rules](#compliance--audit-rules)
17. [System Configuration Rules](#system-configuration-rules)

---

## Document Overview

This document defines all business rules governing the Inventory Management System. Each rule is uniquely identified and categorized by its domain area. Rules are marked as either **Mandatory** (must be enforced by the system) or **Configurable** (can be adjusted based on business needs).

### Rule Format
- **Rule ID**: Unique identifier (e.g., UAR-001)
- **Type**: Mandatory/Configurable
- **Priority**: High/Medium/Low
- **Description**: Clear statement of the rule
- **Conditions**: When the rule applies
- **Actions**: What happens when rule is triggered

---

## User Access & Authentication Rules

### UAR-001: User Authentication Required
- **Type**: Mandatory
- **Priority**: High
- **Description**: All system access requires valid user authentication
- **Conditions**: Any system access attempt
- **Actions**: 
  - Verify username and password
  - Check account active status
  - Log authentication attempt

### UAR-002: Role-Based Permissions
- **Type**: Mandatory
- **Priority**: High
- **Description**: Users can only perform actions allowed by their assigned role
- **Conditions**: User attempts any system action
- **Actions**: 
  - Check user role permissions
  - Allow/deny based on permission matrix
  - Log permission checks

### UAR-003: Location-Based Access
- **Type**: Mandatory
- **Priority**: High
- **Description**: Users can only access data for their assigned location(s)
- **Conditions**: User accesses location-specific data
- **Actions**: 
  - Verify user location assignment
  - Filter data by allowed locations
  - Restrict cross-location operations

### UAR-004: Session Timeout
- **Type**: Configurable
- **Priority**: Medium
- **Description**: User sessions expire after 30 minutes of inactivity
- **Conditions**: No user activity detected
- **Actions**: 
  - Terminate session
  - Require re-authentication
  - Save current work state

---

## Customer Management Rules

### CMR-001: Unique Customer Identification
- **Type**: Mandatory
- **Priority**: High
- **Description**: Each customer must have at least one unique identifier
- **Conditions**: Customer creation or update
- **Actions**: 
  - Validate uniqueness of mobile/email
  - Prevent duplicate customer records
  - Generate unique customer code

### CMR-002: Multiple Contact Methods
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Customers can register multiple phone numbers and emails
- **Conditions**: Adding contact information
- **Actions**: 
  - Allow multiple entries per type
  - Designate one primary per type
  - Track verification status

### CMR-003: Customer Type Classification
- **Type**: Mandatory
- **Priority**: High
- **Description**: Customers must be classified as INDIVIDUAL or BUSINESS
- **Conditions**: Customer registration
- **Actions**: 
  - Require type selection
  - Apply type-specific validation
  - Enable relevant fields

### CMR-004: Credit Limit Management
- **Type**: Configurable
- **Priority**: High
- **Description**: Business customers can have credit limits for purchases
- **Conditions**: Business customer transactions
- **Actions**: 
  - Check available credit before sale
  - Update used credit after sale
  - Block transactions exceeding limit

### CMR-005: Customer Blacklist Check
- **Type**: Mandatory
- **Priority**: High
- **Description**: Blacklisted customers cannot make new transactions
- **Conditions**: Any transaction initiation
- **Actions**: 
  - Check blacklist status
  - Prevent new transactions if blacklisted
  - Alert staff of attempted transaction

### CMR-006: Customer Tier Benefits
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Customer tiers (Bronze/Silver/Gold/Platinum) determine benefits
- **Conditions**: Transaction processing
- **Actions**: 
  - Apply tier-specific discounts
  - Provide tier-based services
  - Track for tier upgrades

---

## Product & Category Rules

### PCR-001: Category Hierarchy
- **Type**: Mandatory
- **Priority**: High
- **Description**: Products can only be assigned to leaf categories
- **Conditions**: Product creation or category assignment
- **Actions**: 
  - Validate category is leaf node
  - Prevent assignment to parent categories
  - Update category paths automatically

### PCR-002: Self-Referencing Categories
- **Type**: Mandatory
- **Priority**: High
- **Description**: Categories support unlimited hierarchy levels through self-referencing
- **Conditions**: Category creation or modification
- **Actions**: 
  - Allow parent category assignment
  - Update is_leaf flags
  - Maintain category paths

### PCR-003: Product Serialization
- **Type**: Mandatory
- **Priority**: High
- **Description**: High-value items must have individual serial number tracking
- **Conditions**: Item marked as serialized
- **Actions**: 
  - Require unique serial numbers
  - Create individual inventory units
  - Track item-level history

### PCR-004: SKU Availability Modes
- **Type**: Mandatory
- **Priority**: High
- **Description**: SKUs must be marked as saleable, rentable, or both
- **Conditions**: SKU configuration
- **Actions**: 
  - Validate at least one mode selected
  - Enable mode-specific features
  - Control inventory allocation

### PCR-005: Rental Period Limits
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Rentable items have minimum and maximum rental periods
- **Conditions**: Rental item configuration
- **Actions**: 
  - Enforce minimum rental days
  - Prevent exceeding maximum days
  - Calculate pricing accordingly

---

## Inventory Management Rules

### IMR-001: Inventory Status Flow
- **Type**: Mandatory
- **Priority**: High
- **Description**: Inventory items must follow defined status transitions
- **Conditions**: Any status change
- **Actions**: 
  - Validate allowed transitions
  - Log status changes with reasons
  - Update related systems

### IMR-002: Sale Status Transitions
- **Type**: Mandatory
- **Priority**: High
- **Description**: Sale items follow: AVAILABLE_SALE → RESERVED_SALE → SOLD
- **Conditions**: Sales transaction processing
- **Actions**: 
  - Update status at each stage
  - Prevent backward transitions
  - Release holds on cancellation

### IMR-003: Rental Status Transitions
- **Type**: Mandatory
- **Priority**: High
- **Description**: Rental items follow: AVAILABLE_RENT → RESERVED_RENT → RENTED → INSPECTION_PENDING → CLEANING/REPAIR → AVAILABLE_RENT
- **Conditions**: Rental lifecycle events
- **Actions**: 
  - Enforce sequential transitions
  - Require inspection before availability
  - Track status duration

### IMR-004: Inventory Holds
- **Type**: Mandatory
- **Priority**: High
- **Description**: Temporary holds expire automatically after specified time
- **Conditions**: Hold creation
- **Actions**: 
  - Set expiry timestamp
  - Auto-release on expiry
  - Notify hold creator

### IMR-005: Multi-Location Stock
- **Type**: Mandatory
- **Priority**: High
- **Description**: Inventory tracked separately by location
- **Conditions**: Any inventory operation
- **Actions**: 
  - Maintain location-specific counts
  - Prevent negative stock
  - Sync across channels

### IMR-006: Serial Number Uniqueness
- **Type**: Mandatory
- **Priority**: High
- **Description**: Serial numbers must be globally unique
- **Conditions**: Serial number entry
- **Actions**: 
  - Validate uniqueness
  - Prevent duplicates
  - Link to specific SKU

### IMR-007: Condition Grade Tracking
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Inventory items graded A/B/C/D based on condition
- **Conditions**: Inspection completion
- **Actions**: 
  - Update condition grade
  - Affect rental pricing
  - Trigger maintenance if needed

---

## Sales Transaction Rules

### STR-001: Sales Permission Required
- **Type**: Mandatory
- **Priority**: High
- **Description**: Only users with SALE_CREATE permission can process sales
- **Conditions**: Sales initiation
- **Actions**: 
  - Verify user permissions
  - Enable sales functions
  - Log access attempt

### STR-002: Inventory Availability Check
- **Type**: Mandatory
- **Priority**: High
- **Description**: Items must be in AVAILABLE_SALE status to be sold
- **Conditions**: Adding items to sale
- **Actions**: 
  - Check real-time availability
  - Reserve selected items
  - Prevent overselling

### STR-003: Minimum Margin Enforcement
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Sales price must maintain minimum margin (default: 15%)
- **Conditions**: Price calculation
- **Actions**: 
  - Calculate margin
  - Alert if below minimum
  - Require manager override

### STR-004: Payment Before Delivery
- **Type**: Mandatory
- **Priority**: High
- **Description**: Full payment required before item handover
- **Conditions**: Sale completion
- **Actions**: 
  - Verify payment received
  - Block delivery if unpaid
  - Update payment status

### STR-005: Immediate Inventory Update
- **Type**: Mandatory
- **Priority**: High
- **Description**: Inventory status updated to SOLD immediately upon payment
- **Conditions**: Payment confirmation
- **Actions**: 
  - Mark items as SOLD
  - Remove from available stock
  - Update all channels

### STR-006: Invoice Generation
- **Type**: Mandatory
- **Priority**: High
- **Description**: Tax-compliant invoice generated for every sale
- **Conditions**: Sale completion
- **Actions**: 
  - Generate unique invoice number
  - Include all tax details
  - Store permanently

---

## Rental Transaction Rules

### RTR-001: Customer Eligibility
- **Type**: Mandatory
- **Priority**: High
- **Description**: Customers must pass credit check for rentals
- **Conditions**: Rental initiation
- **Actions**: 
  - Check credit score
  - Verify rental history
  - Set rental limits

### RTR-002: Availability Calendar Check
- **Type**: Mandatory
- **Priority**: High
- **Description**: Items must be available for entire requested period
- **Conditions**: Rental booking
- **Actions**: 
  - Check date conflicts
  - Include buffer time
  - Block calendar dates

### RTR-003: Minimum Rental Period
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Rentals must meet minimum duration requirements
- **Conditions**: Rental duration selection
- **Actions**: 
  - Validate against SKU minimum
  - Calculate pricing
  - Show minimum if not met

### RTR-004: Security Deposit Collection
- **Type**: Mandatory
- **Priority**: High
- **Description**: Security deposit required before rental handover
- **Conditions**: Rental confirmation
- **Actions**: 
  - Calculate deposit amount (30% value or ₹5,000 minimum)
  - Collect and hold deposit
  - Link to rental transaction

### RTR-005: Rental Agreement Signature
- **Type**: Mandatory
- **Priority**: High
- **Description**: Digital rental agreement must be signed by customer
- **Conditions**: Before item handover
- **Actions**: 
  - Generate agreement
  - Capture digital signature
  - Store permanently

### RTR-006: Pre-Rental Inspection
- **Type**: Mandatory
- **Priority**: High
- **Description**: Detailed inspection required before rental handover
- **Conditions**: Rental activation
- **Actions**: 
  - Complete inspection checklist
  - Document with photos
  - Get customer acknowledgment

### RTR-007: Buffer Time Between Rentals
- **Type**: Configurable
- **Priority**: Medium
- **Description**: 4-hour buffer required between consecutive rentals
- **Conditions**: Availability calculation
- **Actions**: 
  - Add buffer to end date
  - Block buffer period
  - Allow emergency override

### RTR-008: Extension Approval
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Rental extensions allowed if item available
- **Conditions**: Extension request
- **Actions**: 
  - Check future bookings
  - Calculate additional charges
  - Update end date

### RTR-009: Insurance Options
- **Type**: Configurable
- **Priority**: Low
- **Description**: Customers can choose insurance coverage levels
- **Conditions**: Rental booking
- **Actions**: 
  - Offer insurance tiers
  - Calculate premiums
  - Document coverage

---

## Return Processing Rules

### RPR-001: Return Window Enforcement
- **Type**: Mandatory
- **Priority**: High
- **Description**: Returns must be completed by agreed date/time
- **Conditions**: Return processing
- **Actions**: 
  - Check return timing
  - Calculate if late
  - Apply penalties if applicable

### RPR-002: Physical Verification Required
- **Type**: Mandatory
- **Priority**: High
- **Description**: All returned items must be physically verified
- **Conditions**: Return initiation
- **Actions**: 
  - Verify serial numbers
  - Check all accessories
  - Document missing items

### RPR-003: Post-Return Inspection
- **Type**: Mandatory
- **Priority**: High
- **Description**: Detailed inspection comparing pre/post condition
- **Conditions**: Item return
- **Actions**: 
  - Complete inspection checklist
  - Compare with pre-rental condition
  - Document new damage

### RPR-004: Late Return Penalties
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Late returns charged 150% of daily rate per item
- **Conditions**: Return after due date
- **Actions**: 
  - Calculate late days per item
  - Apply penalty rate individually
  - Track in LATE_FEE_CALCULATION

### RPR-005: Damage Assessment
- **Type**: Mandatory
- **Priority**: High
- **Description**: Customer liable for damage beyond normal wear
- **Conditions**: Damage found during inspection
- **Actions**: 
  - Classify damage type
  - Estimate repair cost
  - Document with photos

### RPR-006: Deposit Refund Timeline
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Deposits refunded within 3-5 business days
- **Conditions**: Return completion
- **Actions**: 
  - Calculate final charges
  - Process refund
  - Notify customer

### RPR-007: Cleaning Requirements
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Items requiring cleaning cannot be re-rented immediately
- **Conditions**: Inspection findings
- **Actions**: 
  - Route to cleaning
  - Update status
  - Schedule availability

### RPR-008: Partial Return Support
- **Type**: Mandatory
- **Priority**: High
- **Description**: Customers can return items in multiple transactions
- **Conditions**: Rental with multiple items
- **Actions**: 
  - Create RENTAL_RETURN_HEADER for each return
  - Track items returned vs pending
  - Update PARTIAL_RETURN_TRACKING

### RPR-009: Per-Item Fee Calculation
- **Type**: Mandatory
- **Priority**: High
- **Description**: Late fees and damages calculated per individual item
- **Conditions**: Partial or late returns
- **Actions**: 
  - Calculate fees for each item separately
  - Store in RENTAL_RETURN_LINE
  - Aggregate for total charges

### RPR-010: Defective Item Classification
- **Type**: Mandatory
- **Priority**: High
- **Description**: Defective items must be classified by type and severity
- **Conditions**: Item returned in defective condition
- **Actions**: 
  - Classify defect type (COSMETIC/FUNCTIONAL/MISSING_PARTS/TOTAL_FAILURE)
  - Assess severity (MINOR/MAJOR/CRITICAL)
  - Create DEFECTIVE_ITEM_LOG entry

### RPR-011: Proportional Deposit Release
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Deposit released proportionally for partial returns
- **Conditions**: Partial return with good condition items
- **Actions**: 
  - Calculate percentage of items returned
  - Assess condition of returned items
  - Release appropriate deposit portion

### RPR-012: Customer Fault Determination
- **Type**: Mandatory
- **Priority**: High
- **Description**: Determine if defect is due to customer misuse
- **Conditions**: Defective item return
- **Actions**: 
  - Inspect for misuse indicators
  - Document evidence
  - Set customer_fault flag
  - Apply charges if customer fault

### RPR-013: Insurance Claim Eligibility
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Check if damage is covered by rental insurance
- **Conditions**: Item damage with insurance coverage
- **Actions**: 
  - Verify insurance type
  - Check coverage limits
  - Mark insurance_claim_eligible
  - Process claim if eligible

### RPR-014: Final Return Completion
- **Type**: Mandatory
- **Priority**: High
- **Description**: Rental marked complete only after all items returned
- **Conditions**: Last pending item returned
- **Actions**: 
  - Update return_type to 'FINAL'
  - Calculate total fees
  - Process final deposit settlement
  - Close rental transaction

---

## Pricing & Discount Rules

### PDR-001: Multi-Tier Pricing
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Different price lists for customer segments
- **Conditions**: Price calculation
- **Actions**: 
  - Select appropriate price list
  - Apply customer-specific pricing
  - Show applicable price

### PDR-002: Rental Duration Discounts
- **Type**: Configurable
- **Priority**: Low
- **Description**: Longer rentals receive duration-based discounts
- **Conditions**: Rental pricing
- **Actions**: 
  - 5+ days: 10% discount
  - 7+ days: 15% discount
  - 30+ days: Special rates

### PDR-003: Customer Discount Limits
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Maximum discount per transaction (default: 20%)
- **Conditions**: Discount application
- **Actions**: 
  - Calculate total discount
  - Require approval if exceeded
  - Log override reasons

### PDR-004: Peak Season Surcharge
- **Type**: Configurable
- **Priority**: Low
- **Description**: Additional charges during peak seasons
- **Conditions**: Date-based pricing
- **Actions**: 
  - Check season calendar
  - Apply surcharge percentage
  - Display to customer

### PDR-005: Weekend Rental Premium
- **Type**: Configurable
- **Priority**: Low
- **Description**: Weekend days charged at premium rates
- **Conditions**: Rental includes weekends
- **Actions**: 
  - Identify weekend days
  - Add premium amount
  - Show in breakdown

---

## Payment & Financial Rules

### PFR-001: Payment Method Validation
- **Type**: Mandatory
- **Priority**: High
- **Description**: Only configured payment methods accepted
- **Conditions**: Payment processing
- **Actions**: 
  - Show allowed methods
  - Validate payment details
  - Process through gateway

### PFR-002: Payment Verification
- **Type**: Mandatory
- **Priority**: High
- **Description**: All payments must be verified before order completion
- **Conditions**: Payment receipt
- **Actions**: 
  - Confirm amount received
  - Verify reference numbers
  - Update payment status

### PFR-003: Credit Sales Approval
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Credit sales require approval and credit limit check
- **Conditions**: Credit payment selection
- **Actions**: 
  - Check customer credit limit
  - Verify payment terms
  - Create receivable entry

### PFR-004: Refund Processing
- **Type**: Mandatory
- **Priority**: High
- **Description**: Refunds processed to original payment method
- **Conditions**: Refund initiation
- **Actions**: 
  - Identify original payment
  - Process through same channel
  - Track refund status

### PFR-005: Tax Calculation
- **Type**: Mandatory
- **Priority**: High
- **Description**: Taxes calculated based on product category and location
- **Conditions**: Transaction processing
- **Actions**: 
  - Apply category tax rates
  - Consider interstate rules
  - Include in total

### PFR-006: Revenue Recognition
- **Type**: Mandatory
- **Priority**: High
- **Description**: Revenue recognized based on transaction type
- **Conditions**: Transaction completion
- **Actions**: 
  - Sales: Immediate recognition
  - Rentals: Daily accrual
  - Track for reporting

---

## Document Generation Rules

### DGR-001: Unique Document Numbers
- **Type**: Mandatory
- **Priority**: High
- **Description**: All documents have unique sequential numbers
- **Conditions**: Document generation
- **Actions**: 
  - Get next sequence number
  - Apply prefix/format
  - Ensure no duplicates

### DGR-002: Invoice Compliance
- **Type**: Mandatory
- **Priority**: High
- **Description**: Invoices must include all tax-mandated fields
- **Conditions**: Invoice generation
- **Actions**: 
  - Include GSTIN
  - Show HSN codes
  - Calculate tax breakup

### DGR-003: Digital Agreement Storage
- **Type**: Mandatory
- **Priority**: High
- **Description**: All agreements stored permanently with signatures
- **Conditions**: Agreement completion
- **Actions**: 
  - Generate PDF
  - Embed signatures
  - Archive securely

### DGR-004: Warranty Activation
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Warranty starts from sale date automatically
- **Conditions**: Product sale
- **Actions**: 
  - Record start date
  - Calculate end date
  - Generate warranty card

---

## Inspection & Quality Control Rules

### IQR-001: Inspection Checklist Completion
- **Type**: Mandatory
- **Priority**: High
- **Description**: All checklist items must be completed
- **Conditions**: Inspection process
- **Actions**: 
  - Enforce all fields
  - Require inspector signature
  - Store permanently

### IQR-002: Photo Documentation
- **Type**: Mandatory
- **Priority**: High
- **Description**: Minimum 6 photos required for rental inspections
- **Conditions**: Pre/post rental inspection
- **Actions**: 
  - Capture required angles
  - Include serial number shot
  - Link to inspection record

### IQR-003: Condition Grade Assignment
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Inspector must assign condition grade after inspection
- **Conditions**: Inspection completion
- **Actions**: 
  - Evaluate against criteria
  - Assign A/B/C/D grade
  - Affect future pricing

### IQR-004: Customer Acknowledgment
- **Type**: Mandatory
- **Priority**: High
- **Description**: Customer must acknowledge pre-rental condition
- **Conditions**: Pre-rental inspection
- **Actions**: 
  - Show inspection results
  - Capture acknowledgment
  - Store with rental

### IQR-005: Service Routing
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Items needing service cannot return to available status
- **Conditions**: Post-inspection findings
- **Actions**: 
  - Route to appropriate queue
  - Update status accordingly
  - Track service completion

---

## Commission & Incentive Rules

### CIR-001: Commission Calculation
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Sales commission calculated by product category
- **Conditions**: Sale completion
- **Actions**: 
  - Apply category rates
  - Calculate on net amount
  - Queue for payment

### CIR-002: Commission Approval
- **Type**: Configurable
- **Priority**: Low
- **Description**: Commission above threshold requires approval
- **Conditions**: High-value sales
- **Actions**: 
  - Check threshold
  - Route for approval
  - Track approval status

### CIR-003: Monthly Commission Processing
- **Type**: Configurable
- **Priority**: Low
- **Description**: Commissions processed with monthly payroll
- **Conditions**: Month end
- **Actions**: 
  - Aggregate by salesperson
  - Generate reports
  - Send to payroll

---

## Notification & Communication Rules

### NCR-001: Transaction Confirmations
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: All transactions trigger customer notifications
- **Conditions**: Transaction completion
- **Actions**: 
  - Send email invoice
  - SMS confirmation
  - WhatsApp if opted-in

### NCR-002: Rental Reminders
- **Type**: Configurable
- **Priority**: Medium
- **Description**: Automated reminders for rental returns
- **Conditions**: Rental timeline
- **Actions**: 
  - 2 days before: First reminder
  - 1 day before: Second reminder
  - Due date: Final reminder

### NCR-003: Contact Method Preferences
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Respect customer communication preferences
- **Conditions**: Sending notifications
- **Actions**: 
  - Check opt-in status
  - Use preferred channels
  - Track delivery status

### NCR-004: Marketing Consent
- **Type**: Mandatory
- **Priority**: High
- **Description**: Marketing only to consented contacts
- **Conditions**: Marketing campaigns
- **Actions**: 
  - Filter by consent
  - Honor unsubscribe
  - Track consent changes

---

## Compliance & Audit Rules

### CAR-001: Complete Audit Trail
- **Type**: Mandatory
- **Priority**: High
- **Description**: All transactions maintain complete audit trail
- **Conditions**: Any data change
- **Actions**: 
  - Log user, timestamp, changes
  - Store old and new values
  - Maintain permanently

### CAR-002: Data Retention
- **Type**: Mandatory
- **Priority**: High
- **Description**: Transaction data retained for 7 years
- **Conditions**: Data archival
- **Actions**: 
  - Archive completed transactions
  - Maintain accessibility
  - Comply with regulations

### CAR-003: User Action Logging
- **Type**: Mandatory
- **Priority**: High
- **Description**: All user actions logged with context
- **Conditions**: System usage
- **Actions**: 
  - Log action type
  - Capture IP address
  - Link to user session

### CAR-004: Financial Compliance
- **Type**: Mandatory
- **Priority**: High
- **Description**: All financial transactions comply with accounting standards
- **Conditions**: Financial operations
- **Actions**: 
  - Double-entry bookkeeping
  - Tax compliance
  - Audit readiness

---

## System Configuration Rules

### SCR-001: Parameter Validation
- **Type**: Mandatory
- **Priority**: High
- **Description**: System parameters validated before saving
- **Conditions**: Configuration changes
- **Actions**: 
  - Check data types
  - Validate ranges
  - Test dependencies

### SCR-002: Number Sequence Management
- **Type**: Mandatory
- **Priority**: High
- **Description**: Number sequences never repeat or have gaps
- **Conditions**: Sequence generation
- **Actions**: 
  - Lock during generation
  - Increment atomically
  - Handle failures gracefully

### SCR-003: Multi-Location Configuration
- **Type**: Mandatory
- **Priority**: Medium
- **Description**: Each location can have specific configurations
- **Conditions**: Location setup
- **Actions**: 
  - Allow location overrides
  - Inherit from global
  - Validate completeness

### SCR-004: Tax Configuration Updates
- **Type**: Mandatory
- **Priority**: High
- **Description**: Tax changes apply from effective date
- **Conditions**: Tax rate updates
- **Actions**: 
  - Set effective date
  - Maintain history
  - Apply to new transactions only

---

## Business Rule Enforcement

### Rule Priority Matrix

| Priority | Response Time | Override Authority | Notification |
|----------|--------------|-------------------|--------------|
| High | Immediate | System Admin Only | Alert + Block |
| Medium | Real-time | Manager Level | Warning |
| Low | Batch/Async | Supervisor Level | Log Only |

### Rule Violation Handling

1. **Blocking Rules**: Transaction cannot proceed
2. **Warning Rules**: Alert shown but can continue
3. **Audit Rules**: Logged for review
4. **Override Rules**: Requires authorization

### Rule Configuration Management

- Rules can be enabled/disabled by location
- Configurable rules allow parameter adjustment
- Rule changes require approval workflow
- All rule changes are audited

---

## Change Management

### Rule Change Process
1. Request submitted with business justification
2. Impact analysis performed
3. Testing in sandbox environment
4. Approval from stakeholders
5. Scheduled deployment
6. Post-implementation review

### Version Control
- All rule changes versioned
- Previous versions maintained
- Rollback capability available
- Change history documented

---

## Appendices

### A. Rule Categories
- **Mandatory**: System-enforced, cannot be disabled
- **Configurable**: Parameters can be adjusted
- **Location-Specific**: Can vary by location
- **Time-Based**: Apply during specific periods

### B. Integration Points
- Payment Gateway Rules
- Tax System Rules
- Accounting System Rules
- Communication Platform Rules

### C. Exception Scenarios
- System Downtime Rules
- Emergency Override Procedures
- Disaster Recovery Rules
- Data Recovery Rules

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 2025 | System Analyst | Initial version |

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Business Owner | | | |
| IT Manager | | | |
| Operations Head | | | |
| Compliance Officer | | | |