#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "→ check:filenames"
bash scripts/dev/check-filename-conventions.sh

echo "→ check:design-slop"
bash scripts/dev/check-design-slop.sh

echo "→ lint"
pnpm run lint

echo "→ type-check"
pnpm run type-check

echo "→ build"
pnpm run build

if [[ -d apps/api/tests ]]; then
  echo "→ pytest"
  pnpm run test:api
fi

if [[ -d apps/web/src ]] && grep -q '"test"' apps/web/package.json 2>/dev/null; then
  echo "→ vitest"
  pnpm run test:web
fi

echo "OK — ci:quality gate passed"
