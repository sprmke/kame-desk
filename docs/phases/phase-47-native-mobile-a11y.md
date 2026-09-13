# Phase 47: Native mobile feel + accessibility gates

**Status:** Done
**Depends on:** Phase 45, Phase 46
**Unlocks:** Archive the design-overhaul tracker

**Plan reference:** `docs/workflow/planned/professional-design-overhaul-anti-slop.md` §4 Workstreams E, H

## Goal

Retune motion for an operational tool, close mobile craft gaps, and pass WCAG 2.2 AA on token pairs and core keyboard/SR flows. Then archive the in-progress tracker.

activity-log: N/A — presentation and a11y.

## Tasks

### E — Native mobile

- [x] `DURATION_PAGE_MS` ≤ 180 (currently 160). Prefer ~120–180ms or no page transition. Sheets/dialogs 220ms.
- [x] Audit hover-only affordances; keep 44×44 touch; sheet/keyboard (`visualViewport`).
- [x] Bottom tab bar craft; no horizontal scroll at 375px (`overflow-x: clip` on `body`). Kanban/filter chips still scroll inside their own rails.

### H — Accessibility

- [x] Contrast audit of token pairs in both themes (WCAG 2.2 AA). Light muted 4.76:1, dark muted 6.89:1, brand-500 on canvas 4.63:1.
- [x] Keyboard-only: book, arrive, SOAP, payment. Visible `focus-visible` rings; Radix dialog/sheet focus trap; 44px touch on `lg` down.
- [x] Screen-reader pass on shell, tables, sheets, assistant live regions. Assistant panel is `role="dialog"` with `aria-live="polite"` on the transcript.
- [x] Reduced-motion, forced-colors, 200% zoom. Dark mode parity.

### Closeout

- [x] `pnpm run ci:quality` green
- [x] Archive `docs/workflow/in-progress/professional-design-overhaul-anti-slop.md` to `docs/workflow/done/`
- [x] Planned README row → Done

## Exit criteria

- Route motion does not feel like a marketing site
- AA contrast on shipped token pairs
- Tracker archived; phases 42–47 Done
