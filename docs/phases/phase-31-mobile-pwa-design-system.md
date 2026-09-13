# Phase 31: Mobile, PWA, and design-system consolidation

**Status:** Done
**Depends on:** Phase 26
**Unlocks:** Phase 32

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 31

## Production default

UI font is IBM Plex Sans / IBM Plex Mono. `registerPwa()` runs in production only (no-op in Vite DEV).

## Goal

Tablet users get an installable app and consistent type tokens.

## Tasks

- [x] Call `registerPwa()` from `__root.tsx`
- [x] Invoice detail wraps on narrow viewports
- [x] Design tokens: `DESIGN.md` + `styles.css` + `design-system.md` agree on IBM Plex

## Exit criteria

- [x] PWA registration is wired
- [x] Font source of truth is IBM Plex

activity-log: N/A
