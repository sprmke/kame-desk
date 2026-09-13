#!/usr/bin/env bash
# PostToolUse: warn when new code mentions stacks explicitly out of scope for DoctorDesk.
set -e
input=$(cat)
if command -v jq >/dev/null 2>&1; then
  file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
else
  file_path=""
fi

[[ -n "$file_path" && -f "$file_path" ]] || { echo '{}'; exit 0; }

case "$file_path" in
  *.md|*.mdc|docs/*|.agent/*|.cursor/*|.claude/*|.opencode/*) echo '{}'; exit 0 ;;
esac

BANNED='Supabase|Deno edge|tRPC|Drizzle|Next\.js App Router|Prisma|bun run|kamewave'
if grep -qE "$BANNED" "$file_path" 2>/dev/null; then
  reason="Possible wrong-stack terminology in $file_path — DoctorDesk uses FastAPI + SQLAlchemy + Alembic + TanStack Start + pnpm (see docs/tech-stack.md)."
  if command -v jq >/dev/null 2>&1; then
    jq -n --arg reason "$reason" '{additional_context: $reason}'
  else
    printf '{"additional_context":"%s"}' "$reason"
  fi
else
  echo '{}'
fi
