# DigiScrapyard API

Backend API for the DigiScrapyard scrap management mobile apps (Shopfloor, Scrapeyard, Admin).

## Stack

- FastAPI + Uvicorn
- SQLAlchemy 2.x + MySQL
- JWT authentication (DB-stored plant/admin credentials)
- Alembic migrations

## Quick Start

1. Copy environment variables from [`docs/env.example`](docs/env.example) to `.env`
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `alembic upgrade head`
4. Seed admin: `python scripts/seed_admin.py`
5. Start server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- Frontend integration guide: [`docs/api_integration.md`](docs/api_integration.md)

## Tests

```bash
TESTING=1 pytest app/auto_tests/ -v
```

## Docker

```bash
cd build_infra && docker compose up --build
```

## User Roles

| Role | App | Key endpoints |
|------|-----|---------------|
| shopfloor | Shopfloor | dispatch, rejected, history |
| scrapeyard | Scrapeyard | accept, reject, history |
| admin | Admin | plants, reporting, sales |
