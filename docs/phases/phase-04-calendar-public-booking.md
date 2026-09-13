# Phase 4: Day calendar, drag reschedule, public self-service booking link

**Status:** Done
**Depends on:** Phase 3
**Unlocks:** Phase 5

**mvp.md reference:** §6.4 (calendar UX), §7.3 · Gap closed: #3 in §7

## Goal

Front desk gets a real calendar — daily/weekly/monthly views, per-doctor and clinic-wide, drag-and-drop reschedule, color-coded by status/doctor. Patients get a public link to request an appointment without calling.

## Prerequisites

- Phase 3 done: appointments + exclusion constraint exist and are provably safe under concurrency

## Tasks

### 1. Backend

- [ ] `GET /api/v1/appointments/available-slots` — given doctor_id + date (+ optional duration), returns real open slots respecting working hours + existing bookings + holidays (this becomes `get_available_slots`, a Tier 0 AI tool later per mvp.md §9.5 — build it as a clean, reusable service function now)
- [ ] `PATCH /api/v1/appointments/{id}/reschedule` — dedicated endpoint (distinct from generic PATCH) that re-validates the exclusion constraint and records the prior slot for audit
- [ ] Public booking endpoints (no auth, clinic-scoped by slug/token):
  - `GET /api/v1/public/clinics/{slug}` — clinic profile, hours, accepted services (safe subset only — never leak other patients' data)
  - `GET /api/v1/public/clinics/{slug}/available-slots`
  - `POST /api/v1/public/clinics/{slug}/appointment-requests` — creates an appointment in a `Scheduled` (pending confirmation) state or a distinct `requested` sub-state if the clinic wants to manually confirm public requests before they're real bookings — decide and document which (recommend: clinic setting toggle, default = auto-confirm within available slots, since the slot query already guarantees availability)
- [ ] Rate limiting / abuse protection on public endpoints (no auth = no natural throttle) — basic IP-based rate limit is enough for MVP

### 2. Frontend

- [ ] `src/features/appointments/calendar/` — day/week/month views (Schedule-X or FullCalendar resource view per tech-stack.md), dnd-kit for drag-reschedule, color coding by status and by doctor (toggleable)
- [ ] Doctor-filter and clinic-wide toggle
- [ ] Optimistic UI on drag-reschedule with rollback on server rejection (exclusion constraint conflict)
- [ ] Public booking page (`apps/web` route outside the authenticated dashboard shell, e.g. `/book/{clinicSlug}`) — mobile-first, no login required, shows real slots, confirms booking
- [ ] Clinic settings: toggle for "auto-confirm public bookings" vs. "require staff confirmation"

## Data model

No new tables if the "requested vs. confirmed" distinction is modeled via `appointment_status` values already defined in Phase 3; add a `booking_source` enum column (`staff`/`public_link`/`ai_assistant` — the last one anticipates Phase 16) to `appointments` for reporting (Phase 12) and audit clarity.

## API endpoints

| Method | Path                                                 | Auth                  |
| ------ | ---------------------------------------------------- | --------------------- |
| GET    | `/api/v1/appointments/available-slots`               | staff (clinic-scoped) |
| PATCH  | `/api/v1/appointments/{id}/reschedule`               | staff                 |
| GET    | `/api/v1/public/clinics/{slug}`                      | none                  |
| GET    | `/api/v1/public/clinics/{slug}/available-slots`      | none                  |
| POST   | `/api/v1/public/clinics/{slug}/appointment-requests` | none                  |

## Edge cases & safety

- Public endpoints must never expose another patient's name/contact/reason — only aggregate availability (free/busy), never appointment details.
- A public booking request racing a staff booking for the same slot: the exclusion constraint is still the source of truth; the loser gets a clean "slot just taken" response, not a 500.
- Drag-reschedule across working-hours boundaries or into a holiday must be blocked client-side and re-validated server-side.
- Public booking link must be per-clinic (slug or token), never a single global booking page that could leak which clinics exist on the platform to each other.
- Rate limit public endpoints; log repeated failures (e.g. slot-scraping patterns) without logging patient-identifying data from failed attempts.

## Testing

- pytest: available-slots correctness (boundary cases: exactly at open/close, holiday, already-booked), public booking race condition, rate limiting
- Vitest: drag-reschedule optimistic update + rollback
- Playwright: full public booking flow (visit link → pick slot → confirm → appears on staff calendar)

## Docs to update in this phase

- `docs/guides/routes/book.md` (public booking page) and `docs/guides/routes/dashboard/appointments/calendar.md` — per `route-guides.mdc`, including Host-facing (front-desk-facing) Q&A
- `docs/architecture/api-conventions.md` — document the public (unauthenticated) endpoint pattern distinctly from authenticated ones

## Exit criteria

- [ ] Staff can view/drag-reschedule appointments across day/week/month, per-doctor and clinic-wide
- [ ] A patient can book a real appointment through the public link without calling, and it appears correctly on the staff calendar
- [ ] Race conditions between public and staff bookings resolve safely (tested)
- [ ] `pnpm run ci:quality` + Playwright green
