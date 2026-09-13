# Assistant settings (`/dashboard/settings/assistant`)

**Status:** Documented

## Behavior

- Owner/admin toggle `ai_assistant_enabled` for the active clinic.
- Per-tool switches write `clinics.assistant_disabled_tools`.
- Usage (30 days) is a settings row, not a card.
- Platform kill switch: env `PLATFORM_AI_ASSISTANT_ENABLED`, overridden by `platform_feature_flags.ai_assistant` when that row exists.

## Save paths

| Action | API                   | DB                             |
| ------ | --------------------- | ------------------------------ |
| Read   | `GET /clinics/{id}`   | `clinics.ai_assistant_enabled` |
| Update | `PATCH /clinics/{id}` | same column                    |

## RBAC

Owner and admin (clinic PATCH is owner/admin only).

## Implementation map

- Web: `apps/web/src/features/settings/assistant/pages/AssistantSettingsPage.tsx`
- API: `apps/api/app/routers/clinics.py` (`PATCH /clinics/{id}`)
- Chat UI: `apps/web/src/features/assistant/` (launcher on dashboard shell). Confirm cards use a heavy border and Confirm/Send vs Cancel. The launcher has no first-run hint bubble.

## Host-facing knowledge

The assistant is off until you enable it here and your platform operator turns on the global assistant flag. When enabled, staff can ask in plain language (book, look up a patient, check a balance). Risky actions still need Confirm. When disabled, chat requests return 403 or 503 with no partial writes.
