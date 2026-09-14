# Phase 42a: Pre-Overhaul Baseline Audit

**Date:** 2026-09-12  
**Commit/State:** Initial baseline before Phase 42b changes  
**Target:** Eliminate template tells, reduce card count by >70%, eliminate AI icon tropes, enforce tabular numbers across all metrics.

---

## 1. Quantitative Codebase Audit

| Metric                                                              | Pre-Overhaul Baseline | Target (Post-Phase 47)            | Notes                                                               |
| :------------------------------------------------------------------ | :-------------------- | :-------------------------------- | :------------------------------------------------------------------ |
| **`<Card>` component usages**                                       | **100**               | < 30                              | Settings: 24, Patients: 12, Billing: 11, Dashboard: 8               |
| **Unique Lucide icons**                                             | **106**               | < 45                              | Scattered icon vocabulary without semantic alignment                |
| **AI tell icons (Stethoscope/Armchair/Bot/Sparkles/CalendarClock)** | **23**                | **0**                             | Stethoscope: 10, Armchair: 4, Bot: 4, CalendarClock: 4, Sparkles: 1 |
| **`StatCard` component instances**                                  | **4**                 | **0**                             | Top of Today/Dashboard row with pastel icon chips                   |
| **`rounded-2xl` count**                                             | **30**                | 0 on inner cards                  | Excessive bubble radii on containers                                |
| **Explicit border utility classes**                                 | **371**               | System surface tokens             | Wireframe look from 1px borders everywhere                          |
| **`tabular-nums` usages**                                           | **18**                | Comprehensive on all tables/money | 18 instances across the entire web app                              |
| **`PageHeader` instances with `description=`**                      | **26 / 30 (86.7%)**   | < 5                               | Restating the page title in muted gray                              |

---

## 2. Card Counts by Feature

- `settings`: 24
- `patients`: 12
- `billing`: 11
- `dashboard`: 8
- `components` (reusable wrappers): 7
- `documents`: 6
- `patient-portal`: 6
- `soap`: 5
- `platform`: 4
- `appointments`: 3
- `prescriptions`: 3
- `reports`: 3
- `waiting-room`: 2
- `audit-log`: 1
- `chart-search`: 1
- `growth`: 1
- `marketing`: 1
- `onboarding`: 1
- `recalls`: 1

---

## 3. Waiting Room Specific Baseline

- **Current layout:** 2 Kanban-style columns wrapped in `<Card>` containers (`Arrived`, `In Consultation`).
- **WaitingRoomCard:** Card inside card with avatar, name, appointment time, and prominent full-width `<Button className="mt-3 w-full">`.
- **Elapsed wait time:** **Missing**. Only shows scheduled start time. Staff cannot see who has been waiting 40 minutes vs 5 minutes.
- **Empty state:** Literal text "Empty" inside a card border.
- **Status indicators:** All pastel pills (`bg-blue-50 text-blue-700` etc.) relying strictly on color hue.
