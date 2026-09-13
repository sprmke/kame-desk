# Chart search (`/dashboard/chart-search`)

**Status:** Documented

## Behavior

- The fixed **Patients** title and description sit above the Directory / Chart search tabs; the search form renders below the tabs in a full-width card. Switching tabs changes only the content, never the title or description.
- Semantic search over saved SOAP notes (pgvector embeddings).
- Results are real chart rows: patient name, visit date, snippet, link to the SOAP page.
- No AI-generated summaries; ranked pointers only.
- The empty state prompts the user to type at least 2 characters. Idle and no-match empties sit in that same card as the search field.

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

Phase 16 `search_charts` tool will call the same service function.

## Edge cases

- Embedding failures do not roll back SOAP saves.
- Query must be at least 2 characters.

## Implementation map

- Web: `features/chart-search/pages/ChartSearchPage.tsx`
- API: `routers/recordings.py` (chart-search route), `services/chart_search_service.py`, `services/embedding_service.py`

## Host-facing knowledge

Use **Charts** in the header to search notes by meaning (for example "migraine follow-up"). Each result opens the real saved SOAP version.
