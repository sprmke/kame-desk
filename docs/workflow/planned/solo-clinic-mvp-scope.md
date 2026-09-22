# Solo-clinic MVP reset

**Status:** In progress (docs + clinic UI hide).
**PRD:** [`docs/mvp.md`](../../mvp.md) v1.2.

Rewrite DoctorDesk around a **1-doctor + secretary** clinic. Keep the daily loop (calendar, SOAP, Rx, billing including HMO) plus the full staff AI assistant. Hide multi-clinic, multi-doctor, and growth extras from staff UI without deleting APIs or tables. **Multi-doctor clinics are Phase 2.**

activity-log: N/A — product-surface hide and documentation; no new mutating capabilities.

## Keep (clinic-facing)

Today, Schedule (one doctor), Waiting room, Patients, SOAP + specialty templates, Prescriptions, Billing (invoices + claims + eligibility + LOA), Documents, email reminders, simple reports + activity log, staff AI assistant, thin settings.

## Hide (Phase 2+)

Per-doctor calendar columns, rooms, waitlist, extra-doctor / admin invite, organization / add-clinic, patient portal, public booking FAQ bot, semantic chart search tab, recall campaigns, WhatsApp, NPS/reviews/memberships, BIR PTU/CAS UI.

## Implementation

Hide from nav, onboarding, and settings. Redirect leftover staff routes. Keep FastAPI routers and tests.

## Related

Design overhaul Phases 44–47 only polish **kept** screens.
