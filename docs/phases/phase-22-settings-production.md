# Phase 22: Settings that actually reach production

**Status:** Done
**Depends on:** Phase 21
**Unlocks:** Phase 23

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 22

## Goal

Every clinic-level configuration that exists in the backend has a reachable Settings UI: clinic profile and hours, services and fees, reception SOAP access, recall rules, BIR receipt numbering, and a usable document template editor.

## Production defaults

- BIR Official Receipt numbering: prefix `OR-`, next number `1`, pad width `6` (same as existing invoice allocation). Owners can change prefix and next number; pad width 1–10.
- Recall rules: condition label + interval in months, stored in `notification_preferences.chronic_condition_rules`.

## Tasks

### Backend

- [x] Receipt numbering GET/PUT
- [x] Service fee update/delete audit log
- [x] Template placeholder list + sample preview (no PHI)

### Frontend

- [x] Settings → Clinic (profile, hours, holidays, branding, SOAP toggle, receipt numbering)
- [x] Settings → Services and fees
- [x] Notifications: recall rules
- [x] Document templates: placeholder picker and live sample preview

## Exit criteria

- [x] Every clinic-level config item has a Settings UI
- [x] `pnpm run ci:quality` green
