# Public referral chart share (`/referral-chart/{token}`)

**Status:** Documented

## Behavior

- Token-scoped page (no auth, no recipient account required). Read-only: recent diagnoses and a vitals-trend table, the same shape as Phase 37's patient-portal chart summary.
- Created from a referral letter document on the patient's Documents tab (**Share chart summary** → **Copy link**). Only `document_type == "referral_letter"` documents can create a share.
- The share link expires 7 days after creation (`CHART_SHARE_TTL`); an expired or unknown token returns an error state ("This link is invalid or has expired") in a card instead of a 500. Empty diagnoses and vitals sections also sit in a card.
- Creating a new share for the same document rotates the token — the old link stops working immediately.

## Save paths

| Action                 | API                                  | Effect                                                                                                                                 |
| ---------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| Create share link      | `POST /documents/{id}/chart-share`   | sets `chart_share_token_hash` (SHA-256 of a fresh `secrets.token_urlsafe(32)`), `chart_share_expires_at`; logs `referral.chart_shared` |
| Resolve share (public) | `GET /public/referral-chart/{token}` | reuses `patient_portal_service.get_chart_summary()` — never exposes raw SOAP text                                                      |

## RBAC

Creating a share: clinic staff with document read access. Resolving a share: none (token is the scope).

## Implementation map

- Web: `apps/web/src/routes/referral-chart.$token.tsx`, `apps/web/src/features/growth/pages/PublicReferralChartPage.tsx`; share button in `apps/web/src/features/patients/pages/PatientDetailPage.tsx`
- API: `apps/api/app/routers/documents.py` (create), `apps/api/app/routers/public_documents.py` (resolve), `apps/api/app/services/document_service.py` (`create_chart_share`, `resolve_chart_share`)

## Host-facing knowledge

Use **Share chart summary** on a referral letter to hand a specialist a read-only snapshot without giving them a login. The link works for 7 days; generate a new one if it expires or if you sent it to the wrong recipient (the old link stops working the moment you do).
