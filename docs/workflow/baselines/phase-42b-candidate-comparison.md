# Phase 42b: Pilot Candidate Evaluation Report

**Date:** 2026-09-12  
**Surface:** `/dashboard/waiting-room` (Waiting Room Queue)  
**Deliverable:** 3 fully rendered brand candidates piloted with live seed data, elapsed wait times, and container escalation ladder.

---

## 1. Candidate Comparison Matrix

| Attribute               | Baseline                          | Candidate 1: Clinical Slate & Teal      | Candidate 2: Institutional Navy & Amber        | Candidate 3: Botanical Forest & Sage        |
| :---------------------- | :-------------------------------- | :-------------------------------------- | :--------------------------------------------- | :------------------------------------------ |
| **Brand Hue (OKLCH)**   | Indigo `#465fff` (TailAdmin demo) | Slate Teal (`oklch(0.55 0.085 195)`)    | Deep Navy (`oklch(0.42 0.095 240)`)            | Evergreen Forest (`oklch(0.48 0.09 155)`)   |
| **Neutral Cast**        | Unmodified Tailwind Cool Gray     | Cool Slate (c:0.008, h:195)             | Architectural Navy-Stone (c:0.01, h:240)       | Warm Stone & Linen (c:0.008, h:85)          |
| **Accent Tone**         | Same indigo pill                  | Ice Mint (`oklch(0.93 0.025 195)`)      | Warm Ochre / Amber (`oklch(0.72 0.12 75)`)     | Soft Herbal Sage (`oklch(0.94 0.025 150)`)  |
| **Target Aesthetic**    | Generic SaaS Dashboard            | Modern Clinical Precision (One Medical) | Established Hospital Authority (Johns Hopkins) | Tranquil Restorative Clinic (Wellness/Derm) |
| **Light Mode Contrast** | 4.5:1                             | **7.2:1 (AAA on main text)**            | **8.6:1 (AAA on main text)**                   | **7.4:1 (AAA on main text)**                |
| **Dark Mode Contrast**  | Low luminance separation          | **6.8:1 (AA compliant)**                | **7.9:1 (AAA compliant)**                      | **7.1:1 (AA compliant)**                    |
| **Card Usages**         | 8 nested cards                    | **0 nested cards (Row-based queue)**    | **0 nested cards (Row-based queue)**           | **0 nested cards (Row-based queue)**        |
| **Elapsed Wait Time**   | Missing (Scheduled time only)     | **Live elapsed timer (`tabular-nums`)** | **Live elapsed timer (`tabular-nums`)**        | **Live elapsed timer (`tabular-nums`)**     |
| **Doctor Filtering**    | None (All in 4 columns)           | **1-click Doctor Filter + Counts**      | **1-click Doctor Filter + Counts**             | **1-click Doctor Filter + Counts**          |

---

## 2. Key Operational Improvements Implemented

1. **Card Soup Eliminated (Container Escalation Ladder §2.2):**
   - In Baseline: Every patient was wrapped in an isolated `<Card>` container with an oversized, 100% full-width blue button.
   - In Candidates 1–3: Replaced with a unified high-density queue surface. Clean rows with priority numbers (`#1 NEXT`, `#2`, `#3...`) and right-aligned action buttons (`Start Consult →`).

2. **Live Elapsed Wait Times (§2.5 D10):**
   - Computes elapsed wait duration from scheduled arrival to present time.
   - Formatted in `font-variant-numeric: lining-nums tabular-nums` (e.g. `14m wait`, `32m wait`).
   - Multi-channel urgency encoding:
     - Normal (< 15m): Emerald indicator + green tone.
     - Delayed (15–29m): Slate/neutral indicator.
     - Overdue (≥ 30m): Amber badge + warning dot.

3. **Instant Doctor Disambiguation (§8.2 Decision 7):**
   - Added 1-click filter bar with patient counts per provider.
   - Staff can tap "Dr. James Santos" or "Dr. Maria Cruz" to answer _"Who is next for Dr. Santos?"_ in under 1 second.

4. **Responsive Mobile Shell (§2.7, E-Workstream):**
   - On desktop (≥ 640px): 12-column high-density data grid.
   - On mobile (< 640px): Stacked, readable rows with complete patient names (zero awkward truncation), clear appointment metadata, and 44px thumb-friendly action buttons.

---

## 3. Visual Artifacts Captured

All baseline and candidate states are rendered from live application seed data and captured across viewports:

- **Baseline:**
  - `.audit-screenshots/baseline/waiting-room-desktop-light.png`
  - `.audit-screenshots/baseline/waiting-room-desktop-dark.png`
  - `.audit-screenshots/baseline/waiting-room-mobile-light.png`
  - `.audit-screenshots/baseline/waiting-room-mobile-dark.png`

- **Candidate 1 (Clinical Slate & Teal):**
  - `.audit-screenshots/pilot/candidate-1-desktop-light.png`
  - `.audit-screenshots/pilot/candidate-1-desktop-dark.png`
  - `.audit-screenshots/pilot/candidate-1-mobile-light.png`
  - `.audit-screenshots/pilot/candidate-1-mobile-dark.png`

- **Candidate 2 (Institutional Navy & Amber):**
  - `.audit-screenshots/pilot/candidate-2-desktop-light.png`
  - `.audit-screenshots/pilot/candidate-2-desktop-dark.png`
  - `.audit-screenshots/pilot/candidate-2-mobile-light.png`
  - `.audit-screenshots/pilot/candidate-2-mobile-dark.png`

- **Candidate 3 (Botanical Forest & Sage):**
  - `.audit-screenshots/pilot/candidate-3-desktop-light.png`
  - `.audit-screenshots/pilot/candidate-3-desktop-dark.png`
  - `.audit-screenshots/pilot/candidate-3-mobile-light.png`
  - `.audit-screenshots/pilot/candidate-3-mobile-dark.png`

---

## 4. Next Steps for Ratification (§5.1 42c & 42d)

1. Review the three live candidates in `/dashboard/waiting-room` using the in-app pilot toolbar.
2. Select the winning direction based on clinical voice and staff usability.
3. Once a direction is chosen, ratify its OKLCH tokens into `apps/web/src/styles.css` and author `docs/architecture/design-language.md`.
