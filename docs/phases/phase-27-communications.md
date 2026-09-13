# Phase 27: Communications you can trust

**Status:** Done
**Depends on:** Phase 26
**Unlocks:** Phase 28

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 27

## Production default

Twilio remains the SMS provider. High no-show risk moves the 24h reminder to 36h before the visit and the same-day reminder to 6h before.

## Goal

Staff can see every reminder, retry a failed send, and honor a per-patient opt-out.

## Tasks

- [x] Reminder list + retry
- [x] Patient reminder opt-out
- [x] Smart timing from no-show risk
- [x] Reminder dashboard UI
- [x] Tests

## Exit criteria

- [x] Staff have visibility and control over reminders the system claims to send
- [x] Tests green (`apps/api/tests/test_communications.py`)

activity-log: `reminder.retried` on retry. Opt-out uses `patient.updated`.
