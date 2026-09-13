---
name: fastapi-jwt-auth
description: FastAPI JWT access/refresh, clinic membership RBAC dependencies.
---

# FastAPI JWT auth

- Issue access (short) + refresh (long, hashed in DB) on login/register.
- `get_current_user`, `get_active_clinic_membership`, `require_clinic_role(*roles)` in `app/core/security.py`.
- Re-check `clinic_memberships.is_active` every request.
- Refresh rotation: reuse of revoked token revokes token family + `activity_log` system event.
- No Supabase — all auth is FastAPI-issued JWT.
