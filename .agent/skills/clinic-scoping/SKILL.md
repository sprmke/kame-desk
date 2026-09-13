---
name: clinic-scoping
description: clinic_id on every table, membership-based queries, never trust client clinic_id.
---

# Clinic scoping

- Tenancy unit: **clinic** (not org/property/parking).
- Every non-global table has `clinic_id`.
- Resolve active clinic from JWT + `X-Clinic-Id` header + `clinic_memberships` row.
- User may belong to multiple clinics; frontend picks active clinic.
- Never filter by client-supplied `clinic_id` without membership check.
