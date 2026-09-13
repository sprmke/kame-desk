# Document templates (`/dashboard/settings/document-templates`)

**Status:** Documented

## Behavior

- Owner/admin create and edit letter templates (`medical_certificate`, `referral_letter`, `lab_request`, `confinement_certificate`, `custom`). Loading uses a catalog skeleton; no templates uses `EmptyState` in a card.
- The page is a **catalog only**. **New template** in the card header opens a `ResponsiveModal` (bottom sheet below `lg`, dialog at `lg+`) in create mode; tapping a catalog row opens the same modal in edit mode with that template loaded. Key and type are fixed once a template exists, so both are disabled when editing. The form reloads from the selected template on every open, so a cancelled edit never leaks into the next one. The action sits in the card header rather than the page header because this body is mounted under both Settings and the Documents hub, each of which supplies its own heading.
- The page header explains that templates use patient and clinic placeholders.
- On `/dashboard/documents/templates` the fixed **Documents** title and description sit above the Generate / Templates tabs, with the template catalog below the tabs. The shared page body carries no heading of its own, so the `/dashboard/settings/document-templates` route supplies its own **Document templates** title and description.
- Body is a WYSIWYG editor (bold, headings, lists, alignment, links). Tokens such as `{{patient.full_name}}` highlight in the editor. Insert tokens from the Placeholders dialog (searchable list with copy).
- Edit / Preview uses a segmented control in the editor toolbar. Preview fills sample names in the browser (not a real patient). Issuing a letter still uses the API renderer with that patient's data.
- Forbidden syntax (`{%`, `__`, etc.) is rejected server-side. Issued PDFs keep heading/list/bold formatting from the HTML body; older plain-text templates still render. Older `{{patient_name}}` / `{{visit_date}}` tokens still fill; opening a template rewrites them to the dotted keys.

## Save paths

| Action | API                                           | DB                                        |
| ------ | --------------------------------------------- | ----------------------------------------- |
| List   | `GET /clinics/{id}/document-templates`        | `document_templates`                      |
| Create | `POST /clinics/{id}/document-templates`       | insert                                    |
| Update | `PATCH /clinics/{id}/document-templates/{id}` | update (does not change issued snapshots) |

## RBAC

Owner and admin only.

## Implementation map

- Web: `apps/web/src/features/documents/pages/DocumentTemplatesPage.tsx`, `apps/web/src/features/documents/components/DocumentTemplateFormModal.tsx`, `apps/web/src/features/documents/components/DocumentTemplateEditor.tsx`, `apps/web/src/components/ui/rich-text-editor.tsx`
- API: `apps/api/app/routers/documents.py`

## Host-facing knowledge

Clinic admins maintain certificate and referral templates under settings. Type the letter in the editor, open Placeholders to insert patient or clinic tokens, then switch to Preview to see sample names filled in. Issued documents keep the text from issue time even if the template changes later.
