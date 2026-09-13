# Phase 46: Patients, Clinical, Billing, Documents, Insights, Settings, Assistant

**Status:** Done
**Depends on:** Phase 44
**Unlocks:** Phase 47 (with 45)

**Plan reference:** `docs/workflow/planned/professional-design-overhaul-anti-slop.md` §4 Workstream D5–D10, F

## Goal

Apply the Phase 44 hierarchy language to the remaining operational modules. Patient list identity already started in 44. Finish chart IA, SOAP writing surface, billing numerals, insights charts, remaining settings rows, and assistant confirm cards.

activity-log: N/A — presentation layer unless a list starts showing an API field it already returns.

## Tasks

- [x] Patients: list columns for last visit / next / flags if the API already returns them; persistent identity rail on detail. (API does not return last/next visit on list; rail ships name, #, allergies, balance.)
- [x] SOAP: four sections without a card per section; AI draft visually distinct from clinician text.
- [x] Billing: tabular money, payment state without pastel-only encoding.
- [x] Documents / Insights: preview matches print; activity log stays dense. Remaining settings lists unboxed.
- [x] Remaining settings pages on `SettingsSection` / `SettingsRow`.
- [x] Assistant: confirm cards as a decision point; no Bot/Sparkles (Phase 44). FAB kept, first-run hint bubble removed, panel sits above the tab bar.
- [x] Copy: remaining B7 PageHeader descriptions.
- [x] Route guides + `ci:quality`

## Exit criteria

- No B7 restating descriptions on these pages
- Confirm cards are unmistakable decision points
- `check:design-slop` does not rise; `ci:quality` green
