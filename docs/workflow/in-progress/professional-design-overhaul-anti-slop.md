# In progress: Professional design overhaul (anti-slop)

**Started:** 2026-09-12
**Plan reference:** [`docs/workflow/planned/professional-design-overhaul-anti-slop.md`](../planned/professional-design-overhaul-anti-slop.md)

Executing the professional design overhaul and anti-slop system per plan:

| #   | Phase                                                                                                        | Status      |
| --- | ------------------------------------------------------------------------------------------------------------ | ----------- |
| 42  | [Design System Pilot & Waiting Room Overhaul](../../phases/phase-42-design-system-pilot.md)                  | Done        |
| 43  | [Anti-slop rules, design-review skill, screenshot harness](../../phases/phase-43-anti-slop-rules-harness.md) | Done        |
| 44  | [Hierarchy and density system (end card soup)](../../phases/phase-44-hierarchy-density.md)                   | Not started |
| 45  | Screen redesign: shell, entry, Today, Schedule, Waiting room                                                 | Not started |
| 46  | Screen redesign: Patients, Clinical, Billing, Documents, Insights, Settings, Assistant                       | Not started |
| 47  | Native mobile feel + accessibility gates                                                                     | Not started |

### Phase 42 closeout

- Waiting-room **Kanban retained** (linear queue rejected).
- Elapsed wait, doctor filter, arrival chime shipped.
- `docs/architecture/design-language.md` records closed layout decisions and archives the three brand candidates.
- **Brand hue still open.** Next visual-pilot surface: Today (`/dashboard`).

### Phase 43 closeout

- `.cursor/rules/anti-slop-design.mdc`, `design-review` skill, `design-reviewer` subagent, `/dd-design-review`.
- `pnpm run check:design-slop` ratchet: [`docs/workflow/baselines/design-slop-baseline.json`](../baselines/design-slop-baseline.json) (146 findings).
- Screenshot harness: `pnpm run capture:design-screenshots` (needs a seeded local app).
- `DESIGN.md` rewritten; `design-system.md` demoted to a historical audit.

### Next: Phase 44

Hierarchy and density: surface variants, kill card soup, density tokens, Lucide rules, replace banned icons in nav/chrome. Do not pick a brand hue here.
