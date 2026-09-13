#!/usr/bin/env bash
set -euo pipefail
ENV="${1:-local}"
echo "db-reset-local ($ENV): drop/recreate local DB, migrate, seed"
docker compose exec -T postgres psql -U doctordesk -c "DROP DATABASE IF EXISTS doctordesk;"
docker compose exec -T postgres psql -U doctordesk -c "CREATE DATABASE doctordesk;"
pnpm --filter @doctordesk/api migrate
pnpm --filter @doctordesk/api seed
