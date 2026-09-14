# Route guides

Per-page behavior specs for `apps/web` routes. Index only — guides added as phases ship real pages.

Header convention shared by every dashboard route: one `<h1>`, then any tab bar, then the content. Page descriptions are opt-in and must not restate the title or nav label (anti-slop B7; `ui-minimal-copy.mdc` wins). In a tabbed section (`SectionHubShell`) the title is **fixed** and equals the sidebar nav label, so switching tabs swaps only the content; tab pages contribute buttons through `SectionHeaderActions` instead of a header of their own. See `docs/architecture/design-language.md`.

| Route                                              | Guide                                                                                  | Status     |
| -------------------------------------------------- | -------------------------------------------------------------------------------------- | ---------- |
| Unmatched URL (404)                                | [not-found.md](./not-found.md)                                                         | Documented |
| `/login`                                           | [login.md](./login.md)                                                                 | Documented |
| `/forgot-password`                                 | [forgot-password.md](./forgot-password.md)                                             | Documented |
| `/reset-password`                                  | [reset-password.md](./reset-password.md)                                               | Documented |
| `/verify-email`                                    | [verify-email.md](./verify-email.md)                                                   | Documented |
| `/register`                                        | (Phase 1 auth shell; `?plan=` from `/pricing`)                                         | Documented |
| `/pricing`                                         | [pricing.md](./pricing.md)                                                             | Documented |
| `/platform`                                        | [platform.md](./platform.md)                                                           | Documented |
| `/onboarding`                                      | [onboarding.md](./onboarding.md)                                                       | Documented |
| `/dashboard`                                       | [dashboard/index.md](./dashboard/index.md)                                             | Documented |
| `/dashboard/patients/:patientId/invoices/new`      | [dashboard/billing/invoices.md](./dashboard/billing/invoices.md)                       | Documented |
| `/dashboard/patients/:patientId/invoices/:id`      | [dashboard/billing/invoices.md](./dashboard/billing/invoices.md)                       | Documented |
| `/dashboard/billing`                               | [dashboard/billing/invoices.md](./dashboard/billing/invoices.md) (hub)                 | Documented |
| `/dashboard/billing/invoices`                      | [dashboard/billing/invoices.md](./dashboard/billing/invoices.md)                       | Documented |
| `/dashboard/billing/claims`                        | [dashboard/billing/claims.md](./dashboard/billing/claims.md)                           | Documented |
| `/dashboard/billing/claims/:claimId`               | [dashboard/billing/claims.md](./dashboard/billing/claims.md)                           | Documented |
| `/dashboard/billing/eligibility`                   | [dashboard/billing/eligibility.md](./dashboard/billing/eligibility.md)                 | Documented |
| `/dashboard/billing/loa`                           | [dashboard/billing/loa.md](./dashboard/billing/loa.md)                                 | Documented |
| `/dashboard/outreach/reminders`                    | [dashboard/reminders.md](./dashboard/reminders.md)                                     | Documented |
| `/dashboard/outreach/recalls`                      | [dashboard/recalls.md](./dashboard/recalls.md)                                         | Documented |
| `/dashboard/documents/generate`                    | [dashboard/documents/generate.md](./dashboard/documents/generate.md)                   | Documented |
| `/dashboard/documents/templates`                   | [dashboard/settings/document-templates.md](./dashboard/settings/document-templates.md) | Documented |
| `/dashboard/insights/reports`                      | [dashboard/reports.md](./dashboard/reports.md)                                         | Documented |
| `/dashboard/insights/audit-log`                    | [dashboard/audit-log.md](./dashboard/audit-log.md)                                     | Documented |
| `/dashboard/patients/chart-search`                 | [dashboard/chart-search.md](./dashboard/chart-search.md)                               | Documented |
| `/dashboard/patients`                              | [dashboard/patients/index.md](./dashboard/patients/index.md)                           | Documented |
| `/dashboard/patients/new`                          | [dashboard/patients/new.md](./dashboard/patients/new.md)                               | Documented |
| `/dashboard/patients/:id`                          | [dashboard/patients/detail.md](./dashboard/patients/detail.md)                         | Documented |
| `/dashboard/patients/:patientId/prescriptions/new` | [dashboard/patients/prescriptions.md](./dashboard/patients/prescriptions.md)           | Documented |
| `/dashboard/patients/:patientId/documents/new`     | [dashboard/patients/documents.md](./dashboard/patients/documents.md)                   | Documented |
| `/dashboard/appointments`                          | [dashboard/appointments/index.md](./dashboard/appointments/index.md)                   | Documented |
| `/dashboard/appointments/new`                      | [dashboard/appointments/new.md](./dashboard/appointments/new.md)                       | Documented |
| `/dashboard/appointments/calendar`                 | [dashboard/appointments/calendar.md](./dashboard/appointments/calendar.md)             | Documented |
| `/dashboard/appointments/:appointmentId/soap`      | [dashboard/appointments/soap.md](./dashboard/appointments/soap.md)                     | Documented |
| `/book/:clinicSlug`                                | [book.md](./book.md)                                                                   | Documented |
| `/dashboard/waiting-room`                          | [dashboard/waiting-room.md](./dashboard/waiting-room.md)                               | Documented |
| `/dashboard/notifications`                         | [dashboard/notifications.md](./dashboard/notifications.md)                             | Documented |
| `/dashboard/settings/account`                      | [dashboard/settings/account.md](./dashboard/settings/account.md)                       | Documented |
| `/dashboard/settings`                              | [dashboard/settings/account.md](./dashboard/settings/account.md) (layout)              | Documented |
| `/dashboard/settings/clinic/details`               | [dashboard/settings/clinic.md](./dashboard/settings/clinic.md)                         | Documented |
| `/dashboard/settings/clinic/hours`                 | [dashboard/settings/clinic.md](./dashboard/settings/clinic.md)                         | Documented |
| `/dashboard/settings/clinic/rooms`                 | [dashboard/settings/clinic.md](./dashboard/settings/clinic.md)                         | Documented |
| `/dashboard/settings/clinic/branding`              | [dashboard/settings/clinic.md](./dashboard/settings/clinic.md)                         | Documented |
| `/dashboard/settings/clinic/compliance`            | [dashboard/settings/clinic.md](./dashboard/settings/clinic.md)                         | Documented |
| `/dashboard/settings/team`                         | [dashboard/settings/team.md](./dashboard/settings/team.md)                             | Documented |
| `/dashboard/settings/services`                     | [dashboard/settings/services.md](./dashboard/settings/services.md)                     | Documented |
| `/dashboard/settings/payers`                       | [dashboard/settings/payers.md](./dashboard/settings/payers.md)                         | Documented |
| `/dashboard/settings/doctor`                       | [dashboard/settings/doctor.md](./dashboard/settings/doctor.md)                         | Documented |
| `/dashboard/settings/document-templates`           | [dashboard/settings/document-templates.md](./dashboard/settings/document-templates.md) | Documented |
| `/dashboard/settings/notifications`                | [dashboard/settings/notifications.md](./dashboard/settings/notifications.md)           | Documented |
| `/dashboard/settings/assistant`                    | [dashboard/settings/assistant.md](./dashboard/settings/assistant.md)                   | Documented |
| `/dashboard/settings/organization`                 | [dashboard/settings/organization.md](./dashboard/settings/organization.md)             | Documented |
| `/dashboard/settings/organization/clinics/new`     | [dashboard/settings/organization.md](./dashboard/settings/organization.md)             | Documented |
| `/dashboard/settings/plan`                         | [dashboard/settings/plan.md](./dashboard/settings/plan.md)                             | Documented |
| `/dashboard/settings/membership-plans`             | [dashboard/settings/membership-plans.md](./dashboard/settings/membership-plans.md)     | Documented |
| `/dashboard/reminders`                             | Redirects to `/dashboard/outreach/reminders`                                           | Documented |
| `/dashboard/recalls`                               | Redirects to `/dashboard/outreach/recalls`                                             | Documented |
| `/dashboard/reports`                               | Redirects to `/dashboard/insights/reports`                                             | Documented |
| `/dashboard/chart-search`                          | Redirects to `/dashboard/patients/chart-search`                                        | Documented |
| `/dashboard/audit-log`                             | Redirects to `/dashboard/insights/audit-log`                                           | Documented |
| `/reminders/{token}`                               | [reminders.md](./reminders.md)                                                         | Documented |
| `/nps/{token}`                                     | [nps.md](./nps.md)                                                                     | Documented |
| `/referral-chart/{token}`                          | [referral-chart.md](./referral-chart.md)                                               | Documented |
| `/patient-portal/:slug/*`                          | [patient-portal.md](./patient-portal.md)                                               | Documented |

Template: `docs/guides/_template.md`
