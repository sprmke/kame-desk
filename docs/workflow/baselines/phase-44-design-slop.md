# Phase 44: mechanical design-slop baseline

**Date:** 2026-09-13
**Source:** `pnpm run check:design-slop` (`scripts/dev/check-design-slop.mjs`)
**Ratchet file:** [`design-slop-baseline.json`](./design-slop-baseline.json)

Counts after overrides, after Phases 44–47. CI fails if any rule **increases**. Drop counts, then rewrite the JSON with `--write-baseline`.

| Rule | Count | What it catches                                                      |
| ---- | ----- | -------------------------------------------------------------------- |
| T11  | 27    | Hex / `rgb()` outside `styles.css`                                   |
| H3   | 7     | `rounded-2xl` + `border` + `shadow` on one class                     |
| T9   | 6     | Money/number formatting without `tabular-nums` / `dd-nums` in file   |
| B7   | 4     | `PageHeader` `description=` (identity-only leftovers)                |
| B1   | 0     | `StatCard`                                                           |
| B3   | 0     | Literal-object icons (`Stethoscope`, `Armchair`, `CalendarClock`, …) |
| B4   | 0     | `Bot` / `Sparkles`                                                   |
| M6   | 0     | Affordance revealed only on hover                                    |

**Total: 44** (was 66 after Phase 44, 146 at Phase 43 close). Zero B1/B3/B4.

Phase 43 companion: [`phase-43-design-slop.md`](./phase-43-design-slop.md).
