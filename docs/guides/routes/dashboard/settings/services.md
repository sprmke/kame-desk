# Services and fees (`/dashboard/settings/services`)

**Status:** Documented

## Behavior

Owners and admins add and remove rows in the clinic service catalog used when creating invoices. Optional duration (minutes) becomes the default length when booking that type.

The page is a **list only**. The catalog fills the settings content column. **New service** in the page header opens a `ResponsiveModal` (bottom sheet below `lg`, dialog at `lg+`) with name, amount, minutes, and category. Save is disabled until name and amount are filled. Closing the modal by any route (Cancel, X, Escape, overlay) resets the form. The list and the empty state both sit in a card. The empty state repeats the same action.

## Save paths

| Action | API                                          |
| ------ | -------------------------------------------- |
| List   | `GET /clinics/{id}/service-fees`             |
| Add    | `POST /clinics/{id}/service-fees`            |
| Remove | `DELETE /clinics/{id}/service-fees/{fee_id}` |

Writes emit `service_fee.created` / `service_fee.deleted`.

## RBAC

Owner and admin.

## Implementation map

- Web: `apps/web/src/features/settings/services/pages/ServicesSettingsPage.tsx`, `.../services/components/ServiceCreateModal.tsx`
- API: `apps/api/app/routers/clinics.py`

## Host-facing knowledge

Keep the fee list current so billing can pick a named service instead of typing amounts each time.
