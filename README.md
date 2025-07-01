# FastAPI DDD Project

A FastAPI project following Domain-Driven Design (DDD) architecture with SQLAlchemy, Alembic, and Pytest.

## Project Structure

```
src/
├── domain/              # Domain layer (entities, repositories, value objects)
├── application/         # Application layer (use cases, services)
├── infrastructure/      # Infrastructure layer (database, models, repositories)
├── api/                 # API layer (endpoints, schemas, dependencies)
├── core/               # Core configurations
├── tests/              # Test suite
└── main.py             # Application entry point
```

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Run the application:
```bash
uvicorn src.main:app --reload
```

## Testing

Run all tests:
```bash
pytest
```

Run unit tests only:
```bash
pytest -m unit
```

Run integration tests only:
```bash
pytest -m integration
```

Run with coverage:
```bash
pytest --cov=src
```

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc