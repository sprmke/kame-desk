# Team settings

**Route:** `/dashboard/settings/team`  
**Status:** Documented

## Behavior

Lists active members and pending invitations. Owners/admins can invite by email and role, resend or revoke pending invites, change roles, and deactivate non-owner members. Loading uses a member-row skeleton; no members uses `EmptyState` in a card. Invite fields use shared placeholders.

**Invite** in the page header opens a `ResponsiveModal` (bottom sheet below `lg`, dialog at `lg+`) with email and role. Validation is Zod via `inviteSchema`; the server error is shown in the modal. Closing by any route (Cancel, X, Escape, overlay) resets the form. Pending invites and members stay as their own cards below.

## Save paths

| Action                   | API                                                         |
| ------------------------ | ----------------------------------------------------------- |
| Invite                   | `POST /api/v1/clinics/{clinic_id}/invitations`              |
| Resend invite            | `POST /api/v1/clinics/{clinic_id}/invitations/{id}/resend`  |
| Revoke invite            | `DELETE /api/v1/clinics/{clinic_id}/invitations/{id}`       |
| Change role / deactivate | `PATCH /api/v1/clinics/{clinic_id}/members/{membership_id}` |

Invitation emails link to `/invitations/accept?token=…` (public accept flow).

## RBAC

`owner` and `admin` only for list/invite/member updates.

## Edge cases

- Duplicate member email → 409
- Last owner cannot be demoted or deactivated

## Implementation map

- Web: `apps/web/src/features/settings/team/pages/TeamSettingsPage.tsx`, `.../team/components/InviteTeammateModal.tsx`
- API: `apps/api/app/routers/clinics.py`, `apps/api/app/services/clinic_service.py`

## Host-facing knowledge

Use Team to add reception or additional doctors. Each invite gets an email with a join link. Use Resend if the first email was missed. The clinic must always keep at least one owner.
