# Functional Specification

## Overview

Flow: a user uploads a file and is assigned a file ID. A signed URL is then
generated for that file ID and returned to the user. Anyone holding a
valid, non-expired signed URL can retrieve the file through the public
retrieval endpoint.

## Requirements

1. **Secure File Ingestion** — Users should be able to upload their files.
   Uploaded files are stored in a non-public directory on the local file
   system. Each upload is associated with a user ID.

2. **Link Generation (Signed URLs)** — Given a file ID and a TTL, generate
   a signed URL. The URL must be cryptographically signed and must remain
   valid even after a service restart.

3. **File Retrieval & Validation** — Create a public endpoint that accepts
   the signed URL, validates the signature and expiration, and serves the
   file if valid.

4. **Audit & Metadata** — Allow file owners to query the status of their
   files (filename, size, upload date). The service must also record an
   audit event every time a signed link is generated.

## API

- `POST v1/upload -> File Id`
  data: file location + user Id + file content

- `POST v1/generateSignedURL -> Signed URL`
  data: fileID + ttl

- `GET v1/status/fileId -> URL, filename, size, upload date`
  data: fileID + user authentication

- `GET v1/returnFile -> file`
  data: signedURL

## Data Model

- **SignedURLDataMapping**
  Storing the url against the signed url, ttl

- **FileMetadata**
  - ByteLength
  - Timestamp
  - UserId
  - FileId
  - FileType

- **AuditEvent**
  Recorded every time a signed link is generated.
  - FileId
  - RequestedBy
  - IssuedAt
  - ExpiresAt
