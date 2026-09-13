---
name: ai-clinic-assistant
description: AI Clinic Assistant tool catalog, tier classification, confirm-card UX. Use when adding or changing assistant tools.
---

# AI Clinic Assistant

Spec: `docs/mvp.md` §9, `docs/architecture/ai-clinic-assistant.md`. Rule: `ai-assistant-safety.mdc`.

## Tool shape

- Register in `apps/api/app/ai/assistant/tools/`
- Each tool: name, JSON schema, `tier` (server enum), handler calling existing **service** functions.
- Update tool catalog table in `docs/architecture/ai-clinic-assistant.md` in the same change.

## Tier rules

0 = read, 1 = auto idempotent, 2 = confirm. Clinical writes and patient sends are **always** 2.

## UI

`apps/web/src/features/assistant/` — streaming chat, entity cards, Tier 2 confirm with **Send** for external messages.
