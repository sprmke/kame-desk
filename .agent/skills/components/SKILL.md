---
name: components
description: >-
  DoctorDesk UI primitives: reuse shadcn/ui, cva + data-slot, matching
  skeletons, EmptyState/ErrorState, motion tokens. Use when adding or
  changing React components in apps/web.
---

# Components

Cursor glob rule: `.cursor/rules/components.mdc`. Invoke this skill on Claude Code for UI work.

## Primitives first

`apps/web/src/components/ui/*` before native form elements or one-off markup. New primitives: `cva` variants, `data-slot`, `cn()`.

## Async UI (required on new pages)

| State   | Component                                                                                                                                |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Loading | Skeleton that mirrors real DOM. Add to `apps/web/src/components/skeletons/PageSkeletons.tsx` with `// Mirrors <RealComponent>'s markup`. |
| Error   | `ErrorState` / `InlineError`                                                                                                             |
| Empty   | `EmptyState` (icon + short heading, optional CTA)                                                                                        |

## Motion

Tokens in `apps/web/src/lib/motion.ts`. Reduced-motion required. See the `motion` skill.

## Surfaces

Climb the escalation ladder: spacing → divider → borderless section → card. Do not start a page with `Card`. No card-in-card. Record lists are rows. See `docs/architecture/design-language.md` and `anti-slop-design.mdc`.

## Don'ts

Native `<select>`/`checkbox` where a primitive exists. Centered `Dialog` on mobile for ops flows (`ResponsiveModal`). Gradients, confetti, default exports for shared components. No `Stethoscope` / `Armchair` / `Bot` / `Sparkles`. No pastel KPI icon chips on operational screens.
