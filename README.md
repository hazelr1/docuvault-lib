# docuvault-lib

DocuVault backend foundation implemented as a modular Django monolith for secure document storage and processing.

## Current architecture

```text
Client
  -> Django REST API (/api/v1)
       -> accounts (JWT auth + registration + current user)
       -> rbac (roles + user-role bindings)
       -> documents (upload/list/detail/update/delete/download + grants)
       -> processing (extract -> clean -> chunk)
       -> audit (basic access log model)
       -> common (health + API exception formatting)
  -> PostgreSQL-ready relational models (SQLite fallback for local dev/tests)
  -> File storage via Django FileField (local media in this foundation)
```

## Implemented modules

- `backend/apps/accounts`
  - Custom user model
  - `POST /api/v1/auth/register/`
  - `POST /api/v1/auth/login/` (JWT access/refresh)
  - `POST /api/v1/auth/refresh/`
  - `POST /api/v1/auth/logout/` (refresh token blacklist)
  - `GET /api/v1/auth/me/`
- `backend/apps/rbac`
  - Roles: `student`, `faculty`, `administrator`
  - User-role junction model (many-to-many via explicit table)
- `backend/apps/documents`
  - UUID-based document model
  - Owner-based and grant-based authorization filtering
  - Document permissions to user OR role (`view`, `download`, `manage`)
  - Endpoints:
    - `POST /api/v1/documents/`
    - `GET /api/v1/documents/`
    - `GET /api/v1/documents/{id}/`
    - `PATCH /api/v1/documents/{id}/`
    - `DELETE /api/v1/documents/{id}/`
    - `GET /api/v1/documents/{id}/download/`
    - `POST /api/v1/documents/{id}/reprocess/`
    - `GET /api/v1/documents/{id}/permissions/`
    - `POST /api/v1/documents/{id}/permissions/`
    - `DELETE /api/v1/documents/{id}/permissions/{permission_id}/`
- `backend/apps/processing`
  - PDF extraction (`pypdf`) and plain text extraction
  - Text cleaning and chunking
  - `DocumentChunk` persistence model
  - Processing service with safe state transitions: `pending -> processing -> completed|failed`
  - Async boundary function (`enqueue_document_processing`) with documented sync fallback when worker infra is absent
- `backend/apps/common`
  - Health endpoint: `GET /api/v1/health/`
  - Basic consistent DRF exception shape (`code`, `message`, `details`)

## Security behavior implemented

- All document APIs require authentication.
- Querysets are filtered to authorized documents only (owner, administrator role, or explicit grants).
- UUID guessing does not expose private documents to unauthorized users.
- Download endpoint performs its own permission check (`owner/admin` or `download/manage` grant).
- Permission management endpoints require `owner/admin/manage` access.
- File validation includes extension allowlist (`.pdf`, `.txt`), MIME allowlist, and max size checks.
- Storage path uses generated UUID filename, not trusted raw client filename.

## Data model highlights

- `accounts.User` (custom auth user)
- `rbac.Role`, `rbac.UserRole`
- `documents.Document`
  - UUID PK, owner, title, description, file, MIME type, size, SHA-256 checksum, status, visibility, timestamps
  - composite index: `(owner, status, created_at)`
- `documents.DocumentPermission`
  - Subject is exactly one of user or role
  - permission type: `view/download/manage`
  - unique constraints prevent duplicate grants
  - indexes for common permission lookups
- `processing.DocumentChunk`
  - UUID PK, document FK, chunk index, content, token estimate, char offsets, optional page number
  - unique `(document, chunk_index)` + lookup index

## Environment variables

Set these before running in production-like environments:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`true`/`false`)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `DATABASE_URL` (PostgreSQL URL; when omitted, SQLite fallback is used)
- `CORS_ALLOWED_ORIGINS` (comma-separated frontend origins)
- `MAX_DOCUMENT_UPLOAD_SIZE` (bytes)
- `DOC_PROCESSING_ASYNC_ENABLED` (`true`/`false`; currently logs + sync fallback)
- `LOG_LEVEL`

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Run tests

```bash
cd backend
python manage.py test
```

## Implemented tests

`backend/tests/` includes coverage for:
- registration
- login + authenticated current-user access
- unauthenticated access blocked
- private document isolation between users
- owner CRUD access
- user grant behavior
- role grant behavior
- unauthorized download blocked
- invalid file rejection
- processing chunk creation
- reprocess replaces chunks without duplication
- processing failure sets `status=failed`

## Not implemented yet (explicit)

- embeddings generation
- pgvector vector columns/indexes
- semantic search retrieval API
- RAG generation pipeline
- OCR for scanned PDFs
- dedicated background worker integration (Celery/RQ/etc.)

This repository currently provides the secure ingestion/auth/RBAC/document-permission/processing foundation only.
