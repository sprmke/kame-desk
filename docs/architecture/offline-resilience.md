# Offline / degraded-connectivity resilience (Phase 36)

**Status:** Documented

**Production default:** read-only cache, not full offline write-and-sync. Full offline writes need real conflict resolution (two front-desk devices editing the same patient while both offline) that is explicitly out of scope for MVP — see `docs/workflow/planned/clinic-software-market-research-feature-gaps.md` §5 open decision 4. The one write path allowed offline is a SOAP note in progress, single-writer (the doctor's own device) — losing an in-progress consult note mid-visit is the highest-cost failure mode this phase protects against. Booking, billing, and prescriptions stay online-only.

## Connectivity detection

`apps/web/src/lib/onlineStatus.ts` — `useOnlineStatus()` wraps `navigator.onLine` + the browser's `online`/`offline` events via `useSyncExternalStore` (SSR-safe: assumes online on the server, since `navigator` doesn't exist there). This is the one source of truth every offline-aware component reads from — no page re-implements its own online detection.

## Global connectivity banner

`apps/web/src/components/layout/ConnectivityBanner.tsx`, mounted once in `DashboardShell.tsx` above the header (visible on every `/dashboard/*` route). Two states:

- Offline: "You're offline. Viewing cached data as of {time}. Booking, billing, and prescriptions require a connection."
- Just reconnected: "Reconnected, syncing…" for 4 seconds, then disappears.

The reconnect timer is driven by a `useRef` flag inside an effect that depends only on `online` (not on the state it sets) — an earlier version depended on `offlineSince` too, which caused the effect to re-run when it cleared that same state, immediately cancelling its own timeout via cleanup. Keep that dependency array narrow if this component changes.

## Booking/billing/prescriptions: block, don't hide

`AppointmentNewPage.tsx`, `InvoiceNewPage.tsx`, `PrescriptionNewPage.tsx` each call `useOnlineStatus()` and add `!online` to their submit button's `disabled` condition, plus a visible "requires a connection" message next to it. The action stays visible and explained rather than disappearing or silently failing on submit.

## SOAP draft offline queue (the one allowed offline write)

- **Storage:** `apps/web/src/lib/offlineSoapQueue.ts` — a thin hand-rolled IndexedDB wrapper (no new dependency), database `doctordesk-offline`, object store `soap-drafts` keyed by `clientDraftToken`. `enqueueSoapDraft`/`listQueuedSoapDrafts`/`removeQueuedSoapDraft`; `generateClientDraftToken()` makes a `offline-<uuid>` token.
- **Save flow:** `SoapNotePage.tsx`'s save mutation checks `navigator.onLine` before sending; if offline (or the fetch throws something other than `ApiError`, i.e. a real network failure rather than a server rejection) it queues the payload — tagged with a fresh `client_draft_token` — into IndexedDB instead of failing, and shows "Saved locally — will sync automatically once you're back online."
- **Critical gotcha:** the mutation passes `networkMode: "always"` to `useMutation`. TanStack Query's default `networkMode: "online"` pauses a mutation indefinitely while `navigator.onLine` is false — it never even calls `mutationFn`, which would silently defeat this whole offline-queue design (the button gets stuck on "Saving…" forever). This was caught by manual browser testing, not by unit tests (which mock the API client and never touch the real online-gating), so if this regresses, unit tests won't catch it — watch for it in QA whenever the SOAP save mutation is touched.
- **Sync flow:** `apps/web/src/lib/offlineSoapSync.ts` — `useOfflineSoapSync()`, mounted once in `DashboardShell.tsx`, flushes the queue on mount and on every `window` `online` event. `flushQueuedSoapDrafts()` processes queued drafts oldest-first: a network failure stops the loop (retried on the next reconnect); a server rejection (`ApiError`, e.g. the appointment was deleted while offline) can never succeed on retry, so that entry is dropped and the loop continues rather than jamming every draft queued after it.
- **Backend idempotency:** `SoapNote.client_draft_token` (migration `034_soap_client_draft_token`, unique per `appointment_id` — Postgres allows multiple NULLs so normal online saves are unaffected) plus `create_soap_version()` in `soap_service.py` returning the existing row instead of inserting a duplicate when the same token is retried (e.g. the flush succeeds server-side but the client never sees the response before a tab close, then retries on next load).

## Read-only cache: today's schedule + patient roster

`apps/web/public/sw.js` — network-first with a cache fallback, scoped to exactly two endpoints (matched by `URL.pathname.endsWith("/appointments")` / `.endsWith("/patients")`, GET only): every successful online fetch refreshes the cache, and a failed fetch (offline) serves the last cached response instead of erroring. This is a deliberate deviation from the literal "cache-first" phrasing in the phase's own task list — network-first guarantees the data is never staler than the last successful request while online, which matters more for a schedule that changes throughout the day than pure cache-first would. Nothing else is cached — sub-resource endpoints (`/patients/{id}`, `/appointments/{id}/...`) and every write always hit the network.

Registration (`apps/web/src/lib/pwa.ts`, called from `__root.tsx`) only runs in production builds (`import.meta.env.DEV` skips it) — to exercise the cache locally, run `pnpm --filter @doctordesk/web build && pnpm --filter @doctordesk/web preview` rather than the dev server.

## Known limitations (by design, not gaps)

- Two tabs/devices editing the same SOAP note offline: last-write-wins with a visible timestamp — true multi-device conflict resolution is out of scope for MVP (see the single-writer default above).
- Offline patient/appointment data can go stale if another device changes it while this one is offline — TanStack Query's default `refetchOnReconnect: true` (unchanged, no extra code needed) revalidates on reconnect, but there's no explicit "this record was updated elsewhere" diff banner.
- Reschedule-request and other non-SOAP writes have zero offline path — this is intentional per the production default, not an oversight.
