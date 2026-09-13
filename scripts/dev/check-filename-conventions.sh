#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
VIOLATIONS=0

fail() { echo "FILENAME: $1"; VIOLATIONS=$((VIOLATIONS + 1)); }

while IFS= read -r -d '' f; do
  base="$(basename "$f")"
  case "$base" in
    __init__.py|env.py|conftest.py) continue ;;
  esac
  if [[ ! "$base" =~ ^[a-z0-9_]+\.py$ ]]; then
    fail "$f (Python modules must be snake_case.py)"
  fi
done < <(find apps/api/app apps/api/tests -name '*.py' -print0 2>/dev/null)

while IFS= read -r -d '' f; do
  base="$(basename "$f" .tsx)"
  [[ "$f" == */components/ui/* ]] && continue
  [[ "$f" == */routes/* ]] && continue
  if [[ "$f" == *.tsx ]] && [[ ! "$base" =~ ^[A-Z] ]]; then
    fail "$f (feature components must be PascalCase.tsx)"
  fi
done < <(find apps/web/src/features apps/web/src/components -name '*.tsx' -print0 2>/dev/null)

[[ "$VIOLATIONS" -gt 0 ]] && exit 1
echo "OK — filename conventions"
