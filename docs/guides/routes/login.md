# Sign in (`/login`)

**Status:** Documented

## Behavior

Staff sign in with email and password. Fields use required marks, shared placeholders, and inline validation errors. On success, tokens and the active clinic id are stored and the app opens `/dashboard`. A Forgot password link goes to `/forgot-password`. On large screens the form sits beside a brand panel (product mark, no bordered card). On a phone the mark sits above the form.

## Save paths

| Action  | API                       | Effect                                                                                                              |
| ------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Sign in | `POST /api/v1/auth/login` | Issues access + refresh tokens. Active clinic is the first membership by clinic name, then membership created date. |

## RBAC

Public. Inactive users and users with no active membership get 403.

## Implementation map

- Web: `apps/web/src/features/auth/pages/LoginPage.tsx`
- API: `apps/api/app/routers/auth.py`, `apps/api/app/services/auth_service.py`

## Host-facing knowledge

Use the email you registered or were invited with. If you cannot sign in, use Forgot password. The clinic switcher in the header is for people who belong to more than one clinic.
