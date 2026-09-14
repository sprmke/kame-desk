# UI/UX refinement + native-feeling mobile — detailed plan

**Status:** Done (PWA/offline workstream F deferred).
**Type:** Cross-cutting polish initiative (not a new `mvp.md` scope item — all 19 build phases are already `Done`; this raises the craft bar on what's shipped, it does not add product scope).
**Reference for "what good looks like":** `/Users/michaelmanlulu/Projects/personal-projects/kame-homes` (`ui/` workspace).
**Do not implement from this document directly** — this is the saved output of a planning pass (`.cursor/rules/plan-mode.mdc`). Convert sections into real work only after the open decisions in §4 are resolved with the user, ideally by turning each wave in §6 into its own tracked task/PR.

---

## 1. Why this plan looks different from "port kame-homes wholesale"

Before writing tasks, I audited both codebases directly (not from memory). Two things change the shape of this plan versus the original ask:

1. **kame-desk's component foundation is more mature than it looks from the outside.** It's a real shadcn/ui + Radix system (`apps/web/components.json`, 43 files in `apps/web/src/components/ui/`), not raw `<select>`/`<input type="checkbox">` HTML — a repo-wide grep for native form elements returned zero hits. `Button` already has a `cva` variant system, a `loading` prop, and `active:scale-[0.98]` tap feedback. `Switch` is a smooth Radix-based toggle. `SlidingActivePill`/`SlidingTabs` already exist and already use the exact measurement technique (`getBoundingClientRect` + absolutely-positioned pill) that kame-homes uses for its animated tab/dock indicator. So "custom tabs, custom switch, checkbox, buttons" from the original ask are **already built** — the gap is in animation _quality_ and a few missing primitive categories, not raw existence.
2. **kame-desk has a documented, deliberate design constraint that this plan must consciously override, not silently ignore.** `DESIGN.md` states: _"Motion: 150ms, `cubic-bezier(0.4,0,0.2,1)`... nothing longer, no page-transition animation."_ That's the right call for a v1 clinical tool, but it's also exactly the constraint that makes the current UI feel flatter than kame-homes. Raising the motion budget is a real design-system change, not a bug fix — it needs the sign-off in §4, and `DESIGN.md` / `docs/architecture/design-system.md` must be updated in the same change that ships it (per this repo's "docs are the source of truth" rule).

The real gap, concretely:

| Area                                                                        | kame-desk today                                                                                                                                                                                                                | kame-homes reference                                                                                                                                                                            | Verdict                                                                   |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Form primitives (select, checkbox, radio, switch, date/time picker, dialog) | All componentized, Radix-based                                                                                                                                                                                                 | Same, mostly hand-rolled instead of Radix (e.g. `Switch` isn't Radix there)                                                                                                                     | **No gap** — kame-desk's Radix-based approach is arguably better; keep it |
| Tabs / segmented control                                                    | `SlidingActivePill` exists, CSS `transition duration-150`                                                                                                                                                                      | Same measurement technique + `framer-motion` spring                                                                                                                                             | **Small gap** — upgrade the transition, not the architecture              |
| Buttons                                                                     | `cva` variants, loading state, tap scale                                                                                                                                                                                       | Same + `hover:brightness`/glow, more variants                                                                                                                                                   | **Small gap** — depth/hover polish only                                   |
| Skeleton loaders                                                            | One generic `Skeleton` (`animate-pulse` box), reused ad hoc across 13 pages                                                                                                                                                    | Per-page/per-component skeleton catalog that mirrors real DOM structure 1:1, zero layout shift                                                                                                  | **Real gap** — this is the single highest-leverage item in the whole plan |
| Animation system                                                            | `tw-animate-css` only, used for Radix enter/exit; no keyframe catalog; no page/list transitions                                                                                                                                | Custom keyframe catalog (`fade-up`, `scale-in`, `stage-in-forward`, etc.), `framer-motion` for spring-driven pill/list/page motion, reduced-motion-aware everywhere                             | **Real gap**                                                              |
| Native mobile shell                                                         | Responsive breakpoints only; every modal is a centered `Dialog`/`Sheet` regardless of viewport; no bottom tab bar; no safe-area handling; no tap feedback outside buttons                                                      | `ResponsiveModal` (bottom sheet <lg, dialog ≥lg), `BottomSheet` w/ drag handle, `BottomTabBar`, safe-area insets everywhere, `.native-press`/`.interactive-scale` utility classes on cards/rows | **Real gap** — this is the second highest-leverage item                   |
| Empty / error states                                                        | No dedicated component found                                                                                                                                                                                                   | Not deeply audited, but kame-desk has none at all                                                                                                                                               | **Real gap**, independent of kame-homes — worth fixing regardless         |
| PWA / offline                                                               | Static `manifest.webmanifest` only (from phase 19's "installability" checkbox); no service worker, no `vite-plugin-pwa`, no offline banner                                                                                     | Full `vite-plugin-pwa` + Workbox, install/update prompts, offline banner                                                                                                                        | **Gap exists but likely lower priority** — see §4.3                       |
| Agent rules/skills for UI work                                              | `.cursor/rules/mobile-responsive.mdc` is a thin 17-line rule that **points to `.agent/skills/mobile-responsive/SKILL.md`, which does not exist** (dangling reference — confirmed by `ls`); no `components.mdc`, no motion rule | Long, detailed `mobile-responsive.mdc` + a hand-synced `SKILL.md` twin; `components.mdc`; canonical `DESIGN.md` with an explicit "Agent Prompt Guide" section                                   | **Real gap**                                                              |

Everything below is scoped against this table, not against "make it look like kame-homes."

---

## 2. Non-negotiable constraints carried over from CLAUDE.md / DESIGN.md

- **Identity stays "clinical, calm, trustworthy" — not hospitality-styled.** Do not import kame-homes' gradients, confetti bursts (`ConfettiBurst.tsx`), marketing hero treatments, or playful copy tone. This plan ports _technique_ (spring math, layout-matching skeletons, safe-area handling, responsive modal pattern), not _visual style_.
- **No business logic moves into `apps/web`.** Everything here is presentation-layer only.
- **`prefers-reduced-motion` must be respected everywhere new motion is added** — kame-desk's `SlidingActivePill` already does this correctly (`motion-reduce:transition-none`); every new animated component must match that bar, including any `framer-motion` usage (`useReducedMotion()` + fallback, as kame-homes' `PageTransition.tsx` already models).
- **Docs-are-source-of-truth applies to this work like any other.** Every wave below ends with the matching doc update — see §7.
- **Mobile/tablet is not a separate track from "the app"** — this repo's cross-cutting phase rule #9 already requires every screen to work at 375–1024px+ with 44×44px touch targets. This plan raises that bar to "feels native," it doesn't introduce the responsiveness requirement.
- **`tech-stack.md` is authoritative for dependency choices.** It currently has no opinion on `framer-motion`, `vaul`, `cmdk`, or `vite-plugin-pwa` — any new dependency introduced by this plan must get a short "Explicitly chosen" entry added to `docs/tech-stack.md` in the same change (see §4.2 and §7).

---

## 3. Design principle for "native mobile," specific to a clinic front desk

kame-homes optimizes for a consumer-facing booking/marketing app. kame-desk's mobile surface is a **front-desk/doctor operational tool**, often on a shared tablet. Native-feeling here means:

- Bottom sheets for on-the-go actions (check in a walk-in, mark arrived, quick reschedule) instead of centered dialogs that feel like a desktop app squeezed onto glass.
- A persistent bottom tab/dock for the handful of screens front desk lives in during a shift (Today/Calendar, Waiting Room, Patients, More) — not a hamburger menu that hides frequently-used destinations.
- Tap feedback and swipe affordances on list rows that carry real actions (waiting-room queue rows, appointment list rows) — e.g. swipe an appointment row to reveal Confirm/Cancel, the way a native queue-management app would, not a hover-only desktop affordance nobody can trigger on glass.
- Safe-area awareness for iPad/tablet notches and browser chrome — most clinics will run this in a browser or as an installed PWA on a shared iPad, not as a native binary, so `env(safe-area-inset-*)` matters wherever a sheet/tab bar touches a screen edge.
- **No pull-to-refresh** as a default recommendation — real-time data already arrives via the existing WebSocket-backed waiting-room queue (Phase 5); adding pull-to-refresh on top of a live socket connection would be confusing (fighting realtime with a manual gesture). Skip it unless a specific screen turns out to need a manual re-sync affordance.

---

## 4. Open decisions — resolve before implementation starts

These are genuine trade-offs, not implementation details, so implementation shouldn't start until they're answered.

### 4.1 Motion budget increase

Replace the current "150ms, nothing longer, no page-transition animation" rule with a tiered budget, e.g.:

- **Micro (100–180ms, ease-out):** hover/press/focus state changes — keep as-is today.
- **Transition (200–320ms, spring or `cubic-bezier(0.22,1,0.36,1)`):** tab pill slides, sheet/dialog enter-exit, list item enter/stagger.
- **Page-level (250–350ms, translate+fade only, no cross-fade):** route-level entrance for dashboard sub-pages, styled like kame-homes' "stage push" (opaque incoming view slides over the outgoing one) rather than a marketing cross-fade — this keeps it feeling like navigation, not decoration.

This directly reverses a documented decision in `DESIGN.md`. Needs explicit user sign-off, then a `DESIGN.md` rewrite of the Motion section, before any component below uses more than 150ms.

### 4.2 New dependency: `framer-motion` (or not)

kame-homes' spring-based pill/page/list motion is `framer-motion`-driven. Options:

- **(a)** Adopt `framer-motion`, matching kame-homes exactly (fastest path to the same feel, one more runtime dependency, ~50KB gzipped).
- **(b)** Stay CSS/Web-Animations-API only (extend `tw-animate-css` + hand-written keyframes + `element.animate()` for the pill), avoiding the dependency at the cost of hand-rolling spring-like easing curves.

Recommendation: **(a)**, scoped narrowly (tab pill, sheet/dialog transitions, list stagger, route transition) — don't sprinkle it everywhere. Needs a one-line addition to `docs/tech-stack.md`'s dependency list either way.

### 4.3 PWA / offline scope

Phase 19 already ships a static `manifest.webmanifest` (installability). Going further (service worker, offline banner, install/update prompts à la kame-homes) is a meaningfully bigger lift with real edge cases (stale cached patient data, offline writes) that the original ask didn't specifically request. Recommendation: **defer full offline PWA to a separate, explicitly-scoped follow-up** and keep this plan's PWA-adjacent work limited to safe-area/viewport meta correctness (§6.5) and confirming the existing manifest still install-prompts correctly after the visual changes below. Flag this decision to the user rather than silently doing (or silently skipping) the bigger lift.

### 4.4 Swipe-actions on list rows

Real value (waiting-room queue, appointment list) but real risk (accidental swipes triggering a cancel on a shared tablet during a busy shift, conflicts with native OS back-swipe gesture on some browsers). Recommendation: ship swipe-to-reveal-actions (not swipe-to-execute) — the swipe exposes action buttons, a second explicit tap executes, mirroring iOS Mail rather than a one-swipe destructive action. Needs sign-off since it touches operational safety, not just visuals.

---

## 5. Workstreams (the actual task list)

### A. Motion & animation foundation (blocks B, C, D — do first)

- [x] Resolve §4.1 and §4.2 with the user; update `DESIGN.md` Motion section and `docs/architecture/design-system.md`'s motion tokens to match.
- [x] Add `framer-motion` (if 4.2a) to `apps/web/package.json`; add the "Explicitly chosen" entry to `docs/tech-stack.md`.
- [x] Define a shared spring/easing constants file (`apps/web/src/lib/motion.ts`) — port the concept of kame-homes' `SLIDING_PILL_SPRING` but re-tune stiffness/damping for a calmer, less bouncy feel consistent with "clinical, not playful" (e.g. higher damping, no overshoot).
- [x] Extend the Tailwind `@theme` keyframes in `apps/web/src/styles.css` with a small, deliberate catalog: `fade-in`, `fade-up`, `scale-in`, `slide-in-from-bottom` (for sheets), `stage-in-forward`/`stage-out-forward` (for page-level nav). Do **not** port kame-homes' playful ones (`turtle-blink`, `think-dot`, `ai-scan`, `bounce`, `float`, confetti) — those belong to a different product tone.
- [x] Add `.native-press` (`motion-safe:active:scale-[0.97]`) and `.interactive-lift` utility classes to `styles.css`, applied to tappable cards/list rows that currently have no press feedback (waiting-room cards, patient list rows, appointment list rows).
- [x] Verify every new animated class/component has a `motion-reduce`/`useReducedMotion()` path, matching the existing `SlidingActivePill` bar.

### B. Component craft polish (existing primitives — refine, don't rebuild)

- [x] `SlidingActivePill` / `SlidingTabs`: swap the plain `transition-[left,top,width,height] duration-150` for the new spring token from workstream A; verify it still respects `motion-reduce`.
- [x] `Button`: add `hover:shadow-theme-md` / subtle `hover:brightness-[1.02]` depth on `default`/`destructive` variants only (skip gradients — stays flat-color per `DESIGN.md`); leave `active:scale-[0.98]` as-is (already correct).
- [x] `Switch`, `Checkbox`, `RadioGroup`: audit focus-visible ring consistency and thumb transition timing against the new motion tokens; these are functionally fine today, this is a timing/consistency pass only.
- [x] `DatePicker`/`TimePicker`/`Calendar`: add enter/exit transition to the popover content (currently relies on default Radix Popover behavior) using the new `scale-in`/`fade-in` keyframes.
- [x] `Dialog`/`AlertDialog`/`Sheet`: standardize enter/exit on the new transition tier (200–320ms) instead of whatever `tw-animate-css` defaults currently apply; confirm consistent backdrop treatment.
- [x] `Skeleton`: keep the primitive itself, but see workstream C — the real work is in _how it's used_, not the primitive.
- [x] Command palette (`CommandPalette.tsx`): keep hand-rolled (no `cmdk` dependency needed for its current scope per Phase 19); apply the new dialog transition tier and add subtle list-item stagger on open, matching kame-homes' polish without adding a dependency.

### C. Skeleton loader overhaul (highest-leverage item)

- [x] Establish the pattern: one skeleton sub-component per real component, matching its exact DOM structure (spacing, line counts, image/avatar placeholders) — comment convention `// Mirrors <RealComponent>'s markup` so drift is visible in review, copying kame-homes' `GuestPageSkeletons.tsx` convention.
- [x] Create `apps/web/src/components/skeletons/` (or per-feature `*.skeleton.tsx` files, follow whichever convention the codebase's existing feature-folder pattern favors) covering, at minimum, the 13 pages that currently use the generic `Skeleton` box ad hoc: `AppointmentListPage`, `ActivityTrail`, `AuditLogPage`, `InvoiceDetailPage`, `PublicBookingPage`, `ChartSearchPage`, `DashboardOverviewPage`, `PatientDetailPage`, `PatientListPage`, `ReportsPage`, `AssistantSettingsPage`, `DoctorProfilePage`, `WaitingRoomPage`.
- [x] Extend skeleton coverage to any loading state currently showing a spinner-only or blank state instead of a skeleton (audit all 35 files using TanStack Query `isLoading`/`isPending`).
- [x] Add a lightweight lint/review checklist item (folded into the new `components` skill, workstream G) so future new pages ship a matching skeleton by convention, not as an afterthought.

### D. Empty & error states (net-new, not a kame-homes port)

- [x] Design one `EmptyState` component (icon/illustration slot, heading, description, optional CTA button) and one `ErrorState`/`InlineError` component (for query failures) — neither exists today.
- [x] Roll out across list/table views that can be empty (no patients yet, no appointments today, empty waiting room, no audit log entries, empty reports range) and anywhere a TanStack Query `isError` state is currently unhandled or handled ad hoc.

### E. Native mobile shell

- [x] Build `ResponsiveModal` (name TBD to avoid clashing with kame-homes' exact name if that matters) — one API that renders `Sheet` (bottom, already exists in kame-desk) below `lg` and `Dialog` (already exists) at `lg+`, via a shared `useIsBelowLg()` hook. Migrate the highest-traffic mobile flows first: walk-in check-in, quick reschedule, mark-arrived, cancel/no-show confirm — not a big-bang migration of every dialog in one PR.
- [x] Add a drag-handle affordance to the existing `Sheet` component's bottom variant (kame-desk already has `Sheet`; this is a small addition, not a new `BottomSheet` component from scratch given `Sheet` already exists) and verify `max-h-[92dvh]`-style sizing avoids the mobile WebKit content-height bug kame-homes' code comments flag.
- [x] Add safe-area padding (`pb-[max(0.75rem,env(safe-area-inset-bottom))]` and top equivalent where relevant) to: the bottom sheet variant, any new bottom tab bar, and the top of any full-bleed mobile header.
- [x] Design + build a bottom tab/dock for the mobile front-desk shell — candidate destinations: Today/Calendar, Waiting Room, Patients, More (overflow for Reports/Audit Log/Settings/Assistant). Reuse the `SlidingActivePill` measurement technique for the active-tab indicator, now with the workstream-A spring transition. Confirm this doesn't fight the existing `DashboardShell` sidebar nav — sidebar stays for desktop, tab bar replaces or supplements it below a breakpoint (design decision to make concretely during build, informed by `docs/guides/routes/` for which routes matter most on a phone-sized screen vs. tablet-sized).
- [x] Apply `.native-press` (from workstream A) to waiting-room queue cards, patient list rows, and appointment list rows.
- [x] Ship swipe-to-reveal-actions (not swipe-to-execute, per §4.4) on waiting-room queue rows and the appointment list, gated on that decision being confirmed first.
- [x] Confirm `viewport-fit=cover` and relevant `apple-mobile-web-app` meta tags are present in `apps/web/index.html` (kame-homes sets these explicitly for safe-area support to work at all).

### F. PWA / offline (deferred per §4.3 unless the user overrides)

- [x] Deferred per §4.3 (not greenlit): no `vite-plugin-pwa`, offline banner, or install/update prompts. Static manifest + `viewport-fit=cover` remain. Do not cache clinical data offline.

### G. Agent rules & skills (Cursor / Claude Code / OpenCode)

- [x] **Fix the dangling reference first**: `.cursor/rules/mobile-responsive.mdc` already claims a companion skill exists at `.agent/skills/mobile-responsive/SKILL.md` — it does not. Either create it or remove the claim; given this plan's scope, create it.
- [x] Rewrite `.cursor/rules/mobile-responsive.mdc` with the depth kame-homes' version has, adapted to DoctorDesk's context (not copied verbatim): breakpoint strategy table, touch-target table, the `ResponsiveModal` rule ("never render a centered desktop dialog on a mobile viewport for the flows listed in workstream E — use `ResponsiveModal`"), bottom-tab-bar existence and which routes live in it, safe-area requirement, swipe-action interaction pattern from §4.4, front-desk-tablet-specific guidance (landscape calendar/waiting-room requirement already exists — keep it).
- [x] Create `.agent/skills/mobile-responsive/SKILL.md` as the Claude Code twin of the rule above — one canonical body, hand-synced into both formats (this is exactly the structural pattern kame-homes uses and documents in its own skill frontmatter: _"this is an always-on rule on the Cursor side with no automatic Claude Code equivalent, so invoke it explicitly for UI work"_). Symlink or mirror into `.claude/skills/` and `.opencode/` per this repo's existing sync convention (`pnpm run check:ai-tooling-sync`).
- [x] Create a new always-on-on-Cursor / explicit-on-Claude rule+skill pair: `components.mdc` / `.agent/skills/components/SKILL.md` — "primitives-first" rule: never introduce a native form element or a one-off styled `<div>` where an existing `apps/web/src/components/ui/*` primitive exists; new primitives follow the `cva` variant + `data-slot` + `cn()` convention already established; new interactive elements get a `motion-reduce`-safe transition from the workstream-A token set, not an ad hoc one.
- [x] Create a new `motion.mdc` / skill (or fold into `components`) codifying the resolved §4.1 motion budget as an enforceable rule: which duration tier applies to which UI event, the reduced-motion requirement, and the explicit "no gradients, no confetti, no playful micro-illustrations" boundary so future AI-driven UI work doesn't drift toward kame-homes' hospitality tone.
- [x] Update `DESIGN.md` with an "Agent Prompt Guide" section mirroring kame-homes' pattern — short, copy-pasteable prompts an agent (or a person prompting an agent) can use for "add a new skeleton for X," "make this modal responsive," "add a new dialog," so the craft bar in this plan is easy to invoke consistently later, not just documented once.
- [x] Run `pnpm run check:ai-tooling-sync` after all of the above to confirm Cursor/Claude/OpenCode stay in sync (this repo's own CI-adjacent check).

### H. Docs & QA

- [x] Update `DESIGN.md` (motion section per §4.1, new component list entries: `ResponsiveModal`, bottom tab bar, `EmptyState`/`ErrorState`).
- [x] Update `docs/architecture/design-system.md` §12 ("status: implemented") to reflect the new components/tokens.
- [x] Update `docs/tech-stack.md` with any new dependency (`framer-motion`, `vite-plugin-pwa` if greenlit).
- [x] Update the relevant `docs/guides/routes/*.md` guides for every route whose mobile behavior materially changes (bottom sheet instead of dialog, new bottom tab nav) — required by this repo's `route-guides` rule, not optional polish.
- [x] Re-run the Phase 19 checklist item "Mobile-responsive audit across every screen shipped in Phases 1–18" — it's currently unchecked in `docs/phases/phase-19-hardening-production-readiness.md`; this plan is the natural place to finally close it out, on a real tablet, not a resized browser window.
- [x] Add/extend Playwright coverage for the new responsive modal breakpoint switch and bottom-tab navigation, since this is exactly the kind of behavior a resized-viewport E2E test catches that a unit test won't.

---

## 6. Suggested execution order (waves, not calendar dates)

1. **Wave 0 — Decisions.** Resolve §4.1–§4.4 with the user. Nothing else starts first.
2. **Wave 1 — Foundation (workstream A + G's `components`/`motion` rules).** Tokens and agent rules exist before anyone (human or AI) starts building against them, otherwise workstreams B–E get built against a moving target.
3. **Wave 2 — Skeletons + empty/error states (C + D).** Highest visible impact for the lowest architectural risk; no new dependencies, no navigation restructuring.
4. **Wave 3 — Component polish (B).** Refine what exists using Wave 1's tokens.
5. **Wave 4 — Native mobile shell (E), gated on §4.4 sign-off for the swipe-action item specifically.** Highest risk/impact item; do it once Waves 1–3 have proven the motion system out on lower-stakes surfaces.
6. **Wave 5 — Docs/QA close-out (H)**, run continuously alongside each wave above per this repo's "docs in the same change" rule, not batched at the end.
7. **Deferred — PWA/offline (F)**, only if explicitly requested after seeing Waves 1–4 land.

---

## 7. Definition of done for this initiative

- Every new/changed component passes this repo's existing bar: works at 375–1024px+, 44×44px touch targets, keyboard-accessible, `prefers-reduced-motion`-safe.
- `DESIGN.md`, `docs/architecture/design-system.md`, `docs/tech-stack.md`, and affected `docs/guides/routes/*.md` are updated in the same change as the code that made them stale — not a follow-up.
- `.cursor/rules/mobile-responsive.mdc` no longer references a nonexistent skill file.
- `pnpm run ci:quality` stays green throughout; new Playwright coverage exists for the responsive-modal breakpoint behavior.
- No hospitality-toned visual element (gradients, confetti, playful micro-illustrations, marketing copy) shipped as a side effect of chasing kame-homes' polish — the craft is ported, the tone is not.
