# DoctorDesk (kame-desk)

Clinic management platform for independent doctors and small clinics: scheduling, live visit status, SOAP consultation records, prescriptions, billing, documents, and an AI Clinic Assistant that can execute real dashboard actions by chat instead of clicking through screens.

**Status:** Phase 0–1 complete. Monorepo scaffold, AI agent tooling, JWT auth, and local Docker stack are in place. Next: Phase 2 (onboarding wizard).

## Start here

| Doc                                                    | Purpose                                                                                         |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| [`docs/mvp.md`](./docs/mvp.md)                         | Authoritative product PRD — modules, AI assistant spec, production readiness checklist          |
| [`docs/tech-stack.md`](./docs/tech-stack.md)           | Authoritative technology choices                                                                |
| [`docs/architecture/`](./docs/architecture/)           | Monorepo structure, data model, API conventions, AI assistant spec, deployment, security        |
| [`docs/phases/README.md`](./docs/phases/README.md)     | **Multi-phase build plan** — detailed tasks per phase, in build order                           |
| [`CLAUDE.md`](./CLAUDE.md)                             | Agent context (Claude Code, and read by Cursor/OpenCode) — stack, commands, conventions, don'ts |
| [`.cursor/rules/README.md`](./.cursor/rules/README.md) | Cursor rules/skills index                                                                       |

## Quick commands

```bash
pnpm install
pnpm run setup:ai-tooling   # once, after clone
cp apps/api/.env.example apps/api/.env
pnpm run dev:docker         # Postgres+pgvector, Redis, MinIO, Mailhog
cd apps/api && uv sync --all-extras   # Python deps (first time)
pnpm run dev                # web (TanStack Start) + api (FastAPI) + worker stub
pnpm run ci:quality         # lint + type-check + build + test, matches CI
```

Full command reference: [`CLAUDE.md`](./CLAUDE.md) § Commands · run tasks: [`.vscode/tasks.json`](./.vscode/tasks.json) (Cmd/Ctrl+Shift+P → "Tasks: Run Task").

## Related repo

**kame-homes** — a separate product in this workspace (React + Vite + Supabase Edge Functions). Different stack on purpose; DoctorDesk does not inherit its backend, but its AI dashboard assistant and production-readiness practices are the reference pattern for this project's own AI Clinic Assistant. See `docs/tech-stack.md` § Related repos.
