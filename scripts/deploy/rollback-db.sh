#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-dev}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/deploy/lib.sh"

if [[ "$TARGET" == "prod" ]] && [[ "${DESKWAVE:-}" != "deskwave" ]]; then
  echo "BLOCKED: prod rollback — unlock with deskwave in the same command"
  exit 1
fi

load_api_env
require_pg_tools

BACKUP_DIR="$ROOT/.backups/db"
LATEST="$BACKUP_DIR/${TARGET}-latest.sql.gz"
if [[ ! -f "$LATEST" ]]; then
  echo "No backup found at $LATEST — run pnpm run backup:db:${TARGET} first"
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL missing"
  exit 1
fi

PG_URL="$(database_url_to_pg "$DATABASE_URL")"
echo "rollback-db ($TARGET): restoring from $LATEST"
gunzip -c "$LATEST" | psql_from_stdin "$DATABASE_URL"
echo "rollback-db ($TARGET): restore complete"
