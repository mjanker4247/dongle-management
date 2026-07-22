# Dongle Manager

Python/FastAPI + React monorepo for managing physical software dongles, PCs, locations,
categories, and test modules.

## Features

- CRUD for locations, PCs, dongles, categories, and test modules
- Assign dongles to PCs (one PC at a time) and PCs to locations
- Assign modules to categories; enable/disable modules per dongle
- Category completeness check (required vs enabled modules)
- CSV / paste import with preview, upsert, and result summary
- Quick Dongle Entry keyboard workflow for operators
- TÜV-style clean business UI (blue accent, white/gray surfaces)

## Matching / import policy

- Names and dongle IDs are trimmed
- Empty values are rejected
- Duplicate matching is **case-insensitive**
- Original capitalization is preserved on create/update
- Imports upsert instead of creating duplicates

## Project structure

```
backend/     FastAPI + SQLAlchemy 2 + Alembic
frontend/    React + Vite + TypeScript + MUI
docker-compose.yml
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- Optional: Docker / Docker Compose for PostgreSQL stack

## Backend setup (SQLite local default)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Apply migrations
alembic upgrade head

# Seed example data (optional)
SEED_ON_STARTUP=true uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/health

### PostgreSQL via Docker

```bash
# From repo root
docker compose up -d db

# In backend/.env
DATABASE_URL=postgresql+psycopg2://dongle:dongle@localhost:5432/dongle_manager

alembic upgrade head
SEED_ON_STARTUP=true uvicorn app.main:app --reload --port 8000
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

App: http://127.0.0.1:5173

Vite proxies `/api` to the backend on port 8000.

Optional env:

```bash
# frontend/.env
VITE_API_BASE_URL=/api
```

## Tests

```bash
cd backend
source .venv/bin/activate
SEED_ON_STARTUP=false python -m pytest app/tests -v
```

Covered scenarios:

- Completeness check (complete / incomplete / extras)
- Dongle assigned to only one PC at a time
- Import duplicates do not create duplicates
- Enable/disable modules on dongles
- Import preview does not persist

## Sample CSV imports

Examples live in `backend/samples/`:

- `pcs.csv`
- `dongles.csv`
- `categories.csv`
- `test_modules.csv`

Use the Import page, or API:

```bash
curl -F "file=@backend/samples/pcs.csv" -F "preview_only=false" \
  http://127.0.0.1:8000/api/import/pcs
```

Paste import example:

```bash
curl -X POST http://127.0.0.1:8000/api/import/dongles/text \
  -H 'Content-Type: application/json' \
  -d '{"text":"DNG-3001\\nDNG-3002","preview_only":false}'
```

## Completeness check

```bash
curl "http://127.0.0.1:8000/api/dongles/1/completeness?category_id=1"
```

Response includes:

- `total_required_modules`
- `enabled_required_modules`
- `missing_modules`
- `extra_enabled_modules`
- `is_complete`

Required modules = active modules assigned to the category.  
Complete = no missing required modules.

## Full Docker stack

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Quick Dongle Entry shortcuts

| Key | Action |
|-----|--------|
| ↑ / ↓ | Move between modules |
| Space | Toggle selected module |
| Type | Filter modules by name |
| Enter | Save changes |
| Esc | Clear filter |

## Cascade / delete behavior

- Deleting a location unassigns its PCs (PCs/dongles are kept)
- Deleting a PC unassigns its dongles
- Deleting a category removes category↔module links only
- Deleting a dongle removes dongle↔module links
- Deleting a test module removes its category and dongle links
