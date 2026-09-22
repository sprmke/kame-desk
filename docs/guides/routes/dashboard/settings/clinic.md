# Clinic settings (`/dashboard/settings/clinic/*`)

**Status:** Documented (solo-clinic MVP: rooms and BIR/growth UI hidden)

## Routes

| Path                                    | Content                        |
| --------------------------------------- | ------------------------------ |
| `/dashboard/settings/clinic`            | Redirects to Details           |
| `/dashboard/settings/clinic/details`    | Profile, secretary SOAP access |
| `/dashboard/settings/clinic/hours`      | Working hours, holidays        |
| `/dashboard/settings/clinic/rooms`      | Redirects to Details (Phase 2) |
| `/dashboard/settings/clinic/branding`   | Logo, brand color              |
| `/dashboard/settings/clinic/compliance` | Receipt numbering only         |

## Behavior

Owners and admins edit clinic profile, logo upload, brand color (letterhead/PDF accent), working hours, holidays, secretary SOAP access, and receipt numbering. Rooms, BIR PTU/CAS, and growth/NPS settings are Phase 2 (APIs remain).

- Each view carries its own page title matching the settings nav item (Clinic details, Hours and holidays, Branding, Receipts). The settings layout renders the nav only, so there is no second "Settings" heading above it.
- **Logo:** `ImageFileDropzone` (click or drag). Uploads to R2 via presigned URL; preview uses a short-lived download URL.
- **Brand color:** `BrandColorField` swatches + custom picker. Stored on `clinics.brand_color`. Used on issued PDFs (Rx, invoice, certificates), not a full theme override.
- **Receipt pad width:** `NumberSlider` (1–10) instead of a plain number field.
- Rooms, BIR PTU/CAS, and growth/NPS cards are hidden in MVP; APIs remain for Phase 2.

## Save paths

| Action                       | API                                   | DB                               |
| ---------------------------- | ------------------------------------- | -------------------------------- |
| Logo upload                  | `POST /clinics/{id}/logo-upload`      | `clinics.logo_url` (object key)  |
| Profile / SOAP / brand color | `PATCH /clinics/{id}`                 | `clinics`                        |
| Hours / holidays             | `PUT /clinics/{id}/working-hours`     | `working_hours`, `holiday_dates` |
| Receipt numbering            | `PUT /clinics/{id}/receipt-numbering` | `receipt_numbering_config`       |

Default numbering is prefix `OR-`, next number `1`, pad width `6`. Hidden APIs still exist: `PUT /clinics/{id}/bir-compliance`, `PUT /clinics/{id}/growth-settings`, `GET/POST /clinics/{id}/rooms`.

## RBAC

Owner and admin edit. Receipt numbering is readable by any clinic staff via `GET /clinics/{id}`.

## Implementation map

- Web: `apps/web/src/features/settings/clinic/pages/ClinicSettingsPage.tsx`; routes under `apps/web/src/routes/dashboard.settings.clinic*.tsx`
- API: `apps/api/app/routers/clinics.py`, migrations `029_clinic_brand_color`, `031_bir_compliance_depth`

## Host-facing knowledge

Use Clinic to change hours, holidays, address, logo, brand color on printed documents, and whether the secretary can open SOAP notes. Receipt numbering is the Official Receipt series used when an invoice is issued.
