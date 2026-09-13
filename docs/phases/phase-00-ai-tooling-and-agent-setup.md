# Phase 0: AI tooling & agent setup

**Status:** Done
**Depends on:** Nothing
**Unlocks:** Phase 1 (every later phase is executed by an AI agent using this tooling)

## Goal

Stand up the same class of AI-agent tooling that already exists in the sibling `kame-homes` repo — `CLAUDE.md`, Cursor rules/skills, Claude Code agents/commands/hooks, OpenCode mirror, MCP servers, and the scripts that keep them in sync — **adapted to DoctorDesk's own stack** (FastAPI/Python + TanStack Start, not Deno/Supabase). This is infrastructure for _how_ every later phase gets built correctly, not product scope.

This phase produces no application code. Its output is entirely `.md`/`.mdc`/config/script files that every future agent session (Claude Code, Cursor, OpenCode) reads automatically.

## Why before Phase 1

Every phase from here on is executed by an AI coding agent against this repo. Without domain rules (`appointment-workflow.mdc`, `ai-assistant-safety.mdc`, `phi-data-safety.mdc`, `fastapi-conventions.mdc`, `tanstack-start-conventions.mdc`), naming conventions, a documentation-maintenance skill, and a no-prod-deploy guard, an agent building Phase 1+ has no guardrails and no shared vocabulary — the same mistake `kame-homes` avoided by building this layer first.

## What already exists (do not redo — extend instead)

