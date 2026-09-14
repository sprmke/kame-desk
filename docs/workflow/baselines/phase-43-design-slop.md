# Phase 43: mechanical design-slop baseline

**Date:** 2026-09-13  
**Source:** `pnpm run check:design-slop` (`scripts/dev/check-design-slop.mjs`)  
**Ratchet file:** [`design-slop-baseline.json`](./design-slop-baseline.json)

Counts after overrides. CI fails if any rule **increases**. Drop counts, then rewrite the JSON with `--write-baseline`.

| Rule | Count | What it catches                                                      |
| ---- | ----- | -------------------------------------------------------------------- |
| B3   | 46    | Literal-object icons (`Stethoscope`, `Armchair`, `CalendarClock`, …) |
| T11  | 38    | Hex / `rgb()` outside `styles.css`                                   |
| B7   | 29    | `PageHeader` `description=`                                          |
| B4   | 10    | `Bot` / `Sparkles`                                                   |
| H3   | 9     | `rounded-2xl` + `border` + `shadow` on one class                     |
| B1   | 7     | `StatCard`                                                           |
| T9   | 6     | Money/number formatting without `tabular-nums` in the file           |
| M6   | 1     | Affordance revealed only on hover                                    |

**Total: 146.** Override a file+rule in `scripts/dev/design-slop-overrides.txt` (tab-separated, written reason required).

Pre-overhaul visual/code audit (Phase 42a, hand-counted): [`phase-42a-baseline.md`](./phase-42a-baseline.md).
