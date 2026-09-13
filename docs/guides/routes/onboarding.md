# Onboarding wizard

**Route:** `/onboarding`  
**Status:** Documented

## Behavior

Multi-step clinic setup after registration. Steps: clinic profile, doctor profile, working hours, fees, invite staff (or skip). A `Stepper` shows progress (mobile bar, desktop node track). Hours use a time picker in 15-minute steps. Progress is stored on the server; reload resumes at `current_step` from `GET /api/v1/clinics/{clinic_id}/onboarding-status`.

Incomplete onboarding redirects away from `/dashboard` to `/onboarding`. Theme matches the rest of the app (icon toggle, top right).

## Save paths

| Step   | UI           | API                                                                          |
| ------ | ------------ | ---------------------------------------------------------------------------- |
| Clinic | `ClinicStep` | `PATCH /api/v1/clinics/{clinic_id}`                                          |
| Doctor | `DoctorStep` | `POST /api/v1/clinics/{clinic_id}/doctors`                                   |
| Hours  | `HoursStep`  | `PUT /api/v1/clinics/{clinic_id}/working-hours`                              |
| Fees   | `FeesStep`   | `POST /api/v1/clinics/{clinic_id}/service-fees` (optional if doctor fee set) |
| Invite | `InviteStep` | `POST .../invitations` or `POST .../onboarding/skip-invite`                  |

## RBAC

Authenticated clinic member. Write steps require `owner` or `admin`.

## Implementation map

- Web: `apps/web/src/features/onboarding/`, `apps/web/src/routes/onboarding.tsx`
- API: `apps/api/app/routers/clinics.py`, `apps/api/app/services/clinic_service.py`

## Host-facing knowledge

New clinics complete setup in the onboarding wizard before using the dashboard. You can skip inviting staff and add team members later under Team settings.

Light and dark appearance is a device setting. During onboarding, use the sun/moon button at the top right. On the dashboard, open your profile picture at the top right and pick Light, Dark, or System under Theme. The choice is remembered on this device.

### Common questions

**How do I switch light and dark?**  
Dashboard: profile picture, top right, then Theme. Sign-in and onboarding: sun/moon button, top right.

**Does this change for the whole clinic?**  
No. Each browser remembers its own choice.
