# Codex instructions — Kame Desk

Read CLAUDE.md before work; it is this repository’s maintained project context, architecture and workflow policy. Read docs/tech-stack.md for tooling decisions. This project uses pnpm, React/TanStack Start, FastAPI and SQLAlchemy; it does not inherit Homes’ Supabase/Deno stack. Use the packageManager version in package.json and the scripts documented in CLAUDE.md. Preserve patient privacy and existing changes.

## Codex compatibility

Before working, read [.codex/README.md](.codex/README.md). It lists this project’s always-on Cursor rules and scoped rules to read for the affected files. Codex skills are discovered in `.agents/skills`; specialist definitions are in `.codex/agents`. Existing Cursor/Claude model aliases are not Codex model settings. Use available Codex tools and preserve project-specific architecture and authorization rules.

Superpowers workflows and subagent delegation remain opt-in; do not start them automatically. Run `python3 .codex/sync.py` after changing project skills, commands or agent definitions. Review/trust hooks through Codex before relying on their enforcement. This repository setup is independent of the hourly job-search task in the personal chat.

<!-- global-agent-skills -->

## Global agent skills

This machine has 159 shared skills in `~/.agents/skill-library` (Claude Code, Cursor,
Codex and OpenCode all read them). Only five behaviour skills are always visible.
For anything else, open `~/.agents/skill-library/agent-skills-index/SKILL.md`, find the
skill that fits, then read `~/.agents/skill-library/<skill>/SKILL.md`.
Manage with `~/.agents/bin/agent-stack.sh`. Repo skills and rules always win.
