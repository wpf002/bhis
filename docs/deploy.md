# BHIS Deployment Runbook

Deploys as two services — a FastAPI **backend** and an nginx-served **frontend** —
plus managed **Postgres**. Redis is optional (the rate limiter is in-memory today).
Examples use [Railway](https://railway.app) (the roadmap's choice); the same
artifacts work on Render, Fly, or any Docker host.

## Artifacts in this repo
- `backend/Dockerfile` — runs `start.sh` (migrate, then `uvicorn` on `$PORT`) as non-root.
- `backend/start.sh` — `alembic upgrade head` on every deploy (idempotent), then start.
- `backend/.env.example` — every backend setting, documented.
- `frontend/Dockerfile` — builds the SPA, serves via nginx, proxies `/api` → backend.
- `frontend/nginx.conf.template` — SPA fallback + `/api` proxy (`${BACKEND_URL}`).

## 1. Provision
1. Create a Railway project; add a **PostgreSQL** plugin. Copy its connection
   string and convert the scheme to async: `postgresql+asyncpg://…`.
2. (Optional) Add a **Redis** plugin for a future multi-worker rate limiter.

## 2. Backend service
1. New service → deploy from this repo, **root directory `/backend`** (uses `backend/Dockerfile`).
2. Set environment variables (see `backend/.env.example`). Minimum:
   - `DATABASE_URL` = the async Postgres URL
   - `SECRET_KEY` = `python -c "import secrets; print(secrets.token_urlsafe(48))"`
   - `ENVIRONMENT=production`
   - `FRONTEND_URL` = the frontend's public URL (used in email links)
   - `EMAIL_BACKEND=sendgrid`, `SENDGRID_API_KEY=…`, `EMAIL_FROM=no-reply@yourdomain`
   - `SENTRY_DSN` (optional; also uncomment `sentry-sdk` in `requirements.txt`)
3. Deploy. `start.sh` runs migrations automatically. Confirm health:
   `curl https://<backend-url>/health` → `{"status":"healthy","db":true,...}`.

## 3. Seed the question bank (one time)
`seeds/seed_questions.py` creates a fresh template each run, so run it **once**,
not on every deploy. From a one-off shell against the production DB:
```
DATABASE_URL=postgresql+asyncpg://… python seeds/seed_questions.py
```
Expect `Seeded template '…' with 60 questions`.

## 4. Frontend service
1. New service → same repo, **root directory `/frontend`** (uses `frontend/Dockerfile`).
2. Set `BACKEND_URL` to the backend's internal URL (e.g. `http://backend.railway.internal:8000`)
   so nginx proxies `/api` to it. The SPA calls relative `/api/v1`, so no CORS and
   no build-time API URL are needed.
3. Deploy and open the public URL — you should land on the BHIS login page.

## 5. Smoke test (production)
Register an admin → create a church → create + launch a survey → open the member
link in an incognito window → complete it → confirm the report renders. (This is
the same flow the backend e2e test and `docs/`-referenced smoke covers locally.)

## 6. Custom domains & TLS
Point `app.<domain>` at the frontend service and (optionally) `api.<domain>` at
the backend. Railway provisions TLS automatically. Update `FRONTEND_URL` and the
CORS `allow_origins` in `backend/app/main.py` to the real domains.

## 7. Operations
- **Backups**: enable daily automated Postgres backups (30-day retention).
- **Migrations**: every deploy runs `alembic upgrade head`; review new migrations before deploying.
- **Monitoring**: set `SENTRY_DSN` for error tracking; add uptime monitoring on `/health`.
- **PDF export** (optional): uncomment `weasyprint` in `requirements.txt` and the
  pango/cairo libs in `backend/Dockerfile`; without them, `?fmt=pdf` returns 501.

## Not yet productionized (tracked in ROADMAP.md)
Stripe billing (Phase 5), Redis-backed rate limiting for multiple workers, S3 for
PDF storage, and a background-job queue. The pilot runs fine without these.
