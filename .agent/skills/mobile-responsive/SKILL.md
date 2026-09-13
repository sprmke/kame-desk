---
name: mobile-responsive
description: >-
  Mobile-first, responsive UI standards for every screen in DoctorDesk —
  breakpoints, touch targets, bottom tab bar, ResponsiveModal, safe-area,
  swipe-to-reveal. Use for any new or changed UI in apps/web/src/**. This is
  an always-on glob rule on the Cursor side (mobile-responsive.mdc) with no
  automatic Claude Code equivalent, so invoke it explicitly for UI work.
---

# Mobile-first clinic UI

Every staff screen must work at **375 px**, **768 px**, **1024 px**, and **1440 px**. Front desk often runs on a shared iPad. Native-feeling means operational (bottom sheets, dock, tap feedback), not hospitality chrome.

## Breakpoints

Use Tailwind **min-width** prefixes. Never max-width queries.

| Prefix   | Min  | Shell                              |
| -------- | ---- | ---------------------------------- |
| _(none)_ | 0    | Phone. Bottom tabs. Sheets.        |
| `sm:`    | 640  | Large phone                        |
| `md:`    | 768  | Tablet portrait                    |
| `lg:`    | 1024 | Desktop sidebar. Centered dialogs. |

## Shell

```
Mobile (<lg):
  Top header (search + profile)
  Page content + bottom tab inset
  BottomTabBar: Calendar | Waiting | Patients | More

Desktop (lg+):
  AppSidebar | header + content
```

- Shared: `apps/web/src/components/mobile/BottomTabBar.tsx`, `MobileMoreSheet.tsx`.
- Content clearance: `bottomTabBarOffsetClassName()` on `DashboardShell` `<main>`.
- Calendar and waiting room must work in **tablet landscape**.

## Touch

Minimum **44×44 px**. Desktop 24×24px or WCAG 2.5.8 spacing. Icon-only: `aria-label`. Prefer `min-h-[44px]` on list actions. `touch-action: manipulation`. No hover-only affordances.

## Modals

Operational flows use `ResponsiveModal` (sheet `<lg`, dialog `lg+`). Do not import `Dialog` directly for walk-in, cancel/no-show, payment, series scope, or command palette. Exceptions: `AlertDialog`, full-screen media.

Bottom `Sheet`: drag handle, `max-h-[92dvh]`, safe-area padding.

## Safe area

`viewport-fit=cover` in `__root.tsx`. Use `env(safe-area-inset-*)` on header top, tab bar, and bottom sheets.

## Press + swipe

- `.native-press` on tappable cards/rows.
- `SwipeRevealRow` on waiting-room cards and appointment rows below `lg`. Swipe **reveals** actions; a second tap executes. Not swipe-to-execute. Disabled when `prefers-reduced-motion`.
- No pull-to-refresh (waiting room is live via WebSocket).

## Tone

Clinical, calm. No gradients, confetti, or marketing heroes. Copy: `ui-minimal-copy.mdc` + `human-copy.mdc`.

## Checklist

- [ ] 375 and 768, no accidental page-level horizontal scroll
- [ ] Targets ≥ 44×44
- [ ] Reduced-motion path for new animation
