# Phase 23: Patient record integrity

**Status:** Done
**Depends on:** Phase 22
**Unlocks:** Phase 24

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 23

## Goal

Every patient-medical field has a real UI. Staff can catch duplicates before create, merge existing charts, import a CSV, and see a visit/billing/Rx timeline.

## Tasks

- [x] Possible-match lookup before create
- [x] Merge tool (reassign FKs, archive source)
- [x] Structured allergies, medications, conditions, vaccines, HMO
- [x] CSV import with dry-run then commit
- [x] Timeline + editable demographics

## Exit criteria

- [x] Medical fields are structured (no JSON textarea)
- [x] `pnpm run ci:quality` green (API integrity suite + web type-check)
