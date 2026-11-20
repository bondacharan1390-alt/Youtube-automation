# Phase 9 Production Readiness

This document records the validated deployment-preparation state. It does not authorize public deployment.

## Recommended Architecture

### Local and small deployment

- Frontend: Next.js production server or static-compatible hosting.
- Backend: FastAPI under a production ASGI server such as Uvicorn with one worker.
- Database: SQLite for a single application instance, backed up before and after migrations.
- Media: local persistent storage.
- Worker: same host process or a separately supervised worker.

### Multi-instance deployment

- Frontend: managed Next.js-compatible hosting.
- Backend: containerized FastAPI service with HTTPS.
- Database: PostgreSQL.
- Media: Cloudflare R2 or another S3-compatible object store.
- Workers: separate always-on worker service.
- Secrets: hosted secret manager or environment-variable injection.

SQLite is not recommended for concurrent multi-instance writes.

## Minimum Hardware

- 8 GB RAM minimum.
- Windows 11.
- 10 GB free disk minimum for generated media.
- NVIDIA GPU optional; the application must not require CUDA.
- Recommended: 16 GB RAM, 50 GB free disk, and an NVIDIA GPU with sufficient VRAM.

## Environment Requirements

- `SECRET_KEY`: required in production.
- `FERNET_KEY`: required in production.
- `APP_ENV=production`.
- `DEBUG=false`.
- `DATABASE_URL`.
- `CORS_ORIGINS`.
- YouTube OAuth values only for live integrations.
- Optional provider API keys.

Never commit an `.env` file or real credentials.

## Public Deployment Blockers

Public deployment is blocked until:

- The Next.js major-version vulnerability risk is resolved.
- Live YouTube OAuth and upload credentials are available.
- OAuth redirect URIs are verified.
- Secrets are supplied through the production environment.
- HTTPS is configured.
- SQLite/PostgreSQL backup and restore has been demonstrated.
- Media storage is persistent and backed up.
- Production monitoring and authentication events are configured.

## Operational Costs

- Development and local use: no mandatory paid service.
- Vercel or compatible frontend hosting: free tier may be available, with usage limits.
- Backend hosting: free tiers may be unavailable for persistent workers.
- PostgreSQL: paid or hosted free-tier options may impose limits.
- Object storage: R2 or alternatives may incur usage or egress charges.
- YouTube API: quota limits apply.
- Cloud LLM providers: usage costs may apply.

## Deployment and Recovery

Run migrations before application startup:

```powershell
cd backend
alembic upgrade head
```

Create a SQLite backup:

```powershell
cd backend
powershell -ExecutionPolicy Bypass -File scripts\backup_sqlite.ps1
```

Restore a backup only after stopping the application and worker, then verify database integrity and
the application startup against the restored database.
