# Phase 41 — Multi-clinic organizations

**Status:** Done
**Depends on:** Phase 30, Phase 21

## Goal

Org envelope above clinics: billing and ownership at org level, operational/PHI scoping unchanged at clinic level. End-to-end from signup through add-clinic, enrollment activation, and org-aware switcher.

## Tasks

### 41a — Schema and backfill

- [x] Alembic `038_organizations`
- [x] Models: `Organization`, `OrganizationSubscription`, `OrganizationEnrolledClinic`
- [x] `clinics.organization_id` NOT NULL after backfill
- [x] Backfill one org per existing clinic

### 41b — Org API + registration

- [x] `organization_service.py`, `organizations.py` router
- [x] `register_user` creates org + subscription + clinic + active enrollment
- [x] `/auth/me` returns `organizations` list

### 41c — Create clinic + enrollment

- [x] `POST /organizations/{org_id}/clinics` (org owner only)
- [x] Additional clinics start as `pending_enrollment`
- [x] `POST /clinics/{id}/transfer-ownership`

### 41d — Seat pooling + plan entitlements

- [x] `seat_service` pools doctor seats across enrolled clinics
- [x] `PLAN_ENTITLEMENTS` with `max_clinics` per plan
- [x] Doctor invites blocked when enrollment not active

### 41e — Platform admin

- [x] Org-centric `/platform/tenants`
- [x] `PATCH /platform/tenants/{org_id}/enrollments/{clinic_id}`
- [x] Org impersonation

### 41f — Web UX

- [x] `/dashboard/settings/organization` + add clinic flow
- [x] Grouped workspace switcher
- [x] Billing plan page reads org subscription

### 41g — Hardening

- [x] Public booking gated on active enrollment
- [x] Org suspended blocks clinic access
- [x] `test_organizations.py`
- [x] E2E `multi-clinic-org.spec.ts`
- [x] Docs sync

## Exit criteria

- New signup creates org + clinic with active enrollment
- Org owner on Pro plan can add a second clinic (pending until Super Admin activates)
- Doctor seats pool at org level
- Platform admin can activate enrollment
- No cross-clinic PHI reads
- `pnpm run ci:quality` green
