# Architecture Flow Diagram

High-level map of the request lifecycle and data flow across the four APIs.
Use this as the anchor for technical review — see [functionalspec.md](functionalspec.md)
for requirements and [codingspec.md](codingspec.md) for per-API implementation detail.

## Component / Layering View

Every request flows through the same layers: **router → service → repository
→ SQLAlchemy model → Postgres**. Routers own HTTP concerns (status codes),
services own business rules, repositories own persistence.

```mermaid
flowchart TB
    subgraph Client["Client (frontend / API consumer)"]
        FE[React frontend]
    end

    subgraph API["FastAPI app (app/main.py)"]
        direction TB
        R1["POST /v1/upload<br/>(routers/upload.py)"]
        R2["POST /v1/generateSignedURL<br/>(routers/signed_url.py)"]
        R3["GET /v1/status/{file_id}<br/>(routers/status.py)"]
        R4["GET /v1/returnFile<br/>(routers/return_file.py)"]

        S1[UploadService]
        S2[SignedURLService]
        S3[StatusService]
        S4[FileRetrievalService]
        SIGNER[SignedURLSigner<br/>itsdangerous HMAC]

        R1 --> S1
        R2 --> S2
        R3 --> S3
        R4 --> S4
        S2 --> SIGNER
        S4 --> SIGNER
    end

    subgraph Persistence["Persistence"]
        FSTORE[(Local filesystem<br/>storage/uploads)]
        subgraph DB["Postgres"]
            T1[(file_metadata)]
            T2[(signed_url_mapping)]
            T3[(audit_event)]
        end
    end

    FE -->|multipart file + user_id| R1
    FE -->|file_id + ttl + user_id| R2
    FE -->|file_id + user_id| R3
    FE -->|signed token| R4

    S1 -->|write bytes| FSTORE
    S1 -->|insert| T1

    S2 -->|read owner| T1
    S2 -->|check active / insert| T2
    S2 -->|insert| T3

    S3 -->|read| T1
    S3 -->|read active| T2

    S4 -->|read| T1
    S4 -->|stream bytes| FSTORE

    R4 -->|FileResponse| FE
    R1 -->|file_id| FE
    R2 -->|signed_url + expires_at| FE
    R3 -->|filename/size/date/signed_url| FE
```

## Request Lifecycle (Sequence View)

The end-to-end flow a file takes from ingestion to public retrieval:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as FastAPI Router
    participant Svc as Service Layer
    participant Signer as SignedURLSigner (HMAC)
    participant DB as Postgres
    participant FS as Local Filesystem

    Note over User,FS: 1. Ingestion
    User->>API: POST /v1/upload (file, user_id)
    API->>Svc: UploadService.upload()
    Svc->>FS: write bytes to storage/uploads/{file_id}
    Svc->>DB: INSERT file_metadata
    API-->>User: 200 { file_id }

    Note over User,FS: 2. Link generation
    User->>API: POST /v1/generateSignedURL (file_id, ttl, user_id)
    API->>Svc: SignedURLService.generate()
    Svc->>DB: SELECT file_metadata WHERE file_id
    Svc->>DB: SELECT active signed_url_mapping WHERE file_id
    Svc->>Signer: sign({file_id, exp})
    Signer-->>Svc: opaque token
    Svc->>DB: INSERT signed_url_mapping
    Svc->>DB: INSERT audit_event
    API-->>User: 200 { signed_url, expires_at }

    Note over User,FS: 3. Status check (owner only)
    User->>API: GET /v1/status/{file_id}?requesting_user_id
    API->>Svc: StatusService.get_status()
    Svc->>DB: SELECT file_metadata + active signed_url_mapping
    API-->>User: 200 { filename, byte_length, uploaded_at, signed_url }

    Note over User,FS: 4. Public retrieval (anonymous, token is the credential)
    User->>API: GET /v1/returnFile?token=...
    API->>Svc: FileRetrievalService.resolve()
    Svc->>Signer: unsign(token) — verify HMAC + exp
    Signer-->>Svc: file_id (or raises Invalid/Expired)
    Svc->>DB: SELECT file_metadata WHERE file_id
    API->>FS: stream bytes from storage_path
    API-->>User: 200 file bytes (Content-Disposition: filename)
```

## Key Data-Flow Properties

- **Stateless validity**: `returnFile` never re-checks `signed_url_mapping`
  at retrieval time — the signature + embedded `exp` in the token is the
  sole source of truth, so validation survives service restarts and doesn't
  require a DB round trip's result to be authoritative.
- **Ownership gate**: `generateSignedURL` and `status` both compare
  `file_metadata.user_id` against a caller-supplied `requesting_user_id`
  (no session/auth token backs this — see [codingspec.md](codingspec.md) notes).
- **One active link per file**: `generateSignedURL` checks
  `signed_url_mapping` for a non-expired row before minting a new token,
  enforcing at most one live signed URL per file at a time.
- **Audit trail**: every successful `generateSignedURL` call writes an
  `audit_event` row, independent of whether the link is ever used.
- **Two persistence stores**: file bytes live on local disk
  (`storage/uploads/{file_id}`), all metadata/audit/mapping records live in
  Postgres — a retrieval always requires both to be consulted.
