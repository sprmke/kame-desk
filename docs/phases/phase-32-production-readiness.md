# Phase 32: Production readiness closeout

**Status:** Done
**Depends on:** Phase 29, 30, 31

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 32

## Goal

Every `mvp.md` §12 box is either checked with automated evidence or left open with a runbook, not a fake check.

## Evidence map (`mvp.md` §12)

| Item                            | Evidence                                                                            | Checkbox |
| ------------------------------- | ----------------------------------------------------------------------------------- | -------- |
| Uninstructed onboarding pilot   | Playwright onboarding spec exists. A real clinic walkthrough is still a human gate. | Open     |
| Full patient lifecycle          | `test_patient_lifecycle.py`                                                         | Checked  |
| Concurrent double-booking       | `test_concurrent_double_booking` + load script                                      | Checked  |
| Physical print fidelity         | PDF endpoints exist. Paper check is manual.                                         | Open     |
| Backup restore drill            | `pnpm run backup:db:dev` dumps. Prod Neon restore needs `deskwave`.                 | Open     |
| SOAP immutability               | `test_soap_versions_are_immutable`                                                  | Checked  |
| RBAC SOAP                       | `test_security_rbac.py`                                                             | Checked  |
| Tier 2 confirm                  | `test_assistant.py`                                                                 | Checked  |
| Assistant failure rollback      | `test_tier1_tool_error_emits_sse_error_no_write`                                    | Checked  |
| AI usage cap                    | `test_soap_draft_usage_cap_blocks`                                                  | Checked  |
| Kill switch                     | env + DB flag (`test_platform.py`, `test_assistant.py`)                             | Checked  |
| Consent capture                 | intake checkbox + tests                                                             | Checked  |
| PHI in logs / Sentry            | conventions in `phi-data-safety.mdc`. Prod Sentry spot-check is operational.        | Open     |
| Audit log on mutations          | service-layer `activity_log`                                                        | Checked  |
| Uptime monitoring               | configure before first pilot. Not a code checkbox.                                  | Open     |
| Support channel + rollback plan | `docs/architecture/deployment.md`                                                   | Checked  |

## Exit criteria

- [x] §12 is honest: automated items stay checked; operational items stay open with a pointer
- [x] Platform + assistant trust boundaries have regression tests

activity-log: N/A
