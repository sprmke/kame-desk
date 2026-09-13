---
name: rbac-and-audit
description: RBAC decision habit for new features — owner/admin/doctor/reception matrix, no subscription tiers in MVP.
---

# RBAC and audit

DoctorDesk MVP has **no subscription plan gating** (`mvp.md` has no Plans module).

For every new capability:

1. **RBAC** — which roles can view/mutate? Wire `require_clinic_role` on API; gate UI consistently.
2. **Audit** — emit `activity_log` or mark N/A.

Role matrix: `docs/mvp.md` §6.11. Reception: no clinical notes by default.
