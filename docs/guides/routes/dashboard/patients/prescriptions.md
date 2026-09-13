# Patient prescriptions (`/dashboard/patients/:patientId/prescriptions/new`)

**Status:** Documented

## Behavior

- Multi-drug Rx pad with add/remove rows. Drug, dosage, frequency, duration, and quantity fields use shared placeholders.
- Inline conflict banner when allergy/interaction flags are returned from the server. Drugs not in the curated list show **not checked** and do not require an override.
- **Explain** per flag calls `POST /api/v1/patients/{id}/prescription-flag/explain` (Tier 0; does not change the deterministic flag).
- Override reason required before issue when flags are present.
- Patient detail lists prescription history with PDF link and **Use as template**.

## Save paths

| Action       | API                                                    | DB effect                  |
| ------------ | ------------------------------------------------------ | -------------------------- |
| Conflicts    | `POST /api/v1/patients/{id}/prescription-conflicts`    | read (deterministic)       |
| Explain flag | `POST /api/v1/patients/{id}/prescription-flag/explain` | read (AI explanation only) |
| Draft        | `POST /api/v1/patients/{id}/prescriptions`             | `prescriptions` draft      |
| Issue        | `POST /api/v1/prescriptions/{id}/issue`                | issued + PDF to R2         |
| Void         | `POST /api/v1/prescriptions/{id}/void`                 | status voided              |
| History      | `GET /api/v1/patients/{id}/prescriptions`              | read                       |
| PDF          | `GET /api/v1/prescriptions/{id}/pdf`                   | read                       |

## RBAC

Write/issue/void: user with a `doctor_profiles` row (`doctor` or `owner`). Read: `owner`, `admin`, `doctor`. Reception: no access.

## Edge cases

- PRC license required on doctor profile before issue.
- Safety flags use curated `drug_reference` seed data, not a national drug DB.
- Void never deletes rows or PDFs.

## Implementation map

- Web: `features/prescriptions/pages/PrescriptionNewPage.tsx`, patient detail history
- API: `routers/prescriptions.py`, `prescription_service.py`, `prescription_safety.py`

## Host-facing knowledge

Open **Rx** on a patient to issue medications. If the system flags an allergy or interaction, enter an override reason before issuing. Past prescriptions can be reused as a template.
