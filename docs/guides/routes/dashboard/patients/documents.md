# Patient documents (`/dashboard/patients/:patientId/documents/new`)

**Status:** Documented

## Behavior

- Doctor/owner picks an active template; API renders a draft preview with patient/clinic/doctor placeholders filled. The preview uses the same rich-text display as template settings (headings, lists, bold).
- User reviews preview text, then **Issue** locks `final_content_snapshot`, generates PDF, and auto-saves to `patient_files` as `clinical_document`.
- Issue is blocked until the issuing doctor's profile has a PRC license and an uploaded signature.
- Issued certificates and referrals include an electronic signature line on the PDF.
- Referral templates ask for a recipient (shared placeholder), then track status (`draft` / `sent` / `acknowledged` / `completed`) and outcome.
- Document history lists on patient detail (all staff can read).

## Save paths

| Action       | API                             | DB                                                                   |
| ------------ | ------------------------------- | -------------------------------------------------------------------- |
| Create draft | `POST /patients/{id}/documents` | `documents_generated` (draft; referral fields when type is referral) |
| Update       | `PATCH /documents/{id}`         | referral recipient/status/outcome                                    |
| Issue        | `POST /documents/{id}/issue`    | snapshot + PDF key + `patient_files` row                             |
| History      | `GET /patients/{id}/documents`  | read                                                                 |

## RBAC

| Role             | Create/issue | Read |
| ---------------- | ------------ | ---- |
| owner, doctor    | yes          | yes  |
| admin, reception | no           | yes  |

## Implementation map

- Web: `apps/web/src/features/documents/pages/DocumentNewPage.tsx`
- API: `apps/api/app/routers/documents.py`, `template_renderer.py`

## Host-facing knowledge

From a patient chart, tap **Document**, choose a template, review the filled text, then **Issue**. Referral letters also ask who you are sending to, and keep status after issue. The PDF is saved to the patient's files automatically. Issue needs the doctor's PRC license and signature on file (same completeness bar as a prescription).
