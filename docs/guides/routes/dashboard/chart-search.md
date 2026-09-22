# Chart search (`/dashboard/patients/chart-search`)

**Status:** Out of MVP (v1.2). Redirects to Patients. Find the person in Directory, then open Records on the chart.

## Behavior

- `/dashboard/patients/chart-search` and `/dashboard/chart-search` redirect to `/dashboard/patients`.
- No Patients tab, no command-palette entry. Search the patient by name, contact, or ID, then open Records on the chart.
- Semantic search over saved SOAP notes (pgvector) stays in the API and in the staff assistant `search_charts` tool. The page component is unused in this MVP.

## Save paths

| Action        | API                                               | DB effect                     |
| ------------- | ------------------------------------------------- | ----------------------------- |
| Search        | `GET /api/v1/clinics/{id}/chart-search?q=`        | read (vector similarity)      |
| Embed on save | ARQ `generate_soap_embedding_job` after SOAP save | `soap_note_embeddings` upsert |

## Validation

- Roles: `doctor`, `owner` only.
- Doctors are scoped to their own appointments; owners see all clinic charts.

## RBAC

| Role              | Search                |
| ----------------- | --------------------- |
| owner             | all clinic charts     |
| doctor            | own appointments only |
| admin / reception | blocked               |

## AI assistant parity

`search_charts` calls the same service. There is no clinic tab for the same search.

## Edge cases

- Embedding failures do not roll back SOAP saves.
- Query must be at least 2 characters.
- Bookmarked Chart search URLs land on Patients.

## Implementation map

- Web: `apps/web/src/routes/dashboard.patients.chart-search.tsx`, `apps/web/src/routes/dashboard.chart-search.tsx` (redirects). Page: `features/chart-search/pages/ChartSearchPage.tsx` (unused in MVP).
- API: `routers/recordings.py` (chart-search route), `services/chart_search_service.py`, `services/embedding_service.py`

## Host-facing knowledge

Open **Patients**, search by name, contact, or ID, then open the person. **Records** on the chart opens that SOAP note. There is no Chart search tab in this MVP.
