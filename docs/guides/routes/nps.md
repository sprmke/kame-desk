# Public NPS survey reply (`/nps/{token}`)

**Status:** Documented

## Behavior

- Token-scoped page (no auth, no clinic slug in the path). A 0-10 score picker plus an optional comment.
- Single-use: once `responded_at` is set, replaying the link shows "Link invalid or expired" instead of resubmitting.
- Sent alongside (or after) the post-visit review-request, via the same email/SMS channel infra (`app/services/growth_service.py::queue_review_and_nps_requests`), triggered when a visit is marked Completed.

## Save paths

| Action               | API                                | Effect                                                                    |
| -------------------- | ---------------------------------- | ------------------------------------------------------------------------- |
| Submit score/comment | `POST /public/nps/{token}/respond` | sets `patient_survey_responses.score`, `.comment`, `.responded_at` (once) |

## RBAC

None (token is the scope).

## Implementation map

- Web: `apps/web/src/routes/nps.$token.tsx`, `apps/web/src/features/growth/pages/PublicNpsPage.tsx`
- API: `apps/api/app/routers/public_nps.py`, `apps/api/app/services/growth_service.py` (`respond_to_nps`, `get_nps_report`)

## Host-facing knowledge

Patients get this link by email or SMS shortly after their visit is marked done. It never requires login. A score of 9-10 counts as a promoter, 0-6 a detractor, in the clinic's NPS report under Insights → Reports.
