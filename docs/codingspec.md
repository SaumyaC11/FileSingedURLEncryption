# Coding Specification

This document describes the concrete implementation of the APIs defined in
[functionalspec.md](functionalspec.md): request/response contracts, internal
control flow, error handling, and the data model as actually implemented in
`app/`.

## Architecture

Each API is a thin FastAPI router (`app/routers/*.py`) that delegates to a
service class (`app/services/*.py`), which in turn uses repositories
(`app/repositories.py`) for persistence via SQLAlchemy models (`app/models.py`).
Dependencies (DB session, settings, and service instances) are wired in
`app/dependencies.py` using FastAPI's `Depends`.

Layering: **router → service → repository → SQLAlchemy model / DB**.
Services raise plain Python exceptions for domain errors; routers translate
those into `HTTPException`s with the appropriate status codes. This keeps
services framework-agnostic and easy to unit test.

## Configuration (`app/config.py`)

`Settings` (pydantic-settings), loaded from environment variables or a `.env`
file:

| Setting | Default | Purpose |
|---|---|---|
| `database_url` | `postgresql+psycopg://fileservice:fileservice_dev_pw@localhost:5432/fileservice` | SQLAlchemy connection string |
| `storage_dir` | `storage/uploads` | Non-public directory where raw file bytes are written |
| `signed_url_secret_key` | `dev-only-insecure-secret-change-me` | HMAC secret for signing tokens; **must stay stable across restarts/deploys** or all outstanding signed URLs become invalid |
| `signed_url_salt` | `signed-url` | Salt namespacing the signer (`itsdangerous`) |
| `base_url` | `http://localhost:8000` | Prefix used to build the fully-qualified signed URL returned to clients |

`get_settings()` is `@lru_cache`d, so settings are read once per process.

## Data Model (`app/models.py`)

### `FileMetadata` (table `file_metadata`)
| Column | Type | Notes |
|---|---|---|
| `file_id` | UUID, PK | Generated with `uuid.uuid4()` at upload time |
| `user_id` | String, indexed | Owner of the file; used for authorization checks |
| `filename` | String | Original filename from the upload, or `"unnamed"` |
| `file_type` | String | MIME type from the upload, or `application/octet-stream` |
| `byte_length` | Integer | Size of the uploaded content in bytes |
| `storage_path` | String | Absolute/relative path on local disk where bytes were written |
| `uploaded_at` | DateTime (tz-aware) | Defaults to `utcnow()` at insert |

### `SignedURLMapping` (table `signed_url_mapping`) — the `SignedURLDataMapping` from the functional spec
| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `file_id` | UUID, FK → `file_metadata.file_id`, indexed | |
| `signed_url` | String, unique, indexed | The full URL returned to the client |
| `ttl_seconds` | Integer | TTL requested at generation time |
| `issued_at` | DateTime (tz-aware) | Defaults to `utcnow()` |
| `expires_at` | DateTime (tz-aware) | `issued_at + ttl_seconds`, computed by the service |

This table is a persistence/audit record of issued URLs and is also used to
enforce "one active signed URL per file" (see below). It is **not** the
source of truth for validity — validity is determined statelessly by the
signed token itself (see Signer, below).

### `AuditEvent` (table `audit_event`)
| Column | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `file_id` | UUID, FK → `file_metadata.file_id`, indexed | |
| `requested_by` | String | The `requesting_user_id` that generated the link |
| `issued_at` | DateTime (tz-aware) | Defaults to `utcnow()` |
| `expires_at` | DateTime (tz-aware) | Mirrors the signed URL's expiry |

Written exactly once per successful `POST /v1/generateSignedURL` call, by
`AuditEventRepository.record_signed_url_issued`.

## Signed URL scheme (`app/services/signed_url_signer.py`)

Uses `itsdangerous.URLSafeSerializer(secret_key, salt=signed_url_salt)`
(HMAC-based, not a JWT). The payload is:

```json
{ "file_id": "<uuid str>", "exp": <unix timestamp int> }
```

