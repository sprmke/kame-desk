#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-dev}"
export DEPLOY_TARGET="$TARGET"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/deploy/lib.sh"

if [[ "$TARGET" == "prod" ]] && [[ "${DESKWAVE:-}" != "deskwave" ]]; then
  echo "BLOCKED: remote migrate prod — unlock: deskwave"
  exit 1
fi

load_deploy_env "$TARGET"
REMOTE_URL="${REMOTE_DATABASE_URL:-${DATABASE_URL:-}}"
if [[ -z "$REMOTE_URL" ]]; then
  echo "migrate-remote ($TARGET): set REMOTE_DATABASE_URL or DATABASE_URL"
  exit 1
fi

echo "migrate-remote ($TARGET): alembic upgrade head"
(
  cd "$ROOT/apps/api"
  DATABASE_URL="$REMOTE_URL" uv run alembic upgrade head
)
