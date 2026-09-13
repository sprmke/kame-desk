# DoctorDesk design language

Authoritative token, surface, and component spec for the professional design overhaul (Phases 42–47). Principle-level summary: [`DESIGN.md`](../../DESIGN.md). Historical TailAdmin audit (superseded): [`design-system.md`](./design-system.md).

activity-log: N/A — presentation-layer spec, no clinic writes.

## Status (2026-09-13)

| Decision                                   | State      | Notes                                                                                                                           |
| ------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Waiting-room layout                        | **Closed** | Drag-and-drop Kanban retained. Linear queue pilot rejected by staff.                                                            |
| Elapsed wait, doctor filter, arrival chime | **Closed** | Shipped on the Kanban board.                                                                                                    |
| Container escalation ladder on the queue   | **Closed** | Nested cards removed from waiting-room columns. Card is last resort.                                                            |
| Brand hue                                  | **Open**   | Three candidates piloted; none ratified. Current `styles.css` still uses the TailAdmin indigo ramp until a second visual pilot. |
| Next visual-pilot surface                  | **Closed** | Today (`/dashboard`). Matches Phase 45 sequence (shell, entry, Today, Schedule, Waiting room).                                  |

Do not treat the current indigo ramp as a chosen identity. It is leftover template skin. Ratify a winner only from a rendered Today screen, the same way the waiting room was piloted.

## 1. Governing principle

Slop is the absence of decisions. Every visual element must have a named choice and a rejected alternative. Changing the hue without making those choices still reads as generated UI.

Pass/fail assertions: `.cursor/rules/anti-slop-design.mdc`. Review procedure: `.agent/skills/design-review/SKILL.md`.

## 2. Closed: waiting room

Pilot evidence: [`docs/workflow/baselines/phase-42b-candidate-comparison.md`](../workflow/baselines/phase-42b-candidate-comparison.md).

**Layout.** `/dashboard/waiting-room` stays a spatial Kanban board (Arrived / In consultation columns, drag-and-drop on `lg+`). Staff preferred this over a linear ranked queue. Do not reintroduce the linear-queue pilot.

**Operational additions kept on Kanban:**

- Live elapsed wait on Arrived / In consultation cards (`lining-nums tabular-nums`).
- Threshold urgency: &lt;15m normal, 15–29m delayed, ≥30m overdue. Shape + label + color (D5). Red is not used for appointment type.
- Doctor filter pills when more than one provider is on the board.
- Arrival chime on remote `visit.arrived` toasts.

**Rejected alternative.** A single ranked list with `#1 NEXT` row chrome. Faster for "who waited longest," worse for the actual front-desk motion of moving a person between columns.

## 3. Open: brand hue (archived candidates)

Built as live waiting-room screens, then the unused candidate UI was removed. Values stay on record so the next pilot does not start from adjectives.

| Candidate                    | Brand hue (OKLCH)       | Neutral cast                           | Accent                              | Brief                                         |
| ---------------------------- | ----------------------- | -------------------------------------- | ----------------------------------- | --------------------------------------------- |
| 1 Clinical Slate / Teal      | `oklch(0.55 0.085 195)` | Cool slate, chroma 0.008, hue 195      | Ice mint `oklch(0.93 0.025 195)`    | Modern clinical, calm under fluorescent light |
| 2 Institutional Navy / Ochre | `oklch(0.42 0.095 240)` | Navy-stone, chroma 0.01, hue 240       | Warm ochre `oklch(0.72 0.12 75)`    | Established, hospital-authority               |
| 3 Botanical Forest / Sage    | `oklch(0.48 0.09 155)`  | Warm stone/linen, chroma 0.008, hue 85 | Herbal sage `oklch(0.94 0.025 150)` | Organic wellness                              |

Indigo / violet is off the table (template tell). Screenshots: `.audit-screenshots/pilot/` (gitignored).

**Current code.** `apps/web/src/styles.css` still carries the TailAdmin 12-step indigo brand ramp and Tailwind-gray neutrals. That is a holding pattern, not ratification.

**When to ratify.** Pilot the three directions (or the surviving two) on **Today** (`/dashboard`). Only the winner is copied into `styles.css` and this file. The losers stay in the table above.

## 4. Surface system

Containers follow the escalation ladder and stop at the first level that works:

1. Spacing / gap
2. Divider
3. Section with no border
4. Card (last resort)

Rules H12–H14 in `anti-slop-design.mdc`. A stack of full-width cards is not page structure. Record lists (patients, appointments, invoices, queue) are rows, not a card grid.

The waiting-room Kanban column is a section, not a nested card around each patient. That is the reference implementation other screens copy in Phases 44–46.

## 5. Type, numbers, motion (intent)

These are the decisions. Code may still lag until Phases 44 and 47.

| Topic        | Decision                                                                                                         | Rejected                                                             |
| ------------ | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| UI face      | Keep **IBM Plex Sans** (already shipped, non-default). Author a real scale around it.                            | Switching to Inter/Outfit for a "refresh."                           |
| Mono         | IBM Plex Mono for IDs, timestamps, audit/document preview.                                                       | Mixing a third family.                                               |
| Type ratio   | ≤ 1.25. 14px minimum for readable desktop text; 13px metadata only; inputs never below 16px.                     | Tailwind defaults used as-is with marketing `theme-*` display sizes. |
| Numerals     | `lining-nums tabular-nums` on columns, live timers, and money. `slashed-zero` on financial surfaces. Not global. | `tabular-nums` alone, or applying it to running prose.               |
| Route motion | ≤ 180ms or none (M1). Hard ceiling 300ms for any UI animation.                                                   | Current 300ms translate+fade `PageTransition`.                       |
| Frequency    | 100+/day actions: no animation. Occasional: standard. Rare/first-run: the delight budget.                        | Animating every hover and route.                                     |

Tokens today still live in `apps/web/src/lib/motion.ts` at the old tiers. Retune in Phase 47; new work should follow the table, not the old numbers.

## 6. Status encoding

- At least two channels (shape + text; color is extra). `aria-label="Status: …"`.
- Categorical / appointment-type palette **excludes red**. Red is reserved for status.
- Red and green are never the sole differentiator between two clinical statuses.
- A status _change_ needs a shape change or a short motion cue, not only a hue swap.

## 7. Copy

`ui-minimal-copy.mdc` wins over any older "every page carries a description" requirement in `design-system.md` §12. `PageHeader` `description` is optional. A description that restates the title or the nav label is a B7 fail.

## 8. Implementation map

| Concern                      | Path                                                           |
| ---------------------------- | -------------------------------------------------------------- |
| Tokens (current, unratified) | `apps/web/src/styles.css`                                      |
| Motion tokens                | `apps/web/src/lib/motion.ts`                                   |
| Waiting-room reference       | `apps/web/src/features/waiting-room/`                          |
| Deterministic slop check     | `pnpm run check:design-slop`                                   |
| Screenshot harness           | `pnpm run capture:design-screenshots` (local app + seed login) |
