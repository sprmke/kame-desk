---
name: motion
description: >-
  DoctorDesk motion budget: micro / transition / page tiers, framer-motion
  scope, prefers-reduced-motion. Use when adding animation, sheets, tab
  pills, or page transitions in apps/web.
---

# Motion

Cursor glob rule: `.cursor/rules/motion.mdc`. Tokens: `apps/web/src/lib/motion.ts`.

## Tiers

Frequency first (anti-slop M): 100+/day = none; occasional = standard. Hard ceiling 300ms. Route changes ≤180ms or absent.

- **Micro (150ms, `ease-theme`):** hover/press/focus. Hover motion only on fine pointers.
- **Transition (currently 280ms, retune Phase 47):** tab pill, sheet/dialog, list stagger.
- **Page (code still 300ms; that fails M1):** `PageTransition` on dashboard sub-routes.

`framer-motion` only for the sliding pill, list stagger, and page transition. Only `transform` and `opacity`.

## Reduced motion

`motion-reduce:*` or `useReducedMotion()` with a static fallback. `SlidingActivePill` is the reference.

## Out of bounds

No gradients, confetti, bounce loops, or marketing cross-fades.
