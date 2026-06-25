# DigiScrapyard API

Backend API for scrap management (Shopfloor, Scrapeyard, Admin).

## Stack

- FastAPI + Uvicorn
- SQLAlchemy 2.x + MySQL
- JWT authentication
- Alembic migrations
- Docker

## Quick Start (local venv)

```bash
cp docs/env.example .env   # edit with your MySQL creds
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Quick Start (Docker on server)

```bash
cp docs/env.example .env   # edit MYSQL_HOST, creds, JWT_SECRET
docker compose up -d --build
```

## Seeded logins (after `seed_data.py`)

| Role | login_id | password | Notes |
|------|----------|----------|-------|
| Admin | admin | Admin@123 | env override |
| Shopfloor UDE | UDE | 1234 | QR location 3 |
| Shopfloor UTE | UTE | 1234 | QR location 2 |
| Shopfloor U535 | U535 | 1234 | QR location 4 |
| Scrapeyard | SCRAP | 1234 | shared for all plants |

## QR location mapping

| Plant | QR LOCATION value |
|-------|-------------------|
| UTE | 2 |
| UDE | 3 |
| U535 | 4 |

Dispatch requires logged-in plant to match QR location plant.

## Docs

- API integration: [`docs/api_integration.md`](docs/api_integration.md)
- Environment template: [`docs/env.example`](docs/env.example)
- Swagger: `http://localhost:8000/docs`

## Tests

```bash
TESTING=1 JWT_SECRET=test-secret-key PYTHONPATH=. pytest app/auto_tests/ -v
```