- **Signing** (`sign`): serializes `{file_id, exp}` into an opaque
  URL-safe token string. No expiry check happens here — the token is
  produced from the caller-provided `expires_at`.
- **Verifying** (`unsign`):
  1. `serializer.loads(token)` — raises `InvalidSignedToken` if the HMAC
     signature doesn't match (tampered or garbage token).
  2. Compares `exp` against `datetime.now(timezone.utc)` — raises
     `ExpiredSignedToken` if expired.
  3. Returns the embedded `file_id` as a `uuid.UUID`.

Because expiry is embedded in the signed payload rather than looked up from
the database, validation is **stateless** and survives a service restart as
long as `signed_url_secret_key`/`signed_url_salt` are unchanged — this
satisfies functional-spec requirement 2. The `signed_url_mapping` table is
therefore for bookkeeping/audit/"one active URL" enforcement, not for
validity checks at retrieval time.

The final signed URL returned to clients has the shape:

```
{base_url}/v1/returnFile?token={token}
```

## API Details

### `POST /v1/upload`

- **Router**: `app/routers/upload.py`
- **Content-Type**: `multipart/form-data`
- **Request fields**:
  - `user_id: str` (form field, min length 1)
  - `file: UploadFile` (file field)
- **Response**: `UploadResponse { file_id: UUID }`, HTTP 200
- **Flow**:
  1. Router reads the full file body into memory (`await file.read()`).
  2. `UploadService.upload()`:
     - Generates a new `file_id = uuid.uuid4()`.
     - `FileStorage.save(file_id, content)` writes the raw bytes to
       `storage_dir/{file_id}` (no extension, filename is not part of the
       path) and returns the path as `storage_path`.
     - `FileMetadataRepository.create(...)` inserts a `FileMetadata` row
       with `user_id`, `filename` (or `"unnamed"` if none given),
       `file_type` (or `application/octet-stream` if none given),
       `byte_length = len(content)`, and `storage_path`, then commits.
  3. Returns the new `file_id`.
- **Errors**: none explicitly handled; FastAPI validation errors (422) apply
  if `user_id` or `file` are missing.
- **Notes**: The entire file is buffered in memory before being written to
  disk. 

### `POST /v1/generateSignedURL`

- **Router**: `app/routers/signed_url.py`
- **Request body** (`GenerateSignedURLRequest`):
  - `file_id: UUID`
  - `ttl_seconds: int` (must be `> 0` and `<= 2,592,000` i.e. 30 days)
  - `requesting_user_id: str` (min length 1)
- **Response** (`GenerateSignedURLResponse`), HTTP 200:
  - `signed_url: str`
  - `expires_at: datetime`
- **Flow** (`SignedURLService.generate`):
  1. Look up `FileMetadata` by `file_id`. If missing → `FileNotFoundError`.
  2. Check `file_metadata.user_id == requesting_user_id`. If not → 
     `NotFileOwnerError` (ownership check; anyone who isn't the uploader is
     rejected, regardless of any real authentication).
  3. Check `SignedURLRepository.get_active(file_id)` — a query for any
     `SignedURLMapping` row for this file with `expires_at > now()`,
     ordered by `issued_at desc`. If one exists → `ActiveSignedURLExistsError`
     (a file may have **at most one active signed URL at a time**; a new one
     cannot be minted until the previous one expires).
  4. Compute `expires_at = now() + ttl_seconds`.
  5. `SignedURLSigner.sign(file_id, expires_at)` produces the token; the
     full URL is built as `{base_url}/v1/returnFile?token={token}`.
  6. Persist a `SignedURLMapping` row (`SignedURLRepository.create`) and an
     `AuditEvent` row (`AuditEventRepository.record_signed_url_issued`) —
     both committed independently, in that order, **not** wrapped in a
     single DB transaction (each repository call does its own commit).
  7. Return `{signed_url, expires_at}`.
- **Error → HTTP mapping**:
  - `FileNotFoundError` → 404
  - `NotFileOwnerError` → 403
  - `ActiveSignedURLExistsError` → 409
