#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-dev}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/deploy/lib.sh"

if [[ "$TARGET" == "prod" ]] && [[ "${DESKWAVE:-}" != "deskwave" ]]; then
  echo "BLOCKED: prod backup — unlock with deskwave in the same command"
  exit 1
fi

load_api_env
require_pg_tools

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL missing — set apps/api/.env or export DATABASE_URL"
  exit 1
fi

BACKUP_DIR="$ROOT/.backups/db"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_DIR/doctordesk-${TARGET}-${STAMP}.sql.gz"
PG_URL="$(database_url_to_pg "$DATABASE_URL")"

pg_dump_to_stdout "$DATABASE_URL" | gzip > "$OUT"
ln -sfn "$(basename "$OUT")" "$BACKUP_DIR/${TARGET}-latest.sql.gz"
echo "backup-db ($TARGET): wrote $OUT"
