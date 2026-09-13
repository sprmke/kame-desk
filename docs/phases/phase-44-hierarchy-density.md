# Phase 44: Hierarchy and density system (end card soup)

**Status:** Not started
**Depends on:** Phase 42, Phase 43
**Unlocks:** Phases 45–46

**Plan reference:** `docs/workflow/planned/professional-design-overhaul-anti-slop.md` §4 Workstreams B and C

## Goal

Replace card-as-page-structure with the container escalation ladder, an explicit density mode, and a status/icon language that can be scanned. Do not ratify a brand hue in this phase; tokens stay on the holding TailAdmin ramp until the Today visual pilot (Phase 45).

activity-log: N/A — presentation layer. No clinic/patient/appointment writes unless a list starts showing a field the API already returns.

## Tasks

### B — Surfaces and density

- [ ] Surface variants on `Card` (or a successor): `plain` default, then `panel` / `raised` / `overlay`. `CardHeader` `border-b` opt-in.
- [ ] Audit `<Card>` usages. Target: fewer than 30 bordered/shadowed surfaces. Settings becomes a settings-row pattern, not a stack of cards.
- [ ] Commit the signature primitive: dense divider-separated rows (waiting-room Kanban columns already follow this for patients; lists/tables should match).
- [ ] Density tokens: compact / default / comfortable row heights (~32 / 40 / 48px), per surface and breakpoint. Compact on desktop tables; comfortable on forms and on touch.
- [ ] Replace uniform `gap-4` page rhythm with within-group / between-group / between-section spacing.
- [ ] Table craft: quieter headers, numeric columns right + `lining-nums tabular-nums`, sticky header, distinct hover/focus/selected.
- [ ] `ManagedList` chrome scales with list size. Drop unused view modes (patient card grid is the first candidate).

### C — Icons and status

- [ ] Stay on Lucide under written rules: `absoluteStrokeWidth`, non-default stroke, size from cap-height. Document in `design-language.md`.
- [ ] Replace `Stethoscope` / `Armchair` / `Bot` / `Sparkles` / `CalendarClock` in nav and chrome. Custom product mark and assistant mark: interim geometric SVGs are allowed; distinctive marks remain a human decision (`design-language.md` § open).
- [ ] Status encoding: shape + text, not pastel pills by hue alone. Red out of the appointment-type palette. Threshold terms documented and reused.
- [ ] Patient/doctor identity block reused (name, age/sex, patient number). Initials from a curated palette.

### Enforcement

- [ ] Grade each touched surface with `/dd-design-review` (zero B-class, no unresolved H-class).
- [ ] `pnpm run check:design-slop` counts must not rise; rewrite baseline after intentional drops.
- [ ] Update route guides for any page whose hierarchy or chrome changed.
- [ ] `pnpm run ci:quality` green

## Exit criteria

- Card count on operational screens is visibly down; settings is not a card stack
- Banned Lucide names gone from nav/chrome
- Status survives grayscale on the surfaces touched
- Brand hue still **unratified**
- Design-slop ratchet green; `ci:quality` green

## Docs to update

`docs/architecture/design-language.md`, `docs/guides/routes/**` for touched pages, `docs/phases/README.md`, workflow tracker, `DESIGN.md` if the signature primitive needs a one-line restatement.