- [x] `CLAUDE.md` — full agent context (what this is, commands, architecture, conventions, docs-sync table, don'ts). Already references files this phase must still create (`docs/phases/*`, `docs/architecture/*`, several `.mdc` rules) — keep it accurate as those land.
- [x] `.cursor/rules/ai-usage.mdc` — session hygiene, model routing, subagent policy.
- [x] `.cursor/rules/documentation-maintenance.mdc` — docs-sync table.
- [x] `.cursor/rules/git-commits.mdc` — no AI-tool attribution in commits.
- [x] `.cursor/rules/human-copy.mdc` — copy tone/banned punctuation.
- [x] `.cursor/rules/project-context.mdc` — quick-reference stack + where-to-edit table.
- [x] `.cursor/rules/route-guides.mdc` — route guide maintenance (references `docs/guides/routes/`, not yet created).
- [x] `.cursor/rules/ui-minimal-copy.mdc` — copy volume policy.
- [x] `package.json` — full script surface already defined (`dev`, `dev:docker`, `lint`, `type-check`, `build`, `test`, `db:*`, `deploy:*`, `backup:*`, `rollback:*`, `env:status`, `setup:ai-tooling`, `check:ai-tooling-sync`, `ci:quality`) — **the scripts exist as names, the underlying files under `scripts/` do not yet.** This phase and Phase 1 split responsibility: this phase creates the AI-tooling-related scripts (`setup:ai-tooling`, `check:ai-tooling-sync`, `check:filenames`, `ci:quality`); Phase 1 creates the app/infra ones (`db:*`, `deploy:*`, `backup:*`, `rollback:*`, `env:status`).
- [x] `turbo.json`, `pnpm-workspace.yaml`, `docker-compose.yml` (Postgres+pgvector, Redis, MinIO, Mailhog) — infra config, owned by Phase 1, listed here only for context.
- [x] Root `README.md`, `docs/README.md`, `docs/mvp.md`, `docs/tech-stack.md`.

## Tasks

### 1. Finish the Cursor rules set (`.cursor/rules/`)

Add the domain rules `CLAUDE.md` and `project-context.mdc` already reference but that don't exist yet. Port structure/tone from the matching `kame-homes` rule where one exists; write fresh where the domain has no kame-homes equivalent.

| Rule file                        | Scope                                                                                                                                                                                                        | kame-homes equivalent to adapt                                                                                               |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `appointment-workflow.mdc`       | Appointment status + visit status state machines, transitions, side effects (reminders, calendar, audit log), exclusion-constraint invariant                                                                 | `booking-workflow.mdc`                                                                                                       |
| `ai-assistant-safety.mdc`        | Tiered risk model, RBAC re-check, grounding check, external-send escalation, clinical-write escalation, never-build list                                                                                     | `ai-assistant-parity.mdc` (parity concept) + `admin-auth.mdc` (RBAC re-check pattern) — mostly new, mvp.md §9 is the spec    |
| `fastapi-conventions.mdc`        | Router/service/schema layering, Pydantic v2 schema naming (`XCreate`/`XRead`/`XUpdate`), dependency injection for auth/clinic-scope, async SQLAlchemy session handling, error response shape                 | New (no Deno equivalent)                                                                                                     |
| `tanstack-start-conventions.mdc` | File-route conventions, loader vs. TanStack Query split, no server-function business logic, RHF+Zod form pattern                                                                                             | New (no Next.js/Vite-SPA equivalent — kame-homes is a plain Vite SPA, this repo uses TanStack Start)                         |
| `phi-data-safety.mdc`            | What counts as PHI in this product, logging rules, Sentry scrubbing rules, AI-prompt minimization rules                                                                                                      | New (kame-homes has no clinical data; closest spirit is its guest-PII handling in `security.mdc`)                            |
| `migrations.mdc`                 | Alembic-only, never edit a shipped migration, autogenerate review checklist                                                                                                                                  | `supabase-platform.mdc` (concept only — different tool)                                                                      |
| `naming-conventions.mdc`         | Python `snake_case.py`/`PascalCase` models/Pydantic schemas; TS `PascalCase.tsx`/`useX.ts`/`camelCase.ts`; TanStack Router file-route conventions                                                            | `naming-conventions.mdc`                                                                                                     |
| `mobile-responsive.mdc`          | 375–1024px+, 44×44px touch targets, tablet-first front desk                                                                                                                                                  | `mobile-responsive.mdc`                                                                                                      |
| `no-prod-deploy.mdc`             | Blocked commands (`deploy:api:prod`, `deploy:web:prod`, `migrate:prod`, any write against prod Neon `DATABASE_URL`), unlock word **`deskwave`** (already named in `CLAUDE.md` § Don'ts — keep the same word) | `no-prod-deploy.mdc` (adapt unlock word: kame-homes uses `kamewave`, this repo already commits to `deskwave` in `CLAUDE.md`) |
| `plan-mode.mdc`                  | Plan-mode output path (`docs/workflow/planned/<slug>.md`, no date prefix) + index row                                                                                                                        | `plan-mode.mdc`                                                                                                              |
| `superpowers-opt-in.mdc`         | Same opt-in-only stance if the Superpowers plugin is enabled for this repo                                                                                                                                   | `superpowers-opt-in.mdc`                                                                                                     |
| `security.mdc`                   | Consolidated security invariants pointer (links to `phi-data-safety.mdc`, `ai-assistant-safety.mdc`, RBAC table)                                                                                             | `security.mdc`                                                                                                               |
| `self-review.mdc`                | Pre-done checklist an agent runs on itself before declaring a task complete                                                                                                                                  | `self-review.mdc`                                                                                                            |
| `workflow-docs.mdc`              | Lifecycle for `docs/workflow/{intake,planned,in-progress,done,wont-do}/` if this repo adopts the same workflow-doc pattern                                                                                   | `workflow-docs.mdc`                                                                                                          |
| `README.md` (rules index)        | One-line-per-rule index, mirrors `.cursor/rules/README.md` in kame-homes                                                                                                                                     | `.cursor/rules/README.md`                                                                                                    |

Do **not** port `booking-workflow.mdc`'s guest/property/parking multi-tenancy content verbatim — DoctorDesk's tenancy unit is `clinic`, not `organization/property/parking`; rewrite for clinic scoping.

### 2. Build `.agent/skills/` (canonical) + symlink into `.cursor/skills/` and `.claude/skills/`

Mirror kame-homes' canonical-skill pattern: skills live once in `.agent/skills/<name>/SKILL.md`, symlinked into both tool-specific directories so Cursor and Claude Code see the same content without duplication.

**Skills to port and adapt (rename/reshape for this domain):**

| New skill                                                                                                                                                                                                                           | Adapted from (kame-homes)   | Adaptation notes                                                                                                                                                                                                                                          |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `documentation-maintenance`                                                                                                                                                                                                         | `documentation-maintenance` | Retarget doc paths to `docs/mvp.md`, `docs/architecture/*`, `docs/guides/routes/*`, `docs/phases/*`                                                                                                                                                       |
| `route-guides`                                                                                                                                                                                                                      | `route-guides`              | Retarget to TanStack Router file routes under `apps/web/src/routes/`                                                                                                                                                                                      |
| `human-copy`                                                                                                                                                                                                                        | `human-copy`                | Same rules, clinical/billing register examples instead of hospitality                                                                                                                                                                                     |
| `minimal-ui-copy`                                                                                                                                                                                                                   | `minimal-ui-copy`           | Same                                                                                                                                                                                                                                                      |
| `docs-first`                                                                                                                                                                                                                        | `docs-first`                | Same habit, DoctorDesk doc set                                                                                                                                                                                                                            |
| `audit-logging`                                                                                                                                                                                                                     | `audit-logging`             | Retarget to `activity_log` table (§6.11), FastAPI service-layer emission instead of Deno edge `_shared/activityLog.ts`                                                                                                                                    |
| `appointment-workflow`                                                                                                                                                                                                              | `booking-workflow`          | Two-lifecycle model (appointment status + visit status), exclusion constraint, WebSocket events instead of a single flat booking status enum                                                                                                              |
| `mobile-responsive`                                                                                                                                                                                                                 | `mobile-responsive`         | Same, tablet-at-front-desk framing                                                                                                                                                                                                                        |
| `accessibility`                                                                                                                                                                                                                     | `accessibility`             | Same                                                                                                                                                                                                                                                      |
| `forms`                                                                                                                                                                                                                             | `forms`                     | RHF + Zod, same pattern, different schemas                                                                                                                                                                                                                |
| `notifications`                                                                                                                                                                                                                     | `notifications`             | Retarget to Resend email + Twilio SMS reminders/recalls instead of guest notifications                                                                                                                                                                    |
| `tanstack-query`                                                                                                                                                                                                                    | `tanstack-query`            | Same library, same patterns                                                                                                                                                                                                                               |
| `tanstack-table`                                                                                                                                                                                                                    | `tanstack-table`            | Same, used for patients/appointments/billing lists                                                                                                                                                                                                        |
| `component-generator`                                                                                                                                                                                                               | `component-generator`       | Retarget scaffolds to `apps/web/src/features/{module}/components/`                                                                                                                                                                                        |
| `admin-dashboard`                                                                                                                                                                                                                   | `admin-dashboard`           | Retarget to the clinic staff dashboard                                                                                                                                                                                                                    |
| `github-issues`                                                                                                                                                                                                                     | `github-issues`             | Same                                                                                                                                                                                                                                                      |
| `workflow` / `workflow-intake-scratchpads`                                                                                                                                                                                          | same                        | Only if this repo adopts the intake/planned/in-progress/done workflow-doc pattern (recommend yes, for consistency with kame-homes)                                                                                                                        |
| `self-review`                                                                                                                                                                                                                       | `self-review`               | Same                                                                                                                                                                                                                                                      |
| `superpowers`                                                                                                                                                                                                                       | `superpowers`               | Same opt-in shape, update save paths                                                                                                                                                                                                                      |
| `fix-migration-issues`                                                                                                                                                                                                              | `fix-migration-issues`      | Rewrite entirely for Alembic (autogenerate diff review, downgrade path, never-edit-shipped rule) instead of Supabase CLI                                                                                                                                  |
| `emails`                                                                                                                                                                                                                            | `emails`                    | Retarget to Resend templates for reminders/confirmations/recalls                                                                                                                                                                                          |
| `playwright-cli`                                                                                                                                                                                                                    | `playwright-cli`            | Same, E2E specs land later (Phase 3+)                                                                                                                                                                                                                     |
| `competitive-ux-research`                                                                                                                                                                                                           | `competitive-ux-research`   | Same trigger conditions                                                                                                                                                                                                                                   |
| `design` / `design-system` / `brand` / `high-end-visual-design` / `ui-styling` / `ui-ux-pro-max` / `frontend-design` / `banner-design` / `slides` / `image-to-code` / `stitch-design-taste` / `design-taste-frontend` / `design-md` | same names                  | Port as-is; DoctorDesk needs its own brand/DESIGN.md content (clinical, trustworthy, calm — not hospitality-styled)                                                                                                                                       |
| `redesign-existing-projects`                                                                                                                                                                                                        | same                        | Same                                                                                                                                                                                                                                                      |
| `multi-tenancy` → **`clinic-scoping`**                                                                                                                                                                                              | `multi-tenancy`             | Rewrite for the simpler one-level tenancy unit (`clinic_id` on every table) vs. kame-homes' org/property/parking three-level model                                                                                                                        |
| `plans-and-permissions` → **`rbac-and-audit`** (merge concept)                                                                                                                                                                      | `plans-and-permissions`     | DoctorDesk MVP has no subscription-tier gating (not in `mvp.md`) — drop the "Plans" half, keep and rename the RBAC-decision habit around the fixed `owner/admin/doctor/reception` role matrix (§6.11); do not invent a Plans system that isn't in the PRD |
| `bookings-table` → **`appointments-table`**                                                                                                                                                                                         | `bookings-table`            | Retarget columns/status colors to appointment + visit status                                                                                                                                                                                              |
| `property-dashboard-qa` → **`clinic-dashboard-qa`**                                                                                                                                                                                 | `property-dashboard-qa`     | Retarget checklist to clinic dashboard surfaces                                                                                                                                                                                                           |
| `supabase-auth` → **`fastapi-jwt-auth`**                                                                                                                                                                                            | `supabase-auth`             | Full rewrite: FastAPI JWT access/refresh issuance, dependency-injection auth guards, clinic-scope resolution — no Supabase concepts apply                                                                                                                 |
| `supabase-stack` → **`fastapi-stack`**                                                                                                                                                                                              | `supabase-stack`            | Full rewrite: FastAPI + SQLAlchemy 2 async + Alembic + ARQ + uvicorn conventions                                                                                                                                                                          |
| `impeccable`                                                                                                                                                                                                                        | `impeccable`                | Keep if the global Impeccable tool config applies to this repo too                                                                                                                                                                                        |

**New skills with no kame-homes equivalent (write from scratch, spec source is `mvp.md`):**

- `soap-notes` — versioned chart writes, never-overwrite-in-place rule, specialty template shape (§6.5, §7.8, §7.9)
- `prescriptions` — Rx line-item shape, allergy/interaction check call order, PDF generation, PRC license auto-fill (§6.6, §8.6)
- `billing-invoicing` — invoice/line-item/payment shape, receipt numbering, HMO claim notes (§6.7)
- `pdf-generation` — shared pattern for Rx/certificate/receipt/SOAP-note PDF rendering + storage in R2 (§6.6, §6.7, §6.8)
- `ai-clinic-assistant` — tool catalog conventions, tier classification rules, confirm-card UX, `ChatBlock`-equivalent rendering (§9 in full — this is the most important new skill, mirror the rigor of `booking-workflow` in kame-homes)
- `pgvector-chart-search` — embedding generation trigger (ARQ job on SOAP save), query pattern, grounding-to-real-chart-version rule (§8.3)
- `arq-background-jobs` — job definition conventions, retry/idempotency rules, what belongs in a worker vs. a request handler
- `alembic-migrations` — merge conflict resolution, autogenerate review, `btree_gist` exclusion constraint authoring (double-booking prevention)
- `waiting-room-realtime` — WebSocket event shape, polling-degradation fallback (§10 Reliability)
- `recurring-appointments` — `rrule` expansion via ARQ, edit-this-vs-series semantics

### 3. Claude Code layer (`.claude/`)

- [ ] `.claude/README.md` — index mirroring `kame-homes/.claude/README.md`'s structure (agents, commands, hooks, skills, MCP)
- [ ] `.claude/settings.json` — hook registrations
- [ ] `.claude/agents/`:
  - `debugger.md` — port as-is (generic)
  - `security-auditor.md` — retarget triggers to: JWT auth flow, RBAC checks, AI assistant tool calls, PHI handling, prescription/billing writes
  - `test-runner.md` — retarget commands to `pnpm run lint / type-check / build` + `pytest` (once tests exist)
  - `verifier.md` — port as-is (generic)
- [ ] `.claude/commands/` — `/dd-*` teammate helpers mirroring kame-homes' `/kh-*` set: `dd-help.md`, `dd-start-work.md`, `dd-submit-for-review.md`, `dd-check-before-pr.md`, `dd-pull-new-changes.md`, `dd-create-new-ticket.md`, `dd-start-app.md`, plus repo-agnostic ones ported as-is: `github-issue.md`, `fix-merge-conflicts.md`, `self-review.md`, `workflow-start.md`, `workflow-done.md`, `workflow-sync-scratchpads.md`, `workflow-wont-do.md`, and the Superpowers trio (`superpowers-brainstorm.md`, `superpowers-plan.md`, `superpowers-debug.md`, `superpowers-execute.md`) if Superpowers is adopted here.
- [ ] `.claude/hooks/`:
  - `guard-shell.sh` — block `deploy:api:prod`, `deploy:web:prod`, `migrate:prod`, and any write against a prod `DATABASE_URL`/R2 bucket unless **`deskwave`** appears in the command string (mirrors kame-homes' `guard-shell.sh` + `no-prod-deploy.mdc`)
  - `guard-shipped-migrations.sh` — block edits to files under `apps/api/migrations/versions/` that already exist in git history
  - `format-edited-file.sh` — run `ruff format`/`prettier` on save for the edited file's language
  - `session-docs-sync-reminder.sh` — remind on `PostToolUse` for edits under `apps/web/` or `apps/api/app/` to check `documentation-maintenance`/`route-guides`
  - `session-ai-tooling-sync.sh` — verify Cursor/Claude/OpenCode tooling trees stay in sync (mirrors `check:ai-tooling-sync`)
  - `check-stack-terminology.sh` — flag stale mentions of Supabase/Deno/tRPC/Drizzle/Next.js/Bun in new code (this repo's actual "wrong stack" list, per `docs/tech-stack.md` § Explicitly out of scope)
  - `session-superpowers-opt-in.sh` / `superpowers-lean-mode.sh` / `superpowers-lean-cleanup.sh` / `guard-superpowers-subagents.sh` — only if Superpowers is adopted

### 4. OpenCode layer (`.opencode/`)

- [ ] `.opencode/README.md`
- [ ] `.opencode/agents/` — same four agents as Claude Code, OpenCode-flavored frontmatter
- [ ] `.opencode/commands/` — mirror `.claude/commands/` (`/dd-*` + generic set)
- [ ] `.opencode/plugins/dd-ai-tooling.ts` — port `kame-homes/.opencode/plugins/gfm-ai-tooling.ts`'s hook logic (format-on-save, doc-sync reminder, prod-deploy guard) to this repo's stack
- [ ] root `opencode.json`

### 5. MCP servers (`.mcp.json`)

| Server       | Purpose                                                                                                           | Notes                                                                                                                                       |
| ------------ | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `context7`   | Current docs for FastAPI, SQLAlchemy 2, Alembic, TanStack Start/Router/Query, PydanticAI — APIs move fast         | Same as kame-homes                                                                                                                          |
| `markitdown` | Convert PDF/Office attachments (lab results, HMO letters) before reading into context                             | Same as kame-homes                                                                                                                          |
| `playwright` | E2E-adjacent exploratory browser sessions                                                                         | Same as kame-homes                                                                                                                          |
| `postgres`   | **Local dev DB only** — schema/data inspection against the Docker Compose Postgres, never a hosted `DATABASE_URL` | New (kame-homes doesn't need this the same way since Supabase CLI covers it); wire connection string from `apps/api/.env` local values only |

### 6. Scripts this phase owns (`scripts/dev/`)

These are the `package.json` script targets that are about **tooling and quality gates**, not app runtime — the rest (`db:*`, `deploy:*`, `backup:*`, `rollback:*`, `env:status`, `dev:docker`) belong to Phase 1 because they require the app/infra to exist first.

- [ ] `scripts/dev/setup-ai-tooling.sh` — one-time post-clone setup: verifies/creates symlinks from `.agent/skills/*` into `.cursor/skills/` and `.claude/skills/`, checks required CLI tools, prints next steps
- [ ] `scripts/dev/check-ai-tooling-sync.sh` — CI-safe check that `.cursor/`, `.claude/`, `.opencode/` trees haven't drifted (same rule set exists in at least two places, same skill content in all three)
- [ ] `scripts/dev/check-filename-conventions.sh` — enforce naming-conventions.mdc mechanically (fails CI on a `camelCase.py` file, a `snake_case.tsx` file, etc.)
- [ ] `scripts/dev/ci-quality-gate.sh` — the single script CI and pre-PR checks both call: lint + type-check + build + `check:filenames` (+ tests once they exist)

## Data model

None — this phase touches no database schema.

## API endpoints

None — this phase touches no application code.

## Edge cases & decisions to lock before moving on

- **Unlock word for prod-deploy guard**: `CLAUDE.md` already commits to **`deskwave`** — use it consistently across `no-prod-deploy.mdc`, `guard-shell.sh`, and the OpenCode plugin. Do not introduce a second word.
- **Superpowers adoption**: decide once, here, whether this repo adopts the opt-in Superpowers workflow at all. If yes, port `superpowers-opt-in.mdc` + the skill + commands + lean-mode hooks verbatim in shape. If no, skip that whole column in the tables above and remove the mention from `CLAUDE.md`.
- **Workflow-doc lifecycle** (`docs/workflow/{intake,planned,in-progress,done,wont-do}/`): decide once whether this repo tracks in-flight work the same way kame-homes does. Recommended: yes, for consistency, but confirm before creating the skill/rule pair.
- Do not port kame-homes' `plans-and-permissions.mdc` concept literally — `mvp.md` has no subscription-tier feature-gating. If a future phase introduces pricing tiers, that's a `mvp.md` scope change first, then a new rule — not something to speculatively build now.

## Testing

Not applicable — no application code. Verification is: `pnpm run check:ai-tooling-sync` passes, and a fresh agent session in Cursor/Claude Code/OpenCode can each read `CLAUDE.md` + the rules and correctly answer "what stack does this repo use" and "what's the unlock word for prod deploys" without being told.

## Docs to update in this phase

- `CLAUDE.md` — remove/adjust any reference to a file this phase decided _not_ to create (e.g. if Superpowers is declined)
- `.cursor/rules/README.md` — new index, one line per rule
- `.claude/README.md`, `.opencode/README.md` — new indexes
- `docs/README.md` — add a row linking to `docs/phases/README.md` and `docs/architecture/` (done in this planning pass, see repo root)

## Exit criteria

- [ ] Every rule file `CLAUDE.md`/`project-context.mdc` references exists under `.cursor/rules/`
- [ ] `.agent/skills/` populated, symlinked correctly into `.cursor/skills/` and `.claude/skills/`
- [ ] `.claude/` and `.opencode/` trees both complete and structurally identical (same agents, same command set, hooks doing the equivalent thing per-tool)
- [ ] `.mcp.json` configured with all four servers, `postgres` pointed at local Docker Compose only
- [ ] `pnpm run setup:ai-tooling` and `pnpm run check:ai-tooling-sync` both exist and pass
- [ ] A fresh agent session can correctly state the unlock word, the doc-sync rule, and the AI assistant's three-tier risk model from context alone
