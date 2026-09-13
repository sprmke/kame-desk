# Phase 21: Account & session foundations

**Status:** Done
**Depends on:** Phase 20
**Unlocks:** Phase 22

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 21

## Goal

No account is permanently unrecoverable. Users can reset a password, verify email, see and revoke sessions, export clinic data, and request deletion. Multi-clinic login is deterministic. Pending invites can be resent.

## Tasks

### Backend

- [x] Forgot/reset password (opaque hashed tokens, always-204 forgot)
- [x] Email verification on register (auto-verified in tests; email in production)
- [x] Session list + logout everywhere
- [x] Deterministic membership order (clinic name, then membership created_at)
- [x] Resend invitation
- [x] Patient + appointment CSV export; clinic deletion request (owner)

### Frontend

- [x] Forgot/reset/verify pages
- [x] Clinic switcher on all viewports
- [x] Team: Resend on pending invites
- [x] Settings → Account: sessions, export, deletion request

## Exit criteria

- [x] Locked-out owner can recover via email reset
- [x] User can list and revoke their sessions
- [x] Clinic can export CSV and file a deletion request
- [x] `pnpm run ci:quality` green
