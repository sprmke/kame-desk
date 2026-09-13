# Home (`/`)

**Status:** Documented

## Behavior

`/` has no marketing page. Signed-in staff go to `/dashboard`. Everyone else goes to `/login`. `/pricing` remains the public plan page.

## Save paths

None. Redirect only.

## RBAC

Public. Destination depends on whether an access token is in local storage.

## Implementation map

- Web: `apps/web/src/routes/index.tsx`

## Host-facing knowledge

Open the clinic URL and you land on sign-in, or on Today if you are already signed in.
