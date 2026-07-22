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
backend/          FastAPI + SQLAlchemy 2 + Alembic (managed with uv)
frontend/         React + Vite + TypeScript + MUI
manage            Local start/stop/update script (Linux/macOS)
manage.ps1        Local start/stop/update script (Windows PowerShell)
docker-compose.yml
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager) — installed automatically by `./manage setup` / `.\manage.ps1 setup` if missing
- Node.js 20+
- Optional: Docker / Docker Compose for PostgreSQL stack

## Quick start (recommended)

### Linux / macOS

```bash
./manage setup    # install uv deps, npm deps, create .env, migrate DB
./manage start    # start backend + frontend in the background
./manage status
./manage logs     # follow logs (Ctrl+C to stop following)
./manage stop
```

### Windows (PowerShell)

```powershell
# If scripts are blocked, run once:
# Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

.\manage.ps1 setup
.\manage.ps1 start
.\manage.ps1 status
.\manage.ps1 logs
.\manage.ps1 stop
```

| Command | Description |
|---------|-------------|
| `setup` | Install dependencies, env files, and migrate |
| `update` | Re-sync deps and apply migrations |
| `update --refresh` | Also refresh `uv.lock` upgrades |
| `start` / `stop` / `restart` | Control both services |
| `status` | Process and health status |
| `logs [backend\|frontend\|all]` | Tail logs |
| `migrate` | Run Alembic migrations |
| `seed` | Insert example seed data (skips if present) |
| `test` | Run backend tests via `uv run pytest` |
| `backend` / `frontend` | Run one service in the foreground |
| `doctor` | Check tooling and project health |

Use `./manage <cmd>` on Unix or `.\manage.ps1 <cmd>` on Windows.

UI: http://127.0.0.1:5173 · API docs: http://127.0.0.1:8000/docs

Environment overrides: `BACKEND_PORT`, `FRONTEND_PORT`, `SEED_ON_STARTUP`.

## Manual backend setup with uv

```bash
cd backend
uv sync
cp .env.example .env
uv run alembic upgrade head
SEED_ON_STARTUP=true uv run uvicorn app.main:app --reload --port 8000
```

`uv.lock` is the source of truth. `requirements.txt` is an exported freeze for convenience:

```bash
cd backend
uv export --no-dev --no-hashes -o requirements.txt
```

### PostgreSQL via Docker

```bash
docker compose up -d db

# In backend/.env
DATABASE_URL=postgresql+psycopg2://dongle:dongle@localhost:5432/dongle_manager

./manage migrate
SEED_ON_STARTUP=true ./manage backend
```

## Manual frontend setup

```bash
cd frontend
npm install
npm run dev
```

Optional env:

```bash
# frontend/.env
VITE_API_BASE_URL=/api
```

## Tests

```bash
./manage test
# Windows:
# .\manage.ps1 test
# or
cd backend && uv run pytest app/tests -v
```

Covered scenarios (57 tests):

- Completeness check (complete / incomplete / extras / inactive modules / empty category)
- Dongle assigned to only one PC at a time
- Import duplicates, casing updates, CSV upload, preview-only
- Enable/disable modules; POST replace vs PUT upsert semantics
- Case-insensitive uniqueness for locations, PCs, categories, modules, dongle IDs
- Cascade/delete behavior (locations, PCs, categories, modules, dongles)
- Category module assignment and manual vs alphabetical order
- Test module reorder, filters, and auto sort_index
- Import parsing (headers, CSV columns, BOM, latin-1, newlines)
- Dashboard counts, unassigned dongles, and dongle search
- Name normalization helpers

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

## Completeness check

```bash
curl "http://127.0.0.1:8000/api/dongles/1/completeness?category_id=1"
```

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
