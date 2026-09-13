#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://doctordesk:doctordesk_local_only@127.0.0.1:5432/doctordesk}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export SECRET_KEY="${SECRET_KEY:-ci-e2e-secret-key}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://127.0.0.1:4173}"
export ENVIRONMENT="${ENVIRONMENT:-local}"
export DOCTORDESK_TESTING=1
export CI=1

cat > apps/api/.env <<EOF
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
SECRET_KEY=${SECRET_KEY}
CORS_ORIGINS=${CORS_ORIGINS}
ENVIRONMENT=${ENVIRONMENT}
WEB_BASE_URL=http://127.0.0.1:4173
S3_ENDPOINT_URL=http://127.0.0.1:9000
S3_ACCESS_KEY=doctordesk
S3_SECRET_KEY=doctordesk_local_only
S3_BUCKET=doctordesk
SMTP_HOST=127.0.0.1
SMTP_PORT=1025
SMTP_FROM=noreply@doctordesk.local
EOF

pnpm --filter @doctordesk/api migrate
cd apps/web
pnpm exec playwright install chromium --with-deps
VITE_API_URL=http://127.0.0.1:8000/api/v1 pnpm exec playwright test
