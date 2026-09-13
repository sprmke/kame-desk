# Clinic settings (`/dashboard/settings/clinic/*`)

**Status:** Documented

## Routes

| Path                                    | Content                                            |
| --------------------------------------- | -------------------------------------------------- |
| `/dashboard/settings/clinic`            | Redirects to Details                               |
| `/dashboard/settings/clinic/details`    | Profile, reception SOAP access                     |
| `/dashboard/settings/clinic/hours`      | Working hours, holidays                            |
| `/dashboard/settings/clinic/rooms`      | Room list                                          |
| `/dashboard/settings/clinic/branding`   | Logo, brand color                                  |
| `/dashboard/settings/clinic/compliance` | Receipt numbering, BIR compliance, growth settings |

## Behavior

Owners and admins edit clinic profile, logo upload, brand color (letterhead/PDF accent), working hours, holidays, reception SOAP access, BIR official receipt numbering, and BIR compliance fields after onboarding. Loading uses a stacked-card skeleton. Profile fields use shared placeholders. Settings use divider rows (`SettingsSection` / `SettingsRow`), not a stack of bordered cards.

The Rooms section is a **list only**. **New room** in the section header opens a `ResponsiveModal` (bottom sheet below `lg`, dialog at `lg+`); the empty state repeats the same action. The list and the empty state both sit in a card. Existing rows toggle between Hide and Show (rooms are deactivated, never deleted, so past appointments keep their room).

- Each view carries its own page title matching the settings nav item (Clinic details, Hours and holidays, Rooms, Branding, Compliance). The settings layout renders the nav only, so there is no second "Settings" heading above it.
- **Logo:** `ImageFileDropzone` (click or drag). Uploads to R2 via presigned URL; preview uses a short-lived download URL.
- **Brand color:** `BrandColorField` swatches + custom picker. Stored on `clinics.brand_color`. Used on issued PDFs (Rx, invoice, certificates), not a full theme override.
- **Receipt pad width:** `NumberSlider` (1–10) instead of a plain number field.
- **BIR compliance:** TIN, registered business name/address (fall back to the clinic profile fields when left blank), VAT-registered toggle, and a compliance mode selector (Not yet accredited / Permit to Use / CAS). The accreditation number and validity date fields only appear once a PTU or CAS mode is selected; an expired validity date shows an inline warning but still saves.
- **Growth settings** (`GrowthSettingsCard`, rendered below the BIR compliance card on the Compliance view): a toggle for post-visit review & NPS requests, the clinic's Google Business review link (only sent when the toggle is on and a link is set), and a DOH EMR accreditation number + validity date — display-only trust-signal metadata, same pattern as BIR PTU/CAS, no accreditation workflow and no live DOH system connection.

## Save paths

| Action                       | API                                   | DB                               |
| ---------------------------- | ------------------------------------- | -------------------------------- |
| Logo upload                  | `POST /clinics/{id}/logo-upload`      | `clinics.logo_url` (object key)  |
| Profile / SOAP / brand color | `PATCH /clinics/{id}`                 | `clinics`                        |
| Hours / holidays             | `PUT /clinics/{id}/working-hours`     | `working_hours`, `holiday_dates` |
| Receipt numbering            | `PUT /clinics/{id}/receipt-numbering` | `receipt_numbering_config`       |
| BIR compliance               | `PUT /clinics/{id}/bir-compliance`    | `bir_compliance_config`          |
| Growth settings              | `PUT /clinics/{id}/growth-settings`   | `growth_settings`                |
| Rooms                        | `GET/POST /clinics/{id}/rooms`        | `rooms`                          |

Default numbering is prefix `OR-`, next number `1`, pad width `6`. BIR compliance defaults to `not_yet_accredited` with all fields unset. This never blocks invoice issuance; a non-blocking banner on the Billing invoices page (`/dashboard/billing/invoices`) flags an unset TIN, a missing accreditation number for PTU/CAS mode, or an expired accreditation date. Growth settings default to review requests disabled and all fields unset.

## RBAC

Owner and admin edit; `bir_compliance` is readable by any clinic staff via `GET /clinics/{id}` (same visibility as `receipt_numbering`), matching what reception needs to see when issuing a receipt.

## Implementation map

- Web: `apps/web/src/features/settings/clinic/pages/ClinicSettingsPage.tsx`, `.../clinic/components/RoomCreateModal.tsx`; routes under `apps/web/src/routes/dashboard.settings.clinic*.tsx`; banner in `apps/web/src/features/billing/pages/InvoiceListPage.tsx`
- API: `apps/api/app/routers/clinics.py`, migrations `029_clinic_brand_color`, `031_bir_compliance_depth`

## Host-facing knowledge

Use Clinic to change hours, holidays, address, logo, brand color on printed documents, and whether reception can open SOAP notes. Upload a logo by dropping an image or clicking the upload area. Brand color affects the accent line on prescriptions and receipts, not the whole dashboard. Receipt numbering is the Official Receipt series used when an invoice is issued. Changing the next number only affects invoices issued after you save. BIR compliance fields print on every receipt/invoice so the clinic's own bookkeeper has what they need for BIR filing; kame-desk does not file or accredit anything on the clinic's behalf. Leaving these fields blank never blocks issuing an invoice, it just shows a reminder banner on the Billing page. Growth settings control whether patients get an automatic review-request + NPS survey after their visit is marked Completed (email/SMS, whichever channel is configured); the DOH accreditation fields are display-only and print nowhere yet — they exist so the clinic can record the number for its own reference.
