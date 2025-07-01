# Domain-Driven Design (DDD) Architecture Template

This document provides a comprehensive guide for implementing Domain-Driven Design (DDD) architecture in Python/FastAPI projects. It is based on the proven structure used in the rental-backend project and can serve as a template for new projects.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Layer Details and Implementation Guide](#layer-details-and-implementation-guide)
4. [Implementation Patterns](#implementation-patterns)
5. [Step-by-Step Implementation Guide](#step-by-step-implementation-guide)
6. [Testing Strategy](#testing-strategy)
7. [Best Practices and Conventions](#best-practices-and-conventions)
8. [Migration from Traditional Architecture](#migration-from-traditional-architecture)

## Architecture Overview

This architecture follows Clean Architecture principles with Domain-Driven Design, organizing code into four distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│              (FastAPI Routes & Schemas)                     │
├─────────────────────────────────────────────────────────────┤
│                  Application Layer                          │
│            (Use Cases & Orchestration)                      │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                             │
│         (Entities, Value Objects, Interfaces)              │
├─────────────────────────────────────────────────────────────┤
│                Infrastructure Layer                         │
│          (Database, External Services)                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles:
- **Dependency Rule**: Dependencies point inward. Domain layer has no dependencies.
- **Separation of Concerns**: Each layer has a specific responsibility.
- **Testability**: Each layer can be tested independently.
- **Framework Independence**: Core business logic is framework-agnostic.

## Project Structure

### Complete Directory Template

```
project-root/
├── src/
│   ├── main.py                          # Application entry point
│   │
│   ├── api/                             # API Layer (Presentation)
│   │   └── v1/                          # Versioned API
│   │       ├── router.py                # Main router aggregator
│   │       ├── endpoints/               # Route handlers (Controllers)
│   │       │   ├── __init__.py
│   │       │   ├── {entity_plural}.py   # e.g., customers.py
│   │       │   └── {subdomain}/         # Subdomain-specific endpoints
│   │       │       └── {entity_plural}.py
│   │       └── schemas/                 # Pydantic models (DTOs)
│   │           ├── __init__.py
│   │           ├── base_schemas.py      # Common base schemas
│   │           ├── {entity}_schemas.py  # Entity-specific schemas
│   │           └── {subdomain}/         # Subdomain-specific schemas
│   │               └── {entity}_schemas.py
│   │
│   ├── application/                     # Application Layer
│   │   ├── __init__.py
│   │   ├── services/                    # Orchestration services
│   │   │   ├── __init__.py
│   │   │   └── {entity}_service.py     # Multi-use-case orchestration
│   │   └── use_cases/                   # Business use cases
│   │       ├── __init__.py
│   │       ├── {entity}_use_cases.py    # Simple CRUD use cases
│   │       └── {subdomain}/             # Complex domain use cases
│   │           └── {action}_{entity}_use_case.py
│   │
│   ├── domain/                          # Domain Layer (Core Business)
│   │   ├── __init__.py
│   │   ├── entities/                    # Business entities
│   │   │   ├── __init__.py
│   │   │   ├── base_entity.py          # Base entity class
│   │   │   ├── {entity}.py             # Domain entities
│   │   │   └── {subdomain}/            # Subdomain entities
│   │   │       └── {entity}.py
│   │   ├── repositories/                # Repository interfaces (Ports)
│   │   │   ├── __init__.py
│   │   │   └── {entity}_repository.py  # Abstract repository
│   │   └── value_objects/               # Immutable value objects
│   │       ├── __init__.py
│   │       ├── {value_object}.py       # e.g., address.py, phone_number.py
│   │       └── {subdomain}/            # Subdomain value objects
│   │           └── {value_object}.py
│   │
│   ├── infrastructure/                  # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── database/                    # Database configuration
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # SQLAlchemy declarative base
│   │   │   ├── base_model.py           # Base model for all tables
│   │   │   └── models.py               # All ORM models
│   │   └── repositories/                # Repository implementations (Adapters)
│   │       ├── __init__.py
│   │       └── {entity}_repository_impl.py  # Concrete implementations
│   │
│   └── core/                            # Core utilities and config
│       ├── __init__.py
│       ├── config/                      # Configuration management
│       │   ├── __init__.py
│       │   ├── settings.py              # Application settings
│       │   ├── database.py              # Database connection
│       │   └── logging.py               # Logging configuration
│       ├── middleware.py                # Custom middleware
│       └── utils/                       # Utility functions
│           ├── __init__.py
│           └── {utility}.py             # e.g., id_generator.py
│
├── tests/                               # Test directory
│   ├── conftest.py                      # Shared fixtures
│   ├── unit_{layer}_{entity}.py        # Layer-specific unit tests
│   ├── integration_{entity}.py         # Integration tests
│   └── unit/                           # Additional unit tests
│       └── {layer}/
│           └── test_{component}.py
│
├── alembic/                            # Database migrations
│   ├── versions/                       # Migration files
│   ├── alembic.ini                     # Alembic configuration
│   └── env.py                          # Migration environment
│
├── docker-compose.yml                  # Docker services
├── Dockerfile                          # Container definition
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variables template
├── README.md                           # Project documentation
└── CLAUDE.md                          # AI assistant instructions
```

## Layer Details and Implementation Guide

### 1. Domain Layer (`src/domain/`)

The heart of the application containing business logic.

#### Entities (`src/domain/entities/`)

**Base Entity Template:**
```python
# base_entity.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

class BaseEntity:
    """Base class for all domain entities."""
    
    def __init__(
        self,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        updated_by: Optional[str] = None,
        is_active: bool = True
    ):
        self.id = id or uuid4()
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.created_by = created_by
        self.updated_by = updated_by
        self.is_active = is_active
    
    def update_modified(self, updated_by: Optional[str] = None):
        """Update modification timestamp and user."""
        self.updated_at = datetime.utcnow()
        if updated_by:
            self.updated_by = updated_by
```

**Entity Template:**
```python
# customer.py
from typing import Optional, List
from uuid import UUID
from .base_entity import BaseEntity
from ..value_objects.address import Address
from ..value_objects.phone_number import PhoneNumber

class Customer(BaseEntity):
    """Customer domain entity with business logic."""
    
    def __init__(
        self,
        name: str,
        email: Optional[str] = None,
        address: Optional[Address] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name
        self.email = email
        self.address = address
        self._validate()
    
    def _validate(self):
        """Validate business rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Customer name cannot be empty")
        
        if self.email and "@" not in self.email:
            raise ValueError("Invalid email format")
    
    def update_contact_info(self, email: Optional[str] = None, address: Optional[Address] = None):
        """Business method to update contact information."""
        if email:
            self.email = email
        if address:
            self.address = address
        self._validate()
        self.update_modified()
```

#### Repository Interfaces (`src/domain/repositories/`)

**Repository Interface Template:**
```python
# customer_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from ..entities.customer import Customer

class CustomerRepository(ABC):
    """Abstract repository interface for Customer entity."""
    
    @abstractmethod
    async def create(self, customer: Customer) -> Customer:
        """Create a new customer."""
        pass
    
    @abstractmethod
    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email."""
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[Customer]:
        """List customers with pagination and filters."""
        pass
    
    @abstractmethod
    async def update(self, customer: Customer) -> Customer:
        """Update existing customer."""
        pass
    
    @abstractmethod
    async def delete(self, customer_id: UUID) -> bool:
        """Soft delete customer."""
        pass
    
    @abstractmethod
    async def count(self, filters: dict = None) -> int:
        """Count customers matching filters."""
        pass
```

#### Value Objects (`src/domain/value_objects/`)

**Value Object Template:**
```python
# address.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Address:
    """Immutable address value object."""
    
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    
    def __post_init__(self):
        """Validate address data."""
        if not all([self.street, self.city, self.state, self.zip_code]):
            raise ValueError("All address fields except country are required")
        
        if len(self.zip_code) not in [5, 10]:  # US ZIP or ZIP+4
            raise ValueError("Invalid ZIP code format")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Address":
        """Create from dictionary."""
        return cls(**data)
```

### 2. Application Layer (`src/application/`)

Orchestrates domain objects to fulfill use cases.

#### Use Cases (`src/application/use_cases/`)

**Simple CRUD Use Cases Template:**
```python
# customer_use_cases.py
from typing import List, Optional
from uuid import UUID
from ...domain.entities.customer import Customer
from ...domain.repositories.customer_repository import CustomerRepository

class CustomerUseCases:
    """Customer use cases for CRUD operations."""
    
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository
    
    async def create_customer(
        self,
        name: str,
        email: Optional[str] = None,
        address_data: Optional[dict] = None,
        created_by: Optional[str] = None
    ) -> Customer:
        """Create a new customer."""
        # Create domain entity
        customer = Customer(
            name=name,
            email=email,
            address=Address.from_dict(address_data) if address_data else None,
            created_by=created_by
        )
        
        # Check business rules
        if email:
            existing = await self.customer_repository.get_by_email(email)
            if existing:
                raise ValueError(f"Customer with email {email} already exists")
        
        # Persist
        return await self.customer_repository.create(customer)
    
    async def get_customer(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID."""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")
        return customer
    
    async def list_customers(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict = None
    ) -> tuple[List[Customer], int]:
        """List customers with pagination."""
        customers = await self.customer_repository.list(skip, limit, filters)
        total = await self.customer_repository.count(filters)
        return customers, total
```

**Complex Use Case Template:**
```python
# sales/create_sales_transaction_use_case.py
from typing import List
from uuid import UUID
from ....domain.entities.sales.sales_transaction import SalesTransaction
from ....domain.repositories.sales_transaction_repository import SalesTransactionRepository
from ....domain.repositories.inventory_repository import InventoryRepository

class CreateSalesTransactionUseCase:
    """Use case for creating a sales transaction."""
    
    def __init__(
        self,
        sales_repository: SalesTransactionRepository,
        inventory_repository: InventoryRepository
    ):
        self.sales_repository = sales_repository
        self.inventory_repository = inventory_repository
    
    async def execute(
        self,
        customer_id: UUID,
        items: List[dict],
        payment_terms: str,
        created_by: str
    ) -> SalesTransaction:
        """Execute the use case."""
        # 1. Validate inventory availability
        for item in items:
            available = await self.inventory_repository.check_availability(
                item['item_id'], 
                item['quantity']
            )
            if not available:
                raise ValueError(f"Insufficient inventory for item {item['item_id']}")
        
        # 2. Create sales transaction
        transaction = SalesTransaction.create(
            customer_id=customer_id,
            payment_terms=payment_terms,
            created_by=created_by
        )
        
        # 3. Add line items
        for item in items:
            transaction.add_item(
                item_id=item['item_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price']
            )
        
        # 4. Reserve inventory
        for item in transaction.items:
            await self.inventory_repository.reserve(
                item.item_id,
                item.quantity
            )
        
        # 5. Persist transaction
        return await self.sales_repository.create(transaction)
```

#### Services (`src/application/services/`)

**Service Template:**
```python
# customer_service.py
from typing import List, Optional
from uuid import UUID
from .use_cases.customer_use_cases import CustomerUseCases
from ...domain.entities.customer import Customer

class CustomerService:
    """Service to orchestrate customer-related use cases."""
    
    def __init__(self, customer_use_cases: CustomerUseCases):
        self.use_cases = customer_use_cases
    
    async def register_customer(
        self,
        name: str,
        email: str,
        address_data: dict,
        phone_numbers: List[str],
        created_by: str
    ) -> Customer:
        """Complex customer registration with multiple steps."""
        # Create customer
        customer = await self.use_cases.create_customer(
            name=name,
            email=email,
            address_data=address_data,
            created_by=created_by
        )
        
        # Add phone numbers (if contact service exists)
        for phone in phone_numbers:
            await self.contact_service.add_phone_number(
                entity_type="Customer",
                entity_id=customer.id,
                phone_number=phone
            )
        
        # Send welcome email (if notification service exists)
        await self.notification_service.send_welcome_email(customer)
        
        return customer
```

### 3. Infrastructure Layer (`src/infrastructure/`)

Handles external concerns and implements domain interfaces.

#### Database Models (`src/infrastructure/database/`)

**Base Model Template:**
```python
# base_model.py
from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

class BaseModel:
    """Base model with common fields."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(255))
    updated_by = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
```

**ORM Model Template:**
```python
# models.py
from sqlalchemy import Column, String, JSON, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
from .base_model import BaseModel

class CustomerModel(Base, BaseModel):
    """SQLAlchemy model for Customer entity."""
    
    __tablename__ = "customers"
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    address = Column(JSON)  # Stores address value object as JSON
    
    # Relationships
    sales_transactions = relationship("SalesTransactionModel", back_populates="customer")
    
    def to_entity(self) -> Customer:
        """Convert ORM model to domain entity."""
        from ...domain.entities.customer import Customer
        from ...domain.value_objects.address import Address
        
        return Customer(
            id=self.id,
            name=self.name,
            email=self.email,
            address=Address.from_dict(self.address) if self.address else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            is_active=self.is_active
        )
    
    @classmethod
    def from_entity(cls, customer: Customer) -> "CustomerModel":
        """Create ORM model from domain entity."""
        return cls(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            address=customer.address.to_dict() if customer.address else None,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            created_by=customer.created_by,
            updated_by=customer.updated_by,
            is_active=customer.is_active
        )
```

#### Repository Implementations (`src/infrastructure/repositories/`)

**Repository Implementation Template:**
```python
# customer_repository_impl.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ...domain.entities.customer import Customer
from ...domain.repositories.customer_repository import CustomerRepository
from ..database.models import CustomerModel

class SQLAlchemyCustomerRepository(CustomerRepository):
    """SQLAlchemy implementation of CustomerRepository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, customer: Customer) -> Customer:
        """Create a new customer."""
        db_customer = CustomerModel.from_entity(customer)
        self.db.add(db_customer)
        self.db.commit()
        self.db.refresh(db_customer)
        return db_customer.to_entity()
    
    async def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Get customer by ID."""
        db_customer = self.db.query(CustomerModel).filter(
            and_(
                CustomerModel.id == customer_id,
                CustomerModel.is_active == True
            )
        ).first()
        return db_customer.to_entity() if db_customer else None
    
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email."""
        db_customer = self.db.query(CustomerModel).filter(
            and_(
                CustomerModel.email == email,
                CustomerModel.is_active == True
            )
        ).first()
        return db_customer.to_entity() if db_customer else None
    
    async def list(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[Customer]:
        """List customers with pagination and filters."""
        query = self.db.query(CustomerModel).filter(CustomerModel.is_active == True)
        
        if filters:
            if filters.get('name'):
                query = query.filter(CustomerModel.name.ilike(f"%{filters['name']}%"))
            if filters.get('email'):
                query = query.filter(CustomerModel.email.ilike(f"%{filters['email']}%"))
            if filters.get('city'):
                query = query.filter(CustomerModel.address['city'].astext == filters['city'])
        
        db_customers = query.offset(skip).limit(limit).all()
        return [db_customer.to_entity() for db_customer in db_customers]
    
    async def update(self, customer: Customer) -> Customer:
        """Update existing customer."""
        db_customer = self.db.query(CustomerModel).filter(
            CustomerModel.id == customer.id
        ).first()
        
        if not db_customer:
            raise ValueError(f"Customer with ID {customer.id} not found")
        
        # Update fields
        db_customer.name = customer.name
        db_customer.email = customer.email
        db_customer.address = customer.address.to_dict() if customer.address else None
        db_customer.updated_at = customer.updated_at
        db_customer.updated_by = customer.updated_by
        
        self.db.commit()
        self.db.refresh(db_customer)
        return db_customer.to_entity()
    
    async def delete(self, customer_id: UUID) -> bool:
        """Soft delete customer."""
        db_customer = self.db.query(CustomerModel).filter(
            CustomerModel.id == customer_id
        ).first()
        
        if not db_customer:
            return False
        
        db_customer.is_active = False
        self.db.commit()
        return True
    
    async def count(self, filters: dict = None) -> int:
        """Count customers matching filters."""
        query = self.db.query(CustomerModel).filter(CustomerModel.is_active == True)
        
        if filters:
            # Apply same filters as list method
            if filters.get('name'):
                query = query.filter(CustomerModel.name.ilike(f"%{filters['name']}%"))
            if filters.get('email'):
                query = query.filter(CustomerModel.email.ilike(f"%{filters['email']}%"))
        
        return query.count()
```

### 4. API Layer (`src/api/v1/`)

Handles HTTP requests and responses.

#### Schemas (`src/api/v1/schemas/`)

**Schema Templates:**
```python
# customer_schemas.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class AddressSchema(BaseModel):
    """Address schema matching the value object."""
    street: str
    city: str
    state: str
    zip_code: str = Field(..., pattern=r"^\d{5}(-\d{4})?$")
    country: str = "USA"

class CustomerBase(BaseModel):
    """Base customer schema."""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    address: Optional[AddressSchema] = None

class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    pass

class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    address: Optional[AddressSchema] = None

class CustomerResponse(CustomerBase):
    """Schema for customer responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    is_active: bool = True

class CustomerListResponse(BaseModel):
    """Schema for paginated customer list."""
    items: list[CustomerResponse]
    total: int
    skip: int
    limit: int
```

#### Endpoints (`src/api/v1/endpoints/`)

**Endpoint Template:**
```python
# customers.py
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from ....core.config.database import get_db_session
from ....application.use_cases.customer_use_cases import CustomerUseCases
from ....infrastructure.repositories.customer_repository_impl import SQLAlchemyCustomerRepository
from ..schemas.customer_schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse
)

router = APIRouter(prefix="/customers", tags=["customers"])

def get_customer_use_cases(db: Session = Depends(get_db_session)) -> CustomerUseCases:
    """Dependency injection for customer use cases."""
    repository = SQLAlchemyCustomerRepository(db)
    return CustomerUseCases(repository)

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    use_cases: CustomerUseCases = Depends(get_customer_use_cases),
    current_user: str = Depends(get_current_user)  # Authentication dependency
):
    """Create a new customer."""
    try:
        customer = await use_cases.create_customer(
            name=customer_data.name,
            email=customer_data.email,
            address_data=customer_data.address.model_dump() if customer_data.address else None,
            created_by=current_user
        )
        return customer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    use_cases: CustomerUseCases = Depends(get_customer_use_cases)
):
    """Get a customer by ID."""
    try:
        customer = await use_cases.get_customer(customer_id)
        return customer
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    use_cases: CustomerUseCases = Depends(get_customer_use_cases)
):
    """List customers with pagination and filters."""
    filters = {}
    if name:
        filters['name'] = name
    if email:
        filters['email'] = email
    if city:
        filters['city'] = city
    
    customers, total = await use_cases.list_customers(skip, limit, filters)
    
    return CustomerListResponse(
        items=customers,
        total=total,
        skip=skip,
        limit=limit
    )

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    use_cases: CustomerUseCases = Depends(get_customer_use_cases),
    current_user: str = Depends(get_current_user)
):
    """Update a customer."""
    try:
        customer = await use_cases.update_customer(
            customer_id=customer_id,
            name=customer_data.name,
            email=customer_data.email,
            address_data=customer_data.address.model_dump() if customer_data.address else None,
            updated_by=current_user
        )
        return customer
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    use_cases: CustomerUseCases = Depends(get_customer_use_cases)
):
    """Delete a customer (soft delete)."""
    success = await use_cases.delete_customer(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
```

**Router Aggregator:**
```python
# router.py
from fastapi import APIRouter
from .endpoints import customers, vendors, warehouses, sales_transactions

api_router = APIRouter()

api_router.include_router(customers.router)
api_router.include_router(vendors.router)
api_router.include_router(warehouses.router)
api_router.include_router(sales_transactions.router)
```

### 5. Core Utilities (`src/core/`)

**Database Configuration:**
```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from .settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # For async compatibility
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session() -> Session:
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Settings Management:**
```python
# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "DDD FastAPI Application"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Main Application:**
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.router import api_router
from .core.config.settings import settings
from .core.middleware import (
    CorrelationIdMiddleware,
    PerformanceMiddleware,
    RequestLoggingMiddleware
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}
```

## Implementation Patterns

### 1. Dependency Injection Pattern

**Manual Dependency Injection:**
```python
# In endpoints
def get_customer_use_cases(db: Session = Depends(get_db_session)) -> CustomerUseCases:
    repository = SQLAlchemyCustomerRepository(db)
    return CustomerUseCases(repository)
```

**With Service Layer:**
```python
def get_customer_service(db: Session = Depends(get_db_session)) -> CustomerService:
    repository = SQLAlchemyCustomerRepository(db)
    use_cases = CustomerUseCases(repository)
    return CustomerService(use_cases)
```

### 2. Generic Foreign Key Pattern

For flexible associations (e.g., ContactNumber can belong to any entity):

```python
# Domain entity
class ContactNumber(BaseEntity):
    def __init__(
        self,
        phone_number: PhoneNumber,
        entity_type: str,  # "Customer", "Vendor", etc.
        entity_id: UUID,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.phone_number = phone_number
        self.entity_type = entity_type
        self.entity_id = entity_id

# ORM model
class ContactNumberModel(Base, BaseModel):
    __tablename__ = "contact_numbers"
    
    phone_number = Column(String(20), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_entity_lookup', 'entity_type', 'entity_id'),
    )
```

### 3. Subdomain Organization Pattern

For complex domains, organize by subdomain:

```
domain/
├── entities/
│   └── sales/
│       ├── __init__.py
│       ├── sales_transaction.py
│       ├── sales_transaction_item.py
│       └── sales_return.py
└── value_objects/
    └── sales/
        ├── __init__.py
        ├── payment_status.py
        └── sales_status.py
```

### 4. Aggregate Pattern

When entities form aggregates:

```python
class SalesTransaction(BaseEntity):
    """Sales transaction aggregate root."""
    
    def __init__(self, customer_id: UUID, **kwargs):
        super().__init__(**kwargs)
        self.customer_id = customer_id
        self.items: List[SalesTransactionItem] = []
        self.total_amount = Decimal("0.00")
    
    def add_item(self, item_id: UUID, quantity: int, unit_price: Decimal):
        """Add item to transaction (aggregate operation)."""
        item = SalesTransactionItem(
            transaction_id=self.id,
            item_id=item_id,
            quantity=quantity,
            unit_price=unit_price
        )
        self.items.append(item)
        self._recalculate_total()
    
    def _recalculate_total(self):
        """Internal method to maintain aggregate consistency."""
        self.total_amount = sum(
            item.quantity * item.unit_price 
            for item in self.items
        )
```

## Step-by-Step Implementation Guide

### Phase 1: Project Setup

1. **Create Project Structure:**
```bash
mkdir my-ddd-project
cd my-ddd-project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install Dependencies:**
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic pydantic-settings python-dotenv
```

3. **Create Directory Structure:**
```bash
mkdir -p src/{api/v1/{endpoints,schemas},application/{services,use_cases},domain/{entities,repositories,value_objects},infrastructure/{database,repositories},core/{config,utils}}
touch src/__init__.py src/main.py
```

### Phase 2: Implement Core Components

1. **Start with Domain Layer:**
   - Create base entity
   - Define your first entity (e.g., Customer)
   - Create repository interface
   - Define value objects

2. **Build Infrastructure Layer:**
   - Set up database configuration
   - Create SQLAlchemy models
   - Implement repository

3. **Add Application Layer:**
   - Create use cases
   - Add service layer if needed

4. **Expose via API Layer:**
   - Define Pydantic schemas
   - Create endpoints
   - Set up router

### Phase 3: Database Setup

1. **Initialize Alembic:**
```bash
alembic init alembic
```

2. **Configure Alembic:**
Update `alembic.ini` and `alembic/env.py` to use your database URL.

3. **Create First Migration:**
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Phase 4: Testing Structure

Create comprehensive tests following the layer structure.

## Testing Strategy

### Test Organization

```
tests/
├── conftest.py                      # Shared fixtures
├── unit_{layer}_{entity}.py        # Layer-specific unit tests
├── integration_{entity}.py          # Integration tests
└── e2e_{feature}.py                # End-to-end tests
```

### Layer-Specific Testing

#### Domain Layer Tests
```python
# unit_domain_customer.py
import pytest
from src.domain.entities.customer import Customer
from src.domain.value_objects.address import Address

class TestCustomerEntity:
    def test_create_valid_customer(self):
        customer = Customer(
            name="John Doe",
            email="john@example.com"
        )
        assert customer.name == "John Doe"
        assert customer.email == "john@example.com"
    
    def test_customer_validation_fails_with_empty_name(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Customer(name="", email="john@example.com")
```

#### Application Layer Tests
```python
# unit_application_customer.py
import pytest
from unittest.mock import AsyncMock
from src.application.use_cases.customer_use_cases import CustomerUseCases

class TestCustomerUseCases:
    @pytest.fixture
    def mock_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def use_cases(self, mock_repository):
        return CustomerUseCases(mock_repository)
    
    async def test_create_customer_success(self, use_cases, mock_repository):
        mock_repository.get_by_email.return_value = None
        mock_repository.create.return_value = Customer(
            name="John Doe",
            email="john@example.com"
        )
        
        result = await use_cases.create_customer(
            name="John Doe",
            email="john@example.com"
        )
        
        assert result.name == "John Doe"
        mock_repository.create.assert_called_once()
```

#### Infrastructure Layer Tests
```python
# unit_infrastructure_customer.py
import pytest
from sqlalchemy.orm import Session
from src.infrastructure.repositories.customer_repository_impl import SQLAlchemyCustomerRepository
from src.domain.entities.customer import Customer

class TestCustomerRepository:
    @pytest.fixture
    def repository(self, db_session: Session):
        return SQLAlchemyCustomerRepository(db_session)
    
    async def test_create_customer(self, repository, db_session):
        customer = Customer(name="John Doe", email="john@example.com")
        
        result = await repository.create(customer)
        
        assert result.id is not None
        assert result.name == "John Doe"
        
        # Verify in database
        db_customer = db_session.query(CustomerModel).filter_by(
            id=result.id
        ).first()
        assert db_customer is not None
```

#### Integration Tests
```python
# integration_customer.py
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

class TestCustomerIntegration:
    async def test_create_and_retrieve_customer(
        self, 
        client: AsyncClient,
        db_session: Session
    ):
        # Create customer
        response = await client.post(
            "/api/v1/customers",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA",
                    "zip_code": "12345"
                }
            }
        )
        assert response.status_code == 201
        customer_id = response.json()["id"]
        
        # Retrieve customer
        response = await client.get(f"/api/v1/customers/{customer_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "John Doe"
```

### Test Fixtures (conftest.py)

```python
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from httpx import AsyncClient
from src.main import app
from src.infrastructure.database.base import Base

# Test database URL
TEST_DATABASE_URL = "postgresql://test_user:test_pass@localhost/test_db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[Session, None]:
    """Create test database session."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
async def client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

## Best Practices and Conventions

### 1. Naming Conventions

- **Entities**: Singular nouns (Customer, Order)
- **Repositories**: {Entity}Repository interface, SQLAlchemy{Entity}Repository implementation
- **Use Cases**: {Action}{Entity}UseCase or descriptive names for complex operations
- **Services**: {Entity}Service or {Domain}Service
- **Schemas**: {Entity}Create, {Entity}Update, {Entity}Response
- **Database Tables**: Plural, snake_case (customers, sales_transactions)

### 2. Code Organization

- **One class per file** for entities, use cases, and repositories
- **Group related functionality** in subdirectories (e.g., sales/, inventory/)
- **Keep domain layer pure** - no framework dependencies
- **Use type hints** throughout the codebase
- **Document complex business logic** with docstrings

### 3. Error Handling

```python
# Domain exceptions
class DomainException(Exception):
    """Base domain exception."""
    pass

class CustomerNotFoundException(DomainException):
    """Raised when customer is not found."""
    pass

# Use in API layer
try:
    customer = await use_cases.get_customer(customer_id)
except CustomerNotFoundException:
    raise HTTPException(status_code=404, detail="Customer not found")
except DomainException as e:
    raise HTTPException(status_code=400, detail=str(e))
```

### 4. Transaction Management

```python
# Use case with transaction
class TransferInventoryUseCase:
    async def execute(self, from_warehouse_id: UUID, to_warehouse_id: UUID, items: List[dict]):
        async with self.unit_of_work:
            # All operations in same transaction
            source = await self.warehouse_repo.get_by_id(from_warehouse_id)
            destination = await self.warehouse_repo.get_by_id(to_warehouse_id)
            
            for item in items:
                source.remove_item(item['item_id'], item['quantity'])
                destination.add_item(item['item_id'], item['quantity'])
            
            await self.warehouse_repo.update(source)
            await self.warehouse_repo.update(destination)
            
            # Commit happens automatically on context exit
```

### 5. Performance Considerations

- **Use pagination** for list endpoints
- **Implement caching** for frequently accessed data
- **Use database indexes** appropriately
- **Consider async/await** for I/O operations
- **Profile and optimize** critical paths

## Migration from Traditional Architecture

### From Traditional MVC to DDD

1. **Identify Bounded Contexts**: Group related functionality into domains
2. **Extract Business Logic**: Move from controllers to domain entities
3. **Create Repository Interfaces**: Abstract data access
4. **Implement Use Cases**: Extract controller logic to use cases
5. **Refactor Gradually**: Migrate one module at a time

### Common Pitfalls to Avoid

1. **Anemic Domain Models**: Ensure entities contain business logic
2. **Leaking Domain Logic**: Keep business rules in domain layer
3. **Over-engineering**: Start simple, add complexity as needed
4. **Ignoring Transactions**: Plan transaction boundaries carefully
5. **Tight Coupling**: Use dependency injection and interfaces

## Conclusion

This DDD architecture template provides a solid foundation for building maintainable, testable, and scalable applications. The key is to:

1. **Respect layer boundaries** - Dependencies flow inward
2. **Keep domain logic pure** - No framework dependencies
3. **Use dependency injection** - For flexibility and testability
4. **Test each layer** - In isolation and integration
5. **Evolve gradually** - Start simple and refactor as needed

Remember that DDD is not just about folder structure - it's about modeling your business domain effectively and maintaining clear boundaries between concerns. Use this template as a starting point and adapt it to your specific needs.