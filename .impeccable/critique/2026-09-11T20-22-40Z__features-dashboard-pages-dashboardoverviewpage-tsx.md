---
target: apps/web/src/features/dashboard/pages/DashboardOverviewPage.tsx
total_score: 30
max_score: 40
na_heuristics:
p0_count: 0
p1_count: 0
timestamp: 2026-09-11T20-22-40Z
slug: features-dashboard-pages-dashboardoverviewpage-tsx
---

# Dashboard overview critique (A+B synthesis)

Method: dual-agent. Assessment A reviewed source (pre-polish snapshot). Assessment B: CLI 0 findings; browser detect.js 10 hits at 1280×800 (mostly false positives). Parent already shipped P0/P1 layout polish before A/B returned; this snapshot records synthesis.

## Design specificity

A: moderately clinic-specific in modules, TailAdmin-generic in chrome. After polish: Operate IA is tighter (chart gone; calendar fills). Still a calm admin shell with clinic data, which is correct for Operate mode.

## Heuristics (post-polish Operate)

1 Visibility 3 · 2 Real world 3 (A) / 4 (parent) · 3 Control 3 · 4 Consistency 3 · 5 Prevention 3 · 6 Recognition 3 · 7 Flexibility 3 · 8 Aesthetic 3 · 9 Recovery 3 · 10 Help 2.
Total 30/40 Good.

A scored ~2.2/4 on the pre-polish page (chart + compact calendar + jumping heights). Those P0/P1s are closed.

## Cognitive load

A: FAIL ≤4 chunks on owner/admin with chart. Post-polish: KPI row, Today+Queue, Calendar+Upcoming, follow-up. Still 4 bands; attention is four sibling piles (at the working-memory edge, acceptable for a morning board).

## Detector vs LLM

- CLI file scan: 0. Browser: layout-transition (sidebar, false), undersized tab labels (0×0 at desktop, false), text-occlusion on Billing plan/Clinic (false), clipped chart container (stale: chart removed), skipped-heading h1→h3 (true; card titles now h2).
- A P0 calendar padding and P1 redundant chart/heights: agree with user request; shipped.

## Addressed

- 14-day chart removed (Reports).
- Calendar fills card; day targets ~44px.
- Fixed module heights.
- Dashboard card titles are h2 under page h1.

## Remaining P2 (not shipped; product calls)

- KPI "Today" vs card "Today" label collision (A).
- Today rows open SOAP for all roles (A P3).
- Empty wells when a list has one item (intentional stable height).
- Help is the floating assistant only.
