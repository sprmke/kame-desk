# DoctorDesk design system

Clinical, calm, trustworthy. Operational software for a Philippine private clinic, viewed for hours under fluorescent light. Not a SaaS marketing dashboard and not hospitality-styled.

**Source of truth for tokens, surfaces, and closed/open design decisions:** [`docs/architecture/design-language.md`](docs/architecture/design-language.md).

Pass/fail assertions: `.cursor/rules/anti-slop-design.mdc`. Review procedure: `.agent/skills/design-review/SKILL.md`. Historical TailAdmin extraction (do not copy from it): [`docs/architecture/design-system.md`](docs/architecture/design-system.md).

## Principles

- **Decisions, not defaults.** Every visual element has a named choice and a rejected alternative. Unspecified defaults are slop, even when tidy.
- **Clarity over decoration.** Front desk and doctors work under time pressure.
- **One layout primitive.** Dense, divider-separated rows. Cards are last resort (escalation ladder: spacing → divider → section → card).
- **Hierarchy without color.** Size, weight, and position first. A screen that collapses in grayscale has failed.
- **Domain before chrome.** Elapsed wait, identity disambiguation, and the next action beat metric chips and trend charts on operational screens.
- **Minimal copy.** `ui-minimal-copy.mdc` wins. Page descriptions that restate the title are banned (B7).

## Brand hue

**Not ratified.** Three directions were piloted on the waiting room (clinical slate/teal, institutional navy/ochre, botanical forest/sage). None was chosen. `apps/web/src/styles.css` still holds leftover TailAdmin indigo. That is a holding pattern.

Next visual pilot: **Today** (`/dashboard`). Do not pick a hue from this file.

Indigo and violet stay off the table.

## Typography

- UI: **IBM Plex Sans** via `font-sans` (loaded in `__root.tsx`).
- Mono: **IBM Plex Mono** (`font-mono`) for IDs, timestamps, audit/document preview.
- Ratio ≤ 1.25. 14px minimum for readable desktop text; 13px metadata only; inputs never below 16px.
- No weight below 400. Large text (≥24px) takes negative letter-spacing.

## Numbers

Columns, live timers, and money: `font-variant-numeric: lining-nums tabular-nums`. Financial surfaces also `slashed-zero`. Do not apply tabular figures to running prose.

## Status

Two channels minimum (shape + text). Categorical/appointment-type colors exclude red. Red is status only. A status _change_ is more than a hue swap.

## Motion

Frequency decides whether to animate at all: 100+/day = none; occasional = standard; rare = the delight budget. Route changes ≤180ms or absent. Hard ceiling 300ms. Only `transform` and `opacity`. `prefers-reduced-motion` on every animation. Tokens: `apps/web/src/lib/motion.ts` (values retune in Phase 47; new work follows these rules, not the old 300ms page tier).

## Components

shadcn/ui primitives in `apps/web/src/components/ui/`. Feature UI in `apps/web/src/features/`. Waiting-room Kanban is the reference operational surface.

### Pointer contract

Every interactive control shows `cursor: pointer` (disabled: `not-allowed`).

### Don'ts

No pastel KPI icon chips on Today. No `Stethoscope` / `Armchair` / `Bot` / `Sparkles`. No gradients, glassmorphism, confetti, glow. No card-in-card. No page-level horizontal scroll at 375px. Touch targets ≥44×44px.

## Agent prompt guide

- Review a screen: `/dd-design-review /dashboard/...` or invoke the `design-review` skill.
- New container: climb the escalation ladder; do not start with `Card`.
- New number in a column or a live timer: `lining-nums tabular-nums`.
- New motion: frequency first, then duration. `useReducedMotion()`.
- New copy: omit unless the screen is unusable without it (`ui-minimal-copy.mdc`).
