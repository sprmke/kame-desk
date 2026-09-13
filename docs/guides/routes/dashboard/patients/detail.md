# Patient detail (`/dashboard/patients/:patientId`)

**Status:** Documented

## Behavior

- Persistent identity rail: name, patient number, allergies summary, and outstanding balance stay visible across tabs. Avatar initials sit beside the name.
- Editable demographics: contact and HMO (provider, member ID). Sections use headings, not bordered cards.
- Structured medical editor: allergy/medication/condition/vaccine chips, `allergies_reviewed` checkbox. No JSON textarea.
- Structured medical editor: allergy/medication/condition/vaccine chips, `allergies_reviewed` checkbox. No JSON textarea.
- Timeline tab: visits, prescriptions, invoices, and documents in one list.
- Vitals, files, timeline, prescriptions, invoices, orders, and documents each use a compact `EmptyState` (with a create CTA where it applies) inside the same card as the filled list. Demographics and merge fields use shared placeholders. Order type and referral status use `Select`, not a native `<select>`.
- **Invoice** link to create/issue a bill; billing section lists invoices with balance, a compact eligibility check widget (`PatientEligibilityCard`, Phase 33) showing the latest HMO/PhilHealth eligibility status and a form to request a new one, and a **Membership** card (`PatientMembershipCard`, Phase 38): shows the patient's active plan, renewal date, and usage-this-period, with a **Cancel membership** action; when the patient has no active membership, a plan picker + **Enroll** button lists the clinic's active membership plans.
- **Book** links to new appointment with patient pre-selected.
- Owner/admin can merge a duplicate chart into this one (source archived).
- **Orders** tab: lab/imaging list with status (`ordered` / `in progress` / `resulted` / `cancelled`) and result text.
- Referral documents show recipient, status, and outcome. A referral letter also gets a **Share chart summary** button (Phase 38) that creates a scoped, expiring (7-day) public link to a read-only chart-summary snapshot — no recipient account required — and a **Copy link** action once created.
- Generate letter, new Rx, and new invoice open as nested pages (`…/documents/new`, `…/prescriptions/new`, `…/invoices/new`) so they no longer render under the chart layout.

## Save paths

| Action                       | API                                                                            | DB                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| Update demographics          | `PATCH /api/v1/patients/{id}`                                                  | `patients`                                                                      |
| Update medical info          | `PUT /api/v1/patients/{id}/medical-info`                                       | `patient_medical_info`                                                          |
| Merge duplicate              | `POST /api/v1/patients/{id}/merge`                                             | reassign FKs; archive source                                                    |
| Create order                 | `POST /api/v1/patients/{id}/orders`                                            | `clinical_orders`                                                               |
| Update order                 | `PATCH /api/v1/patients/{id}/orders/{id}`                                      | status / result                                                                 |
| Update referral              | `PATCH /api/v1/documents/{id}`                                                 | referral fields                                                                 |
| List vitals                  | `GET /api/v1/patients/{id}/vitals`                                             | `patient_vitals`                                                                |
| List files                   | `GET /api/v1/patients/{id}/files`                                              | `patient_files` + presigned R2 URL                                              |
| List invoices                | `GET /api/v1/patients/{id}/invoices`                                           | `invoices`                                                                      |
| Patient balance              | `GET /api/v1/patients/{id}/balance`                                            | aggregate                                                                       |
| List/create eligibility      | `GET/POST /api/v1/eligibility-checks`                                          | `eligibility_checks`                                                            |
| Get/enroll/cancel membership | `GET/POST /api/v1/patients/{id}/membership`, `POST .../membership/{id}/cancel` | `patient_memberships`                                                           |
| Create chart share           | `POST /api/v1/documents/{id}/chart-share`                                      | sets `chart_share_token_hash`/`chart_share_expires_at` on `generated_documents` |

## RBAC

All four clinic staff roles can view and edit structured medical info (allergies, medications, history).

`clinical_notes` on medical info follows SOAP rules: `owner`, `admin`, and `doctor` can read/write; `reception` is blocked unless the clinic enables **reception can view SOAP** (same flag as visit SOAP notes). Reception without that flag gets `clinical_notes` omitted on read and `403` on write.

## Implementation map

- Web: `apps/web/src/features/patients/pages/PatientDetailPage.tsx`, `apps/web/src/features/billing/components/PatientEligibilityCard.tsx`, `apps/web/src/features/billing/components/PatientMembershipCard.tsx`
- API: `apps/api/app/routers/patients.py`, `apps/api/app/routers/eligibility_checks.py`, `apps/api/app/routers/membership_plans.py`, `apps/api/app/routers/documents.py` (chart-share)

## Host-facing knowledge

Open a patient to review contact, HMO, allergies, past vitals, and files. Use **Timeline** for visits, prescriptions, invoices, and documents. Use **Orders** for lab and imaging status. Mark **Allergies reviewed** once you have confirmed allergy status with the patient.

**Q: How do I combine two charts for the same person?**  
A: Owners and admins open the chart to keep, enter the other patient's ID, and merge. The other chart is archived. Related visits and bills move over.
