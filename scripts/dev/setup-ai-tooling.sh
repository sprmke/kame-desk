#!/usr/bin/env bash
# One-shot post-clone AI tooling setup for DoctorDesk.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

info() { printf '→ %s\n' "$*"; }
ok() { printf '✓ %s\n' "$*"; }
warn() { printf '⚠ %s\n' "$*" >&2; }

link_relative() {
  local link="$1" target="$2"
  mkdir -p "$(dirname "$link")"
  if [[ -L "$link" ]]; then
    [[ "$(readlink "$link")" == "$target" ]] && return 0
    rm "$link"
  elif [[ -e "$link" ]]; then
    echo "ERROR: $link exists and is not a symlink"
    exit 1
  fi
  ln -s "$target" "$link"
  ok "Linked $link -> $target"
}

info "MCP config"
[[ -f .mcp.json ]] || { echo "ERROR: .mcp.json missing"; exit 1; }
link_relative ".cursor/mcp.json" "../.mcp.json"

info "Team skills (.agent/skills symlinks)"
[[ -d .agent/skills ]] || { echo "ERROR: .agent/skills missing"; exit 1; }
for skill_dir in .agent/skills/*/; do
  [[ -d "$skill_dir" ]] || continue
  name="$(basename "$skill_dir")"
  for side in cursor claude; do
    link=".${side}/skills/${name}"
    link_relative "$link" "../../.agent/skills/${name}"
  done
done

info "OpenCode command symlinks"
mkdir -p .opencode/commands .opencode/agents .opencode/plugins
for cmd in .claude/commands/*.md; do
  [[ -e "$cmd" ]] || continue
  name="$(basename "$cmd")"
  link_relative ".opencode/commands/${name}" "../../.claude/commands/${name}"
done

for agent in debugger security-auditor test-runner verifier design-reviewer; do
  [[ -f ".claude/agents/${agent}.md" ]] && link_relative ".cursor/agents/${agent}.md" "../../.claude/agents/${agent}.md" || true
done

for cmd in .claude/commands/*.md; do
  [[ -e "$cmd" ]] || continue
  name="$(basename "$cmd")"
  link_relative ".cursor/commands/${name}" "../../.claude/commands/${name}" || true
done

chmod +x .claude/hooks/*.sh .cursor/hooks/*.sh 2>/dev/null || true

info "Optional tools"
command -v markitdown-mcp >/dev/null 2>&1 && ok "markitdown-mcp on PATH" || warn "markitdown-mcp not on PATH — uv tool install markitdown-mcp"

bash "$ROOT/scripts/dev/check-ai-tooling-sync.sh"
ok "AI tooling setup complete — re-run: pnpm run setup:ai-tooling"
