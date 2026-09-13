# Reports (`/dashboard/reports`)

**Status:** Documented

## Behavior

- The fixed **Insights** title and description sit above the Reports / Activity log tabs; the report controls render below the tabs. **Export CSV** is contributed to the section header by this tab (hidden on the NPS tab, which has no CSV export). Switching tabs changes only the content, never the title or description.
- Five report types via a segmented control: appointments, revenue, patient growth, top diagnoses, NPS.
- One date-range picker plus a `group_by` filter (day/week/month; doctor and service type where applicable) — hidden on the top-diagnoses and NPS tabs. The range picker opens a two-month calendar: click the start, then the end. The report reloads only after the second click.
- Progress-bar summary per period; revenue tab also shows today/week/month totals.
- NPS tab lists one row per month: responses vs. surveys sent, promoter/passive/detractor counts, and the computed NPS score (promoters − detractors, as a percentage of responses).
- The report picker and date range name the current scope, and the empty state suggests changing the date range or grouping.
- Appointment bars open `/dashboard/appointments` with `from` / `to` / `doctorId`. Revenue bars open invoices with the same date range.
- Doctor grouping shows names, not UUIDs.
- CSV export uses the same filters and RBAC as the JSON endpoints.

## Save paths

Read-only. Data is aggregated server-side from appointments, payments, patients, and signed SOAP notes.

| Report         | API                                | RBAC           |
| -------------- | ---------------------------------- | -------------- |
| Appointments   | `GET /reports/appointments`        | owner, admin   |
| Revenue        | `GET /reports/revenue`             | owner, admin   |
| Patient growth | `GET /reports/patient-growth`      | owner, admin   |
| Top diagnoses  | `GET /reports/top-diagnoses`       | owner, doctor  |
| NPS            | `GET /reports/nps`                 | owner, admin   |
| CSV export     | `GET /reports/{report}/export.csv` | same as report |

Query params: `from_date`, `to_date` (ISO dates), optional `group_by`, optional `doctor_id`.

## Implementation map

- Web: `apps/web/src/features/reports/pages/ReportsPage.tsx`
- API: `apps/api/app/routers/reports.py`, `apps/api/app/services/report_service.py` (appointments/revenue/patient-growth/top-diagnoses), `apps/api/app/services/growth_service.py::get_nps_report` (NPS)
- Dashboard revenue widget on `/dashboard` reads `GET /clinics/{id}/revenue-summary`. The dashboard 14-day chart and this Reports page both read `GET /reports/appointments`.

## Host-facing knowledge

Reports show clinic-wide trends. Top diagnoses is limited to doctors and owners because it uses clinical data in aggregate. Admins can see operational and financial reports but not diagnosis rankings.
