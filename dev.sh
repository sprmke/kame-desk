#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

bash scripts/dev/free-local-ports.sh

docker compose up -d postgres redis minio mailhog

pnpm run dev:api &
API_PID=$!
pnpm run dev:worker &
WORKER_PID=$!
pnpm run dev:web &
WEB_PID=$!

trap 'kill $API_PID $WORKER_PID $WEB_PID 2>/dev/null || true' EXIT INT TERM
wait
