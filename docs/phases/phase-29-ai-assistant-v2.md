# Phase 29: AI Clinic Assistant v2

**Status:** Done
**Depends on:** Phase 20, Phase 28
**Unlocks:** Phase 32

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 29

## Production default

Booking or reschedule outside 08:00–18:00, or with `overlap_risk`, is Tier 2. Per-tool disable lives on `clinics.assistant_disabled_tools`. Confirm cards show the proposal payload, not the raw tool name.

## Goal

A receptionist can confirm exactly what the assistant will do. Owners can see usage and turn off individual tools.

## Tasks

- [x] Confirm cards render proposal fields
- [x] `page_context` from the current route
- [x] Working-hours and overlap-risk tier escalation
- [x] Rich result cards for patient/appointment/invoice payloads
- [x] Suggested prompts, first-run hint, retry
- [x] Owner usage view + per-tool toggles
- [x] Tests

## Exit criteria

- [x] Confirmations are readable
- [x] Risky bookings escalate to confirm
- [x] Owners can disable a tool and see usage

activity-log: existing `assistant.tool.*` rows. Tool disable uses `clinic.updated`.
