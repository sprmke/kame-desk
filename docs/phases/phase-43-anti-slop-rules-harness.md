# Phase 43: Anti-slop rules, design-review skill, screenshot harness

**Status:** Done
**Depends on:** Phase 42
**Unlocks:** Phases 44–47 (grading as screens ship)

**Plan reference:** `docs/workflow/planned/professional-design-overhaul-anti-slop.md` §5 Workstream G

## Goal

Ship the enforcement layer before the bulk redesign: pass/fail anti-slop rules, a design-review skill and subagent, a deterministic checker with a recorded baseline, and a screenshot harness. Later phases grade against this, rather than asserting that the UI "looks better."

activity-log: N/A — docs, agent tooling, and deterministic static checks. No clinic/patient/appointment writes.

## Tasks

- [x] Write `.cursor/rules/anti-slop-design.mdc` (glob: `apps/web` TSX + `styles.css`) with the §2 pass/fail assertions
- [x] Write `.agent/skills/design-review/SKILL.md` (§2.8 procedure) and symlink via `pnpm run setup:ai-tooling`
- [x] Add `design-reviewer` subagent (`.claude/agents/`, `.cursor/agents/`, `.opencode/agents/`)
- [x] Add `/dd-design-review <route-or-diff>` and list it in `dd-help.md`
- [x] Add `scripts/dev/check-design-slop.sh` + `pnpm run check:design-slop`; ratchet against `docs/workflow/baselines/design-slop-baseline.json`; wire into `ci:quality`
- [x] Record Phase 43 checker baseline (counts after allowlisted overrides)
- [x] Rewrite `DESIGN.md` as principle-level source of truth (no TailAdmin matching)
- [x] `docs/architecture/design-language.md` exists (started in Phase 42d; keep in sync)
- [x] Demote `docs/architecture/design-system.md` to a historical audit
- [x] Update `components.mdc`, `motion.mdc`, `mobile-responsive.mdc`, and matching skills
- [x] Screenshot harness: seed login, capture listed routes at 375 / 820 / 1440 in light and dark; output to gitignored `.audit-screenshots/harness/`
- [x] Index rule/skill/subagent/command; `pnpm run check:ai-tooling-sync` clean
- [x] `pnpm run ci:quality` green

## Exit criteria

- An agent can review a route by following the skill and produce a report with rule IDs and `file:line`
- `pnpm run check:design-slop` fails CI if any mechanical rule count rises above the committed baseline
- Screenshot harness exists and is documented; it is not part of default `test:e2e` (slow, needs a seeded local app)
- Brand hue remains **unratified** (deferred to the Today visual pilot in Phase 45)

## Docs to update

`DESIGN.md`, `docs/architecture/design-language.md`, `docs/architecture/design-system.md`, `.cursor/rules/README.md`, `.claude/README.md`, `.opencode/README.md`, `CLAUDE.md`, `docs/phases/README.md`, `docs/README.md`, `docs/guides/routes/README.md` (header convention vs B7), workflow tracker.
