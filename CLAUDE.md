# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI backend project following Domain-Driven Design (DDD) architecture for a comprehensive rental and inventory management system. The project demonstrates clean architecture principles with clear separation between domain logic, application services, infrastructure, and API layers.

## Essential Commands

### Development
```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn src.main:app --reload

# Run with specific host/port
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run specific test markers
poetry run pytest -m unit        # Unit tests only
poetry run pytest -m integration # Integration tests only

# Run specific test file
poetry run pytest src/tests/unit/test_user_entity.py

# Run with verbose output
poetry run pytest -v
```

### Code Quality
```bash
# Format code
poetry run black src/

# Sort imports
poetry run isort src/

# Lint code
poetry run flake8 src/

# Type checking
poetry run mypy src/
```

### Database Operations
```bash
# Create new migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Check current revision
poetry run alembic current
```

## Architecture Overview

### Domain-Driven Design Layers

The project follows DDD with four distinct layers:

1. **Domain Layer** (`src/domain/`)
   - **Entities**: Core business objects with business logic (inherit from BaseEntity)
   - **Value Objects**: Immutable objects representing domain concepts (Email, PhoneNumber, Address)
   - **Repository Interfaces**: Abstract contracts for data persistence
   - **No external dependencies** - Pure Python business logic

2. **Application Layer** (`src/application/`)
   - **Use Cases**: Single-purpose business operations (one use case per operation)
   - **Services**: Orchestration of multiple use cases (when needed)
   - **No framework dependencies** - Only depends on domain layer

3. **Infrastructure Layer** (`src/infrastructure/`)
   - **Database Models**: SQLAlchemy ORM models (separate from domain entities)
   - **Repository Implementations**: Concrete implementations of domain repositories
   - **Database Configuration**: AsyncSession setup for async operations
   - **External Service Integrations**: (future: payment gateways, notifications)

4. **API Layer** (`src/api/v1/`)
   - **Endpoints**: FastAPI route handlers organized by resource
   - **Schemas**: Pydantic models for request/response validation
   - **Dependencies**: Dependency injection setup
   - **Middleware**: Cross-cutting concerns

### Key Patterns

1. **Repository Pattern**
   - Abstract interfaces in domain layer
   - Concrete implementations in infrastructure
   - Enables testing with mock repositories
   - Database-agnostic domain layer

2. **Use Case Pattern**
   - Each use case is a single class with `execute` method
   - Encapsulates one business operation
   - Easy to test and understand
   - Examples: CreateUserUseCase, GetUserUseCase, UpdateUserUseCase

3. **Value Objects**
   - Email validation as a value object
   - Future: PhoneNumber, Address, Money
   - Self-validating with business rules
   - Immutable once created

4. **Entity Base Class**
   - All entities inherit from BaseEntity
   - Common fields: id (UUID), created_at, updated_at, is_active
   - Audit fields: created_by, updated_by
   - Soft delete support (is_active flag)

5. **Dependency Injection**
   - FastAPI's Depends() for automatic injection
   - Repository → Use Case → Endpoint chain
   - Easy to swap implementations for testing

## Business Domain Understanding

Based on the business rules and data model documents, this system is designed for:

### Core Capabilities
1. **Multi-Location Inventory Management**
   - Track items across stores and warehouses
   - Serial number tracking for high-value items
   - Condition grading (A/B/C/D)
   - Status tracking through lifecycle

2. **Rental Operations**
   - Pre-rental inspections with photo documentation
   - Flexible rental periods with extensions
   - Partial returns support
   - Late fee calculations per item
   - Damage assessment and liability determination
   - Security deposit management

3. **Sales Operations**
   - Direct sales with inventory reservation
   - Commission tracking
   - Warranty activation
   - Multi-tier pricing

4. **Customer Management**
   - Individual and business customers
   - Multiple contact methods per customer
   - Credit limits for business customers
   - Customer tier benefits (Bronze/Silver/Gold/Platinum)
   - Blacklist management

### Complex Business Rules

1. **Partial Returns**
   - Customers can return items in multiple transactions
   - Per-item fee calculation (not per transaction)
   - Proportional deposit release
   - Outstanding item tracking

2. **Inventory Status Flow**
   - Sales: AVAILABLE_SALE → RESERVED_SALE → SOLD
   - Rentals: AVAILABLE_RENT → RESERVED_RENT → RENTED → INSPECTION_PENDING → CLEANING/REPAIR → AVAILABLE_RENT

3. **Category Hierarchy**
   - Self-referencing categories with unlimited levels
   - Products only assignable to leaf categories
   - Automatic path maintenance

## Common Development Tasks

### Adding a New Domain Entity

1. Create entity in `src/domain/entities/{entity}.py`
   - Inherit from BaseEntity
   - Add business logic methods
   - Include validation in constructor

2. Create repository interface in `src/domain/repositories/{entity}_repository.py`
   - Define abstract methods for data operations
   - Use async/await for all methods

3. Create value objects if needed in `src/domain/value_objects/`

4. Implement infrastructure:
   - SQLAlchemy model in `src/infrastructure/models/`
   - Repository implementation in `src/infrastructure/repositories/`
   - Add model-entity conversion methods

5. Create use cases in `src/application/use_cases/{entity}/`
   - One file per use case
   - Inject repository through constructor

6. Add API layer:
   - Pydantic schemas in `src/api/v1/schemas/`
   - Endpoints in `src/api/v1/endpoints/`
   - Wire up dependencies

7. Create and run migrations:
   ```bash
   poetry run alembic revision --autogenerate -m "Add {entity} table"
   poetry run alembic upgrade head
   ```

8. Add tests:
   - Unit tests for entity and value objects
   - Integration tests for API endpoints
   - Use fixtures from conftest.py

### Working with Async SQLAlchemy

- All repository methods must be async
- Use `async with` for transactions
- AsyncSession injected through dependencies
- Remember to install greenlet: included in SQLAlchemy[asyncio]

### Testing Strategy

1. **Unit Tests** (`src/tests/unit/`)
   - Test domain entities and value objects
   - Test use cases with mock repositories
   - No database or external dependencies

2. **Integration Tests** (`src/tests/integration/`)
   - Test API endpoints end-to-end
   - Use in-memory SQLite for speed
   - Test actual database operations

3. **Fixtures** (`src/tests/conftest.py`)
   - `db_session`: Provides test database session
   - `override_get_db`: Overrides FastAPI dependencies
   - Automatic cleanup after each test

## Important Technical Details

### Database
- SQLite for development (with aiosqlite for async)
- PostgreSQL ready (just change DATABASE_URL)
- UUID primary keys for all entities
- Soft deletes using is_active flag
- Automatic timestamp management

### Security
- Password hashing with bcrypt (via passlib)
- JWT ready (configuration in place)
- CORS middleware configured
- Environment-based configuration

### API Design
- RESTful endpoints
- Consistent error responses (HTTPException)
- Request/response validation with Pydantic
- API versioning (/api/v1)
- Automatic OpenAPI documentation

### Performance Considerations
- Async throughout for I/O operations
- Database connection pooling
- Pagination support in list endpoints
- Indexed fields for common queries

## Environment Variables

Key variables in `.env`:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: For JWT tokens
- `DEBUG`: Enable debug mode
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins

## Future Expansion Areas

Based on the business rules document, future entities to implement:
- Customer (with contact methods and addresses)
- Product/SKU/Category management
- Inventory tracking with serial numbers
- Rental transactions with calendar blocking
- Inspection and quality control
- Payment and deposit management
- Reporting and analytics

The architecture is designed to handle these complex requirements while maintaining clean separation of concerns and testability.