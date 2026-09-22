# Doctor profile settings

**Route:** `/dashboard/settings/doctor`  
**Status:** Documented

## Behavior

Edit the signed-in doctor's profile (or the first clinic doctor for owners without a profile): specialty catalog (Other plus a name), PRC license, consultation fee, photo, and signature image via dropzones and presigned URLs. Each dropzone shows a local preview of the file just uploaded (the stored object is private).

## Save paths

| Action                | API                                                                               |
| --------------------- | --------------------------------------------------------------------------------- |
| Create/update profile | `POST /api/v1/clinics/{clinic_id}/doctors` or `PATCH /api/v1/doctors/{doctor_id}` |
| Photo upload          | `POST /api/v1/doctors/{doctor_id}/photo-upload` then `PUT` to presigned URL       |
| Signature upload      | `POST /api/v1/doctors/{doctor_id}/signature-upload` then `PUT` to presigned URL   |

## RBAC

Doctor may edit own profile; owners/admins manage clinic doctors via onboarding or this page.

## Implementation map

- Web: `apps/web/src/features/settings/doctor/pages/DoctorProfilePage.tsx`
- API: `apps/api/app/routers/doctors.py`, `apps/api/app/services/storage_service.py`

## Host-facing knowledge

Doctor signature, photo, license, and specialty are used on prescriptions, certificates, and SOAP defaults. Upload a clear signature image (PNG/JPEG/WebP, max 2 MB). Photo uses the same size and types.
