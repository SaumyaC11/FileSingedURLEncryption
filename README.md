# File Service

A FastAPI backend for secure file ingestion, signed-URL link generation, and
public file retrieval, with a React frontend on top.

- Product behavior: [docs/functionalspec.md](docs/functionalspec.md)
- Implementation detail per API: [docs/codingspec.md](docs/codingspec.md)
- Request lifecycle / data flow diagrams: [docs/architecture.md](docs/architecture.md)

## Prerequisites

- Python 3.11+ (developed against 3.14)
- Node.js 20+ and npm (for the frontend)
- A reachable Postgres instance (local or managed — see `DATABASE_URL` below)

## Backend Setup

1. Create and activate a virtual environment, then install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt   # installs runtime deps + pytest/httpx
   ```

   Use `pip install -r requirements.txt` instead if you only need to run the
   service (no tests).

2. Configure environment variables. Copy the example file and adjust values
   for your environment:

   ```bash
   cp .env.example .env
   ```

   | Variable | Purpose |
   |---|---|
   | `DATABASE_URL` | SQLAlchemy connection string for Postgres |
   | `STORAGE_DIR` | Local, non-public directory where uploaded file bytes are written |
   | `SIGNED_URL_SECRET_KEY` | HMAC secret for signing/validating file tokens — must stay stable across restarts, or all previously issued signed URLs become invalid |
   | `SIGNED_URL_SALT` | Salt namespacing the signer |
   | `BASE_URL` | Public base URL used to build the fully-qualified signed URL returned by `generateSignedURL` |

   All settings have safe local-dev defaults in `app/config.py` if `.env` is
   omitted, but you must still point `DATABASE_URL` at a real database you
   can reach.

3. Database tables are created automatically on app startup
   (`Base.metadata.create_all` in `app/main.py`) — no separate migration
   step is required.

## Running the Backend

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

The API is now available at `http://localhost:8001` (match `BASE_URL` in
your `.env` to whatever host/port you run on). Interactive API docs are
served at `http://localhost:8001/docs`.

## Frontend Setup & Running

```bash
cd frontend
npm install
cp .env.example .env   # sets VITE_API_BASE_URL, defaults to http://localhost:8001
npm run dev
```

The dev server runs at `http://localhost:5173` (the origin the backend's
CORS config allows by default). Other frontend scripts:

```bash
npm run build     # type-check + production build
npm run preview   # preview the production build locally
npm run lint      # oxlint
```

## Testing

Backend tests live under `tests/` and are split into two tiers:

- **Unit tests** (`tests/services/`, `tests/routers/`) — fully mocked
  repositories/services, no real database or filesystem required.
- **Integration tests** (`tests/integration/`) — exercise real repositories
  against the Postgres instance configured via `DATABASE_URL`. Each test
  runs inside a transaction that's rolled back on teardown, so they're safe
  to run against a shared dev database. If that database isn't reachable,
  these tests are skipped automatically rather than failing.

Run the default (unit) suite:

```bash
source .venv/bin/activate
pytest
```

`pytest.ini` excludes the `integration` marker by default
(`addopts = -m "not integration"`). To run integration tests too (requires a
reachable `DATABASE_URL`):

```bash
pytest -m integration          # integration tests only
pytest -m ""                   # everything, unit + integration
```

With coverage:

```bash
pytest --cov=app
```

There is no frontend test suite configured yet; verify frontend changes
manually via `npm run dev` against a running backend.

## Project Layout

```
app/
  main.py              FastAPI app, router registration, CORS, table creation
  config.py            Settings (env-driven)
  database.py          SQLAlchemy engine/session
  models.py            ORM models: FileMetadata, SignedURLMapping, AuditEvent
  repositories.py       Persistence layer
  schemas.py           Pydantic request/response models
  routers/             One router per API endpoint
  services/            Business logic per API endpoint
tests/
  services/, routers/  Unit tests (mocked dependencies)
  integration/         Tests against a real Postgres instance
frontend/
  src/                 React app (upload, status check, retrieval forms)
docs/
  functionalspec.md    Requirements and API/data-model overview
  codingspec.md        Per-API implementation detail
  architecture.md      Request lifecycle and data-flow diagrams
```
