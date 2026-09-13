# Documents — generate

**Status:** Documented
**Route:** `/dashboard/documents/generate`

## Behavior

- Pick a patient to start the existing generate-document flow for that chart. The picker sits in a full-width card, matching other hub pages.
- The **Generate** tab label and the patient input placeholder make it clear this creates certificates, referrals, and other documents.
- The fixed **Documents** title and description sit above the Generate / Templates tabs; the patient picker renders below the tabs. Switching tabs changes only the content, never the title or description.

## Save paths

None on this page. Create/issue happens on `/dashboard/patients/:patientId/documents/new`.

## RBAC

Same as document generate: owner and doctor can issue. All staff can search patients.

## Implementation map

- Web: `apps/web/src/features/documents/pages/DocumentGeneratePage.tsx`

## Host-facing knowledge

Open **Documents → Generate**, pick the patient, then choose a template.
