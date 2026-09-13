# Verify email (`/verify-email`)

**Status:** Documented

## Behavior

Opens from the registration verification email (`?token=`). Local and automated tests auto-verify on register so existing onboarding tests stay green. Production sends a verification email; login is not blocked if the address is still unverified.

## Save paths

| Action | API                                     | Effect                                                                             |
| ------ | --------------------------------------- | ---------------------------------------------------------------------------------- |
| Verify | `POST /api/v1/auth/verify-email`        | Set `users.email_verified_at`, consume token, `activity_log` `auth.email_verified` |
| Resend | `POST /api/v1/auth/resend-verification` | New `email_verify` token (authenticated)                                           |

## RBAC

Verify is public. Resend requires a valid access token.

## Implementation map

- Web: `apps/web/src/features/auth/pages/VerifyEmailPage.tsx`
- API: `apps/api/app/services/account_service.py`

## Host-facing knowledge

Open the link in the verification email. You can still sign in if you have not verified yet.
