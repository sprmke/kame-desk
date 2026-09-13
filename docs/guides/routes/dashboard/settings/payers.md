# Settings — payers

**Status:** Documented
**Route:** `/dashboard/settings/payers`

## Behavior

Clinic-managed directory of HMO and PhilHealth payer names, listed in Settings under the **Clinic** group beside Services and fees. It is configuration, not day-to-day operational work, which is why it sits in Settings rather than in the Billing hub.

- **New payer** in the page header opens a `ResponsiveModal` with name and payer type (HMO / PhilHealth / Self-pay / Other). Save is disabled until a name is entered; closing by any route resets the form. The directory and the empty state both sit in a card.
- Payers are **deactivated, never deleted**, so historical claims keep their payer name. Inactive rows render struck through with a **Reactivate** action.
- The directory backs the payer-name autocomplete on the claim, eligibility, and LOA create forms, so the same HMO is spelled consistently everywhere. Only active payers are offered as suggestions; the field still accepts free text for a payer not yet in the directory.
- Without `billing:write` the list is read-only: no New payer button and no activate/deactivate action.

## Save paths

| Action              | API                         | DB                            |
| ------------------- | --------------------------- | ----------------------------- |
| List payers         | `GET /api/v1/payers`        | `payers` (plain array)        |
| Create payer        | `POST /api/v1/payers`       | new row, `is_active` true     |
| Activate/deactivate | `PATCH /api/v1/payers/{id}` | `is_active`, name, payer_type |

activity-log: N/A — payer directory rows are clinic configuration with no patient or financial state; claims, eligibility, and LOA writes that reference a payer emit their own events.

## RBAC

Create/update: owner, admin, reception (`billing:write`). Read: all clinic staff (`billing:view`). The settings nav entry is gated on `billing:view`, which matches what the API enforces, rather than a `settings:*` permission.

## AI assistant parity

No assistant tool reads or writes the payer directory.

## Edge cases

- `GET /api/v1/payers` returns a plain array with no pagination or search. The directory is expected to stay small (a clinic's contracted HMOs); revisit if it grows.
- Duplicate names are not rejected server-side.

## Implementation map

- Web: `apps/web/src/features/settings/payers/pages/PayersSettingsPage.tsx`, `components/PayerCreateModal.tsx`
- Route: `apps/web/src/routes/dashboard.settings.payers.tsx`
- Nav: `apps/web/src/components/layout/settings-config.ts` (Clinic group)
- API: `apps/api/app/routers/payers.py`, service `apps/api/app/services/payer_service.py`
- Migration: `030_ph_payer_workflow.py`

## Host-facing knowledge

Open **Settings → Payers** to keep the list of HMOs and PhilHealth entries your clinic works with. Tap **New payer**, enter the name, and pick the type. These names then appear as suggestions when staff add a claim, an eligibility check, or an LOA request, so everyone spells the same HMO the same way. If you stop working with a payer, use **Deactivate** instead of removing it — past claims keep their records, and the payer simply stops being suggested on new forms.
