# Phase 30: Platform Super Admin, tenancy, and monetization

**Status:** Done
**Depends on:** Phase 21
**Unlocks:** Phase 32

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 30

## Production defaults

- Plans: `starter` (trial 14 days) / `pro` / `clinic`. Metered later: AI + SMS. Seats are flat on the plan card.
- New clinics: `status=trial`, `plan_key` from signup or `starter`.
- Super admin: email allow-list `PLATFORM_ADMIN_EMAILS`.
- Impersonation: Super admin only, clinic owner token, 30 minutes, `platform_audit_log`, PHI visible for support, banner in the clinic app.
- Kill switch: `platform_feature_flags.ai_assistant` overrides env `platform_ai_assistant_enabled` when a flag row exists.

## Goal

Operate DoctorDesk as a SaaS: list tenants, change plan/status, flip the AI flag, help a clinic, see counts only.

## Tasks

- [x] `clinics.status` / `clinics.plan_key`
- [x] Suspend lock at auth
- [x] Platform API + `/platform/*` shell
- [x] Public `/plans` + `/pricing` + register `plan_key`
- [x] Feature flag UI
- [x] Audited support login
- [x] Aggregate metrics (AI, SMS, files, tenant counts; no PHI)
- [x] Tests

## Exit criteria

- [x] A platform admin can sell a plan, suspend a tenant, and cut off the assistant without a deploy

activity-log: N/A for clinic `activity_log`. Platform mutations write `platform_audit_log`.
