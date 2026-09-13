# Forgot password (`/forgot-password`)

**Status:** Documented

## Behavior

Anyone can submit an email. The field uses a shared placeholder and inline validation. The API always returns 204 so the page cannot be used to discover whether an address is registered. If the address belongs to an active user, a one-hour reset link is emailed.

## Save paths

| Action    | API                                 | Effect                                                               |
| --------- | ----------------------------------- | -------------------------------------------------------------------- |
| Send link | `POST /api/v1/auth/forgot-password` | Insert hashed `account_tokens` row (`password_reset`) and send email |

## RBAC

Public. Always 204.

## Implementation map

- Web: `apps/web/src/features/auth/pages/ForgotPasswordPage.tsx`
- API: `apps/api/app/services/account_service.py`

## Host-facing knowledge

Enter your account email. If it is registered, you will get a reset link that expires in one hour.
