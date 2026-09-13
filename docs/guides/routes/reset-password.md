# Reset password (`/reset-password`)

**Status:** Documented

## Behavior

Opens from the email link (`?token=`). Password fields use required marks and inline validation. Saving a new password marks the token used and revokes every refresh session for that user.

## Save paths

| Action | API                                | Effect                                                                                     |
| ------ | ---------------------------------- | ------------------------------------------------------------------------------------------ |
| Save   | `POST /api/v1/auth/reset-password` | Update password hash, consume token, revoke sessions, `activity_log` `auth.password_reset` |

## RBAC

Public. Invalid or expired token returns 400.

## Implementation map

- Web: `apps/web/src/features/auth/pages/ResetPasswordPage.tsx`
- API: `apps/api/app/services/account_service.py`

## Host-facing knowledge

Open the link from the reset email and choose a new password. After saving, sign in again. Older sessions on other devices are signed out.
