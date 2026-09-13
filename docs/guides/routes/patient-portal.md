# Patient portal (`/patient-portal/:slug/*`)

**Status:** Documented

## Behavior

- Fully separate from the staff app — its own route tree, its own shell (`PatientPortalAppShell`), its own localStorage session key. No staff component, route, or auth token is reachable from here.
- Login (`/patient-portal/:slug/login`): patient enters the email or mobile number on file. Always shows the same "check your email or phone" success message, whether or not it matched a record — never confirms or denies someone is a patient of the clinic.
- The clinic sends a magic link (email if the identifier was an email and the patient has one on file; otherwise SMS via the clinic's own Twilio credentials, same as reminders). The link expires in 15 minutes and can only be used once.
- Verify (`/patient-portal/:slug/verify?token=...`): exchanges the one-time link token for a 30-minute session, then redirects to Visits.
- Once signed in: **Visits** (appointment history), **Chart** (diagnoses, ICD-10 codes, follow-up dates, and a vitals trend table — never the raw SOAP subjective/objective/plan text), **Billing** (invoices, balance), **Documents** (list + download via a presigned R2 URL). Empty and error states for those sections sit in a card, same as filled rows.
- A one-time consent notice ("this portal shows your own medical records...") appears above Visits until acknowledged; the acknowledgment is stored per browser.
- A 401 from any portal endpoint (expired/invalid session) clears the session and hard-redirects to that clinic's login page.

## Save paths

| Action            | API                                                  | Effect                                              |
| ----------------- | ---------------------------------------------------- | --------------------------------------------------- |
| Request link      | `POST /api/v1/patient-portal/login/request`          | issues a `PatientPortalToken`, sends email/SMS      |
| Verify link       | `POST /api/v1/patient-portal/login/verify`           | single-use; `patient_portal.login` activity event   |
| Profile           | `GET /api/v1/patient-portal/me`                      | read                                                |
| Visits            | `GET /api/v1/patient-portal/visits`                  | read                                                |
| Chart summary     | `GET /api/v1/patient-portal/chart-summary`           | read                                                |
| Invoices          | `GET /api/v1/patient-portal/invoices`                | read                                                |
| Documents         | `GET /api/v1/patient-portal/documents`               | read                                                |
| Document download | `GET /api/v1/patient-portal/documents/{id}/download` | presigned URL; `patient_portal.document_downloaded` |

## RBAC

None (patient session, not clinic staff). Every endpoint scopes to `get_current_patient`'s own `patient_id` and `clinic_id` — a patient can never pass another patient's id or another clinic's data. See `docs/architecture/security-compliance.md` § Patient portal auth tier.

## Implementation map

- Web: `apps/web/src/routes/patient-portal.$slug.*.tsx`, `apps/web/src/features/patient-portal/`
- API: `apps/api/app/routers/patient_portal.py`, `app/services/patient_portal_service.py`, `app/core/security.py` (`get_current_patient`, `create_patient_access_token`)

## Host-facing knowledge

Share the patient portal link (`/patient-portal/<your-clinic-slug>/login`) the same way you'd share the public booking link. Patients log in with a one-time link sent to their email or phone — there's no password to reset or forget. They can see their own visit history, a summary of diagnoses and vitals, their invoices and balance, and download any documents your clinic has shared with them. They can't message the doctor or edit anything from here.
