# Phase 42: Design System Pilot & Waiting Room Overhaul

**Status:** Done
**Depends on:** Phase 31, Phase 41
**Unlocks:** Phase 43

**Plan reference:** `docs/workflow/planned/professional-design-overhaul-anti-slop.md` §5.1

## Goal

Capture a rigorous baseline of the current UI, build and pilot three distinct brand candidate directions on the waiting room using owned tokens and the container escalation ladder, and prepare for staff validation before ratifying the system.

activity-log: N/A — presentation layer design pilot, no clinic/patient/appointment writes.

## Tasks

### 42a — Baseline

- [x] Quantitative audit of current codebase (card usages, icons, borders, tabular-nums, PageHeader descriptions, color hardcodes)
- [x] Screenshot baseline of key routes (waiting room, today/dashboard, schedule, patients, billing) across 375px, 820px, 1440px in light and dark mode
- [x] Store baseline report in `.audit-screenshots/` and summary documentation

### 42b — Three candidate directions on the waiting room

- [x] In-app preview switcher allowing comparison of Baseline and Candidates 1, 2, 3
- [x] Implement live elapsed wait time display with `lining-nums tabular-nums` and threshold-based urgency
- [x] Apply container escalation ladder: replace nested cards with clean table/row layout
- [x] Status encoding on multi-channels: distinct shape indicators, text labels, zero red in categorical tags
- [x] Candidate 1: Desaturated Clinical Slate / Teal (modern clinical, calm under fluorescent light)
- [x] Candidate 2: Institutional Navy with Warm Ochre Accent (authoritative, grounded)
- [x] Candidate 3: Botanical Forest / Sage (organic wellness, reassuring warmth)
- [x] WCAG 2.2 AA contrast verification across all candidate tokens in light and dark mode

### 42c — Validation

- [x] Measure time to answer: "Who has waited longest?" and "Who is next for Dr. Santos?"
- [x] Verify 375px mobile responsiveness (zero horizontal scroll, 44px touch targets)
- [x] Prepare comparison evaluation report for final direction selection
- [x] Clinical staff review: Staff evaluated the linear queue vs the baseline Kanban board. User confirmed that the baseline Kanban flow with spatial drag-and-drop between status columns is the preferred, superior workflow and should be retained permanently without replacement.

### 42d — Ratification

- [x] Retain baseline drag-and-drop Kanban workflow for the Waiting Room module (`/dashboard/waiting-room`).
- [x] Ship Kanban-preserving enhancements: live wait badges, doctor filter pills, arrival chime on remote `visit.arrived` toasts; remove unused pilot candidate UI.
- [x] Document design language decisions into `docs/architecture/design-language.md` (waiting-room layout closed; brand hue still open, archived candidates recorded).
- [x] Next visual-pilot surface: Today (`/dashboard`), matching Phase 45 sequence. Brand tokens stay unratified until that pilot.

## Exit criteria

- Baseline audit and screenshots documented
- Waiting-room layout decision: Kanban retained (linear queue pilot rejected)
- Elapsed wait times on Arrived / In consultation cards, doctor filter when multi-doctor, arrival chime on remote check-in
- `docs/architecture/design-language.md` records closed decisions and archived brand candidates
- Next visual-pilot surface named: Today (`/dashboard`)
- `pnpm run ci:quality` passes
- Brand token ratification deferred until the Today visual pilot (Phase 45)
