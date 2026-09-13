# Doctor profile settings

**Route:** `/dashboard/settings/doctor`  
**Status:** Documented

## Behavior

Edit the signed-in doctor's profile (or the first clinic doctor for owners without a profile): specialty, PRC license, consultation fee, signature image via a dropzone and presigned URL. The dropzone shows a local preview of the file just uploaded (the stored object is private).

## Save paths

| Action                | API                                                                               |
| --------------------- | --------------------------------------------------------------------------------- |
| Create/update profile | `POST /api/v1/clinics/{clinic_id}/doctors` or `PATCH /api/v1/doctors/{doctor_id}` |
| Signature upload      | `POST /api/v1/doctors/{doctor_id}/signature-upload` then `PUT` to presigned URL   |

## RBAC

Doctor may edit own profile; owners/admins manage clinic doctors via onboarding or this page.

## Implementation map

- Web: `apps/web/src/features/settings/doctor/pages/DoctorProfilePage.tsx`
- API: `apps/api/app/routers/doctors.py`, `apps/api/app/services/storage_service.py`

## Host-facing knowledge

Doctor signature and license details are used later for prescriptions and certificates. Upload a clear signature image (PNG/JPEG/WebP, max 2 MB).
