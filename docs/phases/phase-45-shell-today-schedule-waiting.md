# Phase 45: Shell, entry, Today, Schedule, Waiting room

**Status:** Done
**Depends on:** Phase 44
**Unlocks:** Phase 47 (with 46)

**Plan reference:** `docs/workflow/planned/professional-design-overhaul-anti-slop.md` §4 Workstream D1–D4, F

## Goal

Redesign first-run and day-of operations screens. `/` is not a marketing page; it redirects. Today is the day-of board (what to do now), not a KPI dashboard. Brand hue stays unratified; Today is the visual-pilot surface for a later palette pass, not a place to pick teal/navy/forest from adjectives.

activity-log: N/A — presentation layer.

## Tasks

### D1 — Entry

- [x] `/` redirects signed-in users to `/dashboard` and others to `/login`. Delete the placeholder landing.
- [x] `AuthLayout` / login / register: composed layout, not a centered `max-w-sm` bordered card (B8). Product mark already shipped in Phase 44.

### D2 — Today

- [x] KPI strip is compact numbers, not pastel icon chips (Phase 44).
- [x] Schedule and queue dominate the fold. Same appointment must not render in both panels.
- [x] Collapse the four identical attention cards into one prioritized list with typed rows, `+N more`, and deep links.
- [x] Move the 14-day trend chart off Today (Insights already has reports).

### D3 — Schedule

- [x] Calendar default remains available; doctor colors use categorical tokens (Phase 44). Craft pass on event chips as time allows.

### D4 — Waiting room

- [x] Kanban, elapsed wait, doctor filter, arrival chime (Phase 42).
- [x] Identity block on queue cards where the row still shows a bare name.

### F — Copy

- [x] Drop PageHeader descriptions on screens touched here if they restate the title.

### Enforcement

- [x] Route guides for `/`, `/login`, `/dashboard`, calendar, waiting room.
- [x] `pnpm run check:design-slop` must not rise; `pnpm run ci:quality` green.
- [x] Brand hue still **unratified**.

## Exit criteria

- `/` never shows a blank mark + two buttons
- Today answers "what do I do now" in the fold
- Same patient is not duplicated across Today and Queue
- Attention items are one list, not four identical cards
- `ci:quality` green
