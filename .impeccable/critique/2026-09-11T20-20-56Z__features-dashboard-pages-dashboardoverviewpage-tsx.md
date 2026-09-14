---
target: apps/web/src/features/dashboard/pages/DashboardOverviewPage.tsx
total_score: 30
max_score: 40
na_heuristics:
p0_count: 0
p1_count: 0
timestamp: 2026-09-11T20-20-56Z
slug: features-dashboard-pages-dashboardoverviewpage-tsx
---

# Dashboard overview critique (post layout polish)

Operate-mode clinic morning board. Detector: 0 findings.

## Heuristics

1 Visibility 3, 2 Real world 4, 3 Control 3, 4 Consistency 3, 5 Prevention 3, 6 Recognition 3, 7 Flexibility 3, 8 Aesthetic 3, 9 Recovery 3, 10 Help 2. Total 30/40 Good.

## Addressed this pass

- Removed redundant 14-day appointments chart (lives on Reports).
- Calendar fills its card (no compact postage stamp).
- Fixed body heights: Today/Queue/follow-up h-60; Calendar/Upcoming 22rem.

## Remaining P2

- Empty wells when a list has 1 item (intentional stable height).
- Help is the floating assistant only.
