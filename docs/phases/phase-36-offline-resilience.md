# Phase 36: Offline / degraded-connectivity resilience

**Status:** Done
**Depends on:** Phase 31
**Unlocks:** —

**Plan reference:** `docs/workflow/planned/clinic-software-market-research-feature-gaps.md` §4.1 #5

## Production defaults (resolves plan §5 open decision 4)

- **Read-only cache, not full offline write-and-sync.** Full offline writes need real conflict resolution (two front-desk devices editing the same patient while both offline) that the plan doc itself calls "much harder" and explicitly warns not to let happen without sign-off. MVP scope: patient lookup, today's schedule, and the current SOAP note in progress stay readable/draftable during a connectivity drop; nothing new is committed to the server until connectivity returns, and the UI makes the offline/stale state visible at all times.
- SOAP note drafts made while offline queue locally and sync automatically on reconnect (single-writer assumption: the doctor's own device, not concurrent multi-device edits) — this is the one write path allowed offline, because losing an in-progress consult note mid-visit is the highest-cost failure mode. Everything else (booking, billing, prescriptions) stays online-only and shows a clear "reconnect to continue" state.

## Goal

A clinic with unreliable internet does not lose a consult in progress when the connection drops, and staff can still look up a patient and see today's schedule read-only during an outage.

## Tasks

### Backend

- [x] SOAP note persistence: corrected during implementation — Phase 7/14 never shipped an autosave endpoint, only the manual **Save** endpoint (`POST .../soap-notes`, append-only version insert) and a separate ephemeral AI-draft SSE stream that persists nothing. The offline queue targets the manual Save endpoint; append-only inserts mean there's no "overwrite newer server state" risk, only a duplicate-version risk on a retried flush.
- [x] `client_draft_token` (idempotency key) added to `SoapNoteCreate`/`SoapNote` (migration `034_soap_client_draft_token`, unique per `appointment_id`) — `create_soap_version()` returns the existing row on a retried token instead of inserting a duplicate

### Frontend

- [x] Service worker (`public/sw.js`): network-first with cache fallback for today's schedule (`/appointments`) + patient roster (`/patients`) GET only — deliberately network-first rather than literal cache-first, since every successful online fetch refreshes the cache so offline data is never staler than the last live request; documented as a design decision in `docs/architecture/offline-resilience.md`
- [x] IndexedDB queue (`lib/offlineSoapQueue.ts`) for in-progress SOAP note edits made while offline; flushed on reconnect (`lib/offlineSoapSync.ts`) with the idempotency key. Required `networkMode: "always"` on the `useMutation` call — TanStack Query's default `networkMode: "online"` pauses a mutation indefinitely while offline and never calls `mutationFn`, which would have silently defeated the whole queue (caught only via manual browser testing, not unit tests — see the doc's "critical gotcha" note)
- [x] Global connectivity banner (`components/layout/ConnectivityBanner.tsx`, mounted in `DashboardShell.tsx`) — "You're offline. Viewing cached data as of {time}." / "Reconnected, syncing…" (auto-hides after 4s)
- [x] Booking/billing/prescription submit buttons (`AppointmentNewPage`, `InvoiceNewPage`, `PrescriptionNewPage`) disabled while offline with a visible "requires a connection" message next to each, rather than hidden or silently failing

## Edge cases

- SOAP draft edited offline on two different tabs/devices for the same visit → last-write-wins with a visible timestamp is acceptable for MVP (true multi-device conflict resolution is out of scope, matches the "single-writer" default above)
- Connectivity drops mid-save (not fully offline, just flaky) → corrected during implementation: no client-side retry/backoff existed on the API client (the phase doc's assumption was wrong — verified by research before coding). The SOAP save mutation now treats _any_ non-`ApiError` exception (a real network failure, not a server rejection) as "offline," so a flaky mid-save drop falls into the same offline-queue path as being fully offline — one code path handles both.
- A queued offline draft whose appointment/parent record no longer exists by the time it flushes (`ApiError`, e.g. 404) → dropped rather than retried forever, so it doesn't jam every draft queued after it (`flushQueuedSoapDrafts`)
- Cached patient data goes stale (patient updated by another device while this one was offline) → TanStack Query's default `refetchOnReconnect: true` revalidates active queries on reconnect (no extra code needed); a dedicated "this record was updated elsewhere" diff banner was **not** built — documented as a known simplification in `docs/architecture/offline-resilience.md`, not a silent gap

## Docs to update

- [x] `docs/tech-stack.md` — read-only-cache + single-writer-SOAP-queue boundary, `vite-plugin-pwa` still deferred
- [x] `docs/mvp.md` §10 (Reliability & performance)
- [x] `docs/guides/routes/dashboard/appointments/soap.md`
- [x] `docs/architecture/offline-resilience.md` — new doc, full design + the `networkMode: "always"` gotcha
- [x] `docs/architecture/data-model.md` — `soap_notes.client_draft_token`

## Exit criteria

- [x] Killing network mid-consult does not lose the SOAP draft; it syncs automatically on reconnect — verified end-to-end in a real browser (offline → save → queued in IndexedDB → reconnect → flushed → persisted server-side as the next version), not just unit tests
- [x] Patient lookup and today's schedule remain viewable (read-only, clearly marked stale) during an outage — service worker cache fallback + global banner
- [x] Booking/billing/prescriptions clearly block rather than silently fail while offline — verified in-browser for booking; billing/prescriptions use the identical `useOnlineStatus()` + disabled pattern
- [x] `pnpm run ci:quality` green
