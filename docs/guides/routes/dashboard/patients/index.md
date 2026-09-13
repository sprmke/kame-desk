# Patients list (`/dashboard/patients`)

**Status:** Documented

## Behavior

- Paginated list of clinic patients with fuzzy search on name, contact, and patient number.
- The fixed **Patients** title and description sit above the Directory / Chart search tabs; the patient content renders below the tabs. **Import** and **New patient** are contributed to the section header by this tab. Switching tabs changes only the content, never the title or description.
- Toolbar matches other clinic lists: live search, sort, per-page (25/50/100), and Table / List views. Phone defaults to List. Query params keep `q`, `page`, `limit`, `sort`, and `view`.
- Table and list rows use an identity block (initials, name, patient number) plus age/sex and contact so two people with the same name can be told apart.
- **New patient** opens `/dashboard/patients/new`. Possible matches by name or contact appear before save.
- Owner/admin use **Import** beside **New patient** to open the CSV import sheet/dialog. The custom dropzone supports browse and drag-and-drop, validates CSV type and a 5 MB client limit, then requires Preview before Import.
- Row click opens patient detail.
- **Phone/tablet:** bottom tab **Patients**. Rows use press feedback (`.native-press`). Empty registry shows `EmptyState` with a New patient action, inside the same bordered card as the table.

## Save paths

| Action  | UI                | API                                              | DB                                             |
| ------- | ----------------- | ------------------------------------------------ | ---------------------------------------------- |
| Search  | Search box (live) | `GET /api/v1/patients?q=&page=&page_size=&sort=` | `patients` filtered by `clinic_id` + `pg_trgm` |
| Create  | New patient form  | `POST /api/v1/patients`                          | `patients` + empty `patient_medical_info`      |
| Matches | New patient form  | `GET /api/v1/patients/matches`                   | existing `patients`                            |
| Import  | Preview / Import  | `POST /api/v1/patients/import`                   | `patients` (commit only)                       |

## Validation

- `full_name` required (client Zod + API Pydantic).
- **New patient** (`/dashboard/patients/new`): staff must check **Patient consents to clinic data processing** before save. Birthdate uses a calendar picker (cannot be after today). API stores `data_processing_consent_at` on `patients` and rejects create without consent.

## RBAC

`owner`, `admin`, `doctor`, `reception` — full access (Phase 3 matrix).

## AI assistant parity

Not yet (Phase 16).

## Edge cases

- Archived patients remain in DB (`is_archived`); list may include them until filtered in a later pass.

## Implementation map

- Web: `apps/web/src/features/patients/pages/PatientListPage.tsx`
- API: `apps/api/app/routers/patients.py`, `patient_service.py`

## Host-facing knowledge

Staff use **Patients** (bottom tab on a phone, sidebar on a computer) to find or add people. Search matches partial names and phone numbers. Change how many rows show, sort by name or number, and switch Table or List. Each patient gets a clinic-specific number (#1, #2, …). Owners and admins can open **Import**, drop in a CSV, and preview it before creating records.

**Q: Can I delete a patient?**  
A: Records are archived, not deleted, to keep clinical history intact.
