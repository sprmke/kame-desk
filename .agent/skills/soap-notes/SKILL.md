---
name: soap-notes
description: Versioned SOAP chart writes, never overwrite in place, specialty templates.
---

# SOAP notes

- **Versioned writes only** — new row per save; never UPDATE clinical content in place.
- Service: `apps/api/app/services/soap_service.py` (Phase 7+).
- AI drafts are Tier 2 confirm before commit.
- Spec: `docs/mvp.md` §6.5, §7.8, §7.9.
