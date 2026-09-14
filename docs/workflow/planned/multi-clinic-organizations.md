---
title: Multi-clinic organizations (org envelope)
status: done
updated: 2026-09-12
---

# Multi-clinic organizations (org envelope)

**Status:** Done (Phase 41)
**Prepared:** 2026-09-12

Introduce an `organizations` layer above `clinics` as the billing and ownership envelope. Clinics remain the operational/PHI tenancy unit (`X-Clinic-Id` unchanged).

## Decisions

| Topic        | Choice                                                     |
| ------------ | ---------------------------------------------------------- |
| Tenancy      | Org envelope; clinic stays PHI unit                        |
| Billing      | Plan on org + per-clinic enrollment                        |
| PHI          | Strict isolation between clinics                           |
| Ownership    | User may own multiple orgs; only org owner creates clinics |
| Payment rail | Manual Super Admin enrollment (no checkout in this module) |

## Execution phases

- **41a** Schema + backfill (`038_organizations`)
- **41b** Org API + registration flow
- **41c** Create clinic + enrollment lifecycle
- **41d** Org-level seat pooling
- **41e** Platform admin org-centric UI
- **41f** Web org settings + grouped switcher
- **41g** Tests + docs

See [phase-41-multi-clinic-organizations.md](../../phases/phase-41-multi-clinic-organizations.md) for checklist.
