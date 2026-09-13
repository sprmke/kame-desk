#!/usr/bin/env bash
# Drift prevention: Cursor, Claude Code, OpenCode AI tooling parity.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
VIOLATIONS=0

fail() { echo "VIOLATION: $1"; VIOLATIONS=$((VIOLATIONS + 1)); }

if [[ -d .agent/skills ]]; then
  for skill_dir in .agent/skills/*/; do
    name="$(basename "$skill_dir")"
    target_real="$(cd "$skill_dir" && pwd -P)"
    for side in cursor claude; do
      link=".${side}/skills/${name}"
      if [[ ! -L "$link" ]]; then
        fail "$link missing symlink to .agent/skills/${name}"
        continue
      fi
      link_real="$(cd "$link" && pwd -P)"
      [[ "$link_real" == "$target_real" ]] || fail "$link resolves to $link_real, expected $target_real"
    done
  done
fi

for kind in commands agents; do
  [[ -d .claude/${kind} ]] || continue
  for f in .claude/${kind}/*.md; do
    [[ -e "$f" ]] || continue
    name="$(basename "$f")"
    [[ -f ".cursor/${kind}/${name}" ]] || fail ".claude/${kind}/${name} has no .cursor/${kind}/${name}"
    [[ -f ".opencode/${kind}/${name}" ]] || fail ".claude/${kind}/${name} has no .opencode/${kind}/${name}"
  done
done

if [[ ! -L .cursor/mcp.json ]]; then
  fail ".cursor/mcp.json must symlink to ../.mcp.json"
fi

[[ -f opencode.json ]] || fail "opencode.json missing"
jq -e '.mcp.context7 and .mcp.markitdown and .mcp.playwright and .mcp.postgres' opencode.json >/dev/null 2>&1 \
  || fail "opencode.json mcp must define context7, markitdown, playwright, postgres"

[[ -f .opencode/plugins/dd-ai-tooling.ts ]] || fail ".opencode/plugins/dd-ai-tooling.ts missing"

if [[ -d .claude/commands ]]; then
  for f in .claude/commands/*.md; do
    [[ -e "$f" ]] || continue
    name="$(basename "$f")"
    [[ -e ".opencode/commands/${name}" ]] || fail ".opencode/commands/${name} missing"
  done
fi

[[ "$VIOLATIONS" -gt 0 ]] && { echo "$VIOLATIONS violation(s)"; exit 1; }
echo "OK — Cursor, Claude, and OpenCode AI tooling are in sync."
