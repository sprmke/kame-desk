---
name: clinic-scoping
description: clinic_id on every table, membership-based queries, never trust client clinic_id.
---

# Clinic scoping

- Tenancy unit: **clinic** (not org/property/parking).
- Every non-global table has `clinic_id`.
- Resolve active clinic from JWT + `X-Clinic-Id` header + `clinic_memberships` row.
- User may belong to multiple clinics in the API; **clinic-facing MVP is one clinic** (no Add clinic UI). Switcher only if memberships > 1.
- Never filter by client-supplied `clinic_id` without membership check.
- Multi-doctor UI is Phase 2. Still store `doctor_id` on appointments.
