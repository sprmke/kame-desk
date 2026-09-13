#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-dev}"
export DEPLOY_TARGET="$TARGET"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/deploy/lib.sh"

if [[ "$TARGET" == "prod" ]] && [[ "${DESKWAVE:-}" != "deskwave" ]]; then
  echo "BLOCKED: prod web deploy — see .cursor/rules/no-prod-deploy.mdc (unlock: deskwave)"
  exit 1
fi

load_deploy_env "$TARGET"
require_deploy_var VITE_API_URL
require_deploy_var CLOUDFLARE_PAGES_PROJECT

echo "deploy-web ($TARGET): build"
(
  cd "$ROOT/apps/web"
  VITE_API_URL="$VITE_API_URL" pnpm run build
)

DIST_DIR="${DEPLOY_WEB_DIST:-$ROOT/apps/web/dist}"
if [[ ! -d "$DIST_DIR" ]]; then
  echo "deploy-web ($TARGET): build output not found at $DIST_DIR"
  exit 1
fi

BRANCH="${CLOUDFLARE_PAGES_BRANCH:-$TARGET}"
WRANGLER=(npx wrangler)
if command -v wrangler >/dev/null; then
  WRANGLER=(wrangler)
fi

echo "deploy-web ($TARGET): pages deploy (${CLOUDFLARE_PAGES_PROJECT}, branch ${BRANCH})"
"${WRANGLER[@]}" pages deploy "$DIST_DIR" \
  --project-name="$CLOUDFLARE_PAGES_PROJECT" \
  --branch="$BRANCH"

echo "deploy-web ($TARGET): done"
