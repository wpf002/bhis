#!/usr/bin/env bash
# Production release + start command. Migrations are idempotent and safe to run
# on every deploy; question seeding is a one-time manual step (see docs/deploy.md)
# because seeds/seed_questions.py creates a fresh template each run.
set -euo pipefail

echo "[start] applying database migrations…"
alembic upgrade head

echo "[start] launching API on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