- **Notes**: `requesting_user_id` is a caller-supplied string with no actual
  authentication/session verification behind it — anyone who knows a user's
  ID can request links "as" that user. This is a known gap relative to a
  production auth model.

### `GET /v1/status/{file_id}`

- **Router**: `app/routers/status.py`
- **Path param**: `file_id: UUID`
- **Query param**: `requesting_user_id: str` (min length 1) — stands in for
  the "user authentication" mentioned in the functional spec; there is no
  token/session check, just an ID comparison.
- **Response** (`FileStatusResponse`), HTTP 200:
  - `filename: str`
  - `byte_length: int`
  - `uploaded_at: datetime`
  - `signed_url: str | None` — the currently active signed URL for the
    file, or `null` if none is active
- **Flow** (`StatusService.get_status`):
  1. Look up `FileMetadata` by `file_id`. If missing → `FileNotFoundError`
     (404).
  2. Check `metadata.user_id == requesting_user_id`, else
     `NotFileOwnerError` (403).
  3. `SignedURLRepository.get_active(file_id)` to find the current
     non-expired mapping (or `None`).
  4. Return filename/size/upload date plus the active signed URL if any.
- **Note**: the functional spec lists "URL" as part of the response; the
  implementation returns the *currently active* signed URL only (not the
  full history), and it can be `null`.

### `GET /v1/returnFile`

- **Router**: `app/routers/return_file.py`
- **Query param**: `token: str` — the opaque token embedded in the signed
  URL (i.e. the `token` query param of the URL returned by
  `generateSignedURL`, not the whole URL).
- **Response**: raw file bytes via `FileResponse`, with:
  - `filename` set to the original upload filename (drives
    `Content-Disposition`, exposed to the browser via the CORS
    `expose_headers=["Content-Disposition"]` config in `main.py`)
  - `media_type` set to the stored `file_type`
- **Flow** (`FileRetrievalService.resolve`):
  1. `SignedURLSigner.unsign(token)`:
     - Bad/tampered signature → `InvalidSignedToken` → HTTP 401.
     - Valid signature but `exp` in the past → `ExpiredSignedToken` → HTTP 410.
  2. Look up `FileMetadata` by the recovered `file_id`. If the file record
     was deleted after the link was issued → `FileNotFoundError` → HTTP 404.
  3. Return the `FileMetadata`, and the router streams the file from
     `storage_path` on local disk.
- **Notes**: This endpoint is intentionally public/unauthenticated — the
  signed token itself is the credential. It does **not** check the
  `signed_url_mapping` table at all; a token remains valid purely by HMAC +
  embedded expiry, so revoking a row from that table does not invalidate an
  already-issued, unexpired token.

## Error Handling Summary

| Exception | Raised by | HTTP Status |
|---|---|---|
| `FileNotFoundError` (signed_url_service) | generateSignedURL | 404 |
| `NotFileOwnerError` (signed_url_service) | generateSignedURL | 403 |
| `ActiveSignedURLExistsError` | generateSignedURL | 409 |
| `FileNotFoundError` (status_service) | status | 404 |
| `NotFileOwnerError` (status_service) | status | 403 |
| `InvalidSignedToken` | returnFile | 401 |
| `ExpiredSignedToken` | returnFile | 410 |
| `FileNotFoundError` (file_retrieval_service) | returnFile | 404 |

Each service module defines its own `FileNotFoundError`/`NotFileOwnerError`
classes (not shared across modules), so routers must import the
service-specific exception types they catch.

## Cross-Cutting Notes

- **Database session lifecycle**: `get_db()` yields a `SessionLocal()` per
  request and closes it in a `finally` block; each repository method commits
  immediately rather than deferring to a request-scoped unit of work.
- **CORS**: configured in `app/main.py` for `http://localhost:5173` (the
  Vite dev server) only, all methods/headers allowed, with
  `Content-Disposition` explicitly exposed so the frontend can read the
  downloaded filename.
- **Schema setup**: `Base.metadata.create_all(bind=engine)` runs at import
  time in `main.py` — there is no separate migration tool (e.g. Alembic) in
  use.
