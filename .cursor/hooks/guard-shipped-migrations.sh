#!/usr/bin/env bash
# Cursor preToolUse hook: never edit a shipped Alembic migration.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec "$ROOT/.claude/hooks/guard-shipped-migrations.sh"
