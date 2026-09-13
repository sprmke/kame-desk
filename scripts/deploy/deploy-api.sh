#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-dev}"
export DEPLOY_TARGET="$TARGET"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/deploy/lib.sh"

if [[ "$TARGET" == "prod" ]] && [[ "${DESKWAVE:-}" != "deskwave" ]]; then
  echo "BLOCKED: prod API deploy — see .cursor/rules/no-prod-deploy.mdc (unlock: deskwave)"
  exit 1
fi

load_deploy_env "$TARGET"
require_deploy_var DEPLOY_API_SSH
require_deploy_var DEPLOY_API_PATH

echo "deploy-api ($TARGET): pre-deploy backup"
bash "$ROOT/scripts/deploy/backup-db.sh" "$TARGET"

echo "deploy-api ($TARGET): sync to ${DEPLOY_API_SSH}:${DEPLOY_API_PATH}"
rsync -az --delete \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  --exclude ".ruff_cache" \
  "$ROOT/apps/api/" "${DEPLOY_API_SSH}:${DEPLOY_API_PATH}/apps/api/"
rsync -az \
  "$ROOT/package.json" \
  "$ROOT/pnpm-lock.yaml" \
  "$ROOT/pnpm-workspace.yaml" \
  "${DEPLOY_API_SSH}:${DEPLOY_API_PATH}/"

REMOTE_SERVICES="${DEPLOY_API_SERVICES:-doctordesk-api doctordesk-worker}"
ssh "$DEPLOY_API_SSH" "set -euo pipefail
  cd '${DEPLOY_API_PATH}/apps/api'
  uv sync --frozen
  uv run alembic upgrade head
  sudo systemctl restart ${REMOTE_SERVICES}
"

echo "deploy-api ($TARGET): done"
