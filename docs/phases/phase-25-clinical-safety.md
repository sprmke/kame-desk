# Phase 25: Clinical safety and specialty depth

**Status:** Done
**Depends on:** Phase 24
**Unlocks:** Phase 26

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 25

## Production default

Drug/interaction source: **curated open list** (expanded `drug_reference` seed). No commercial license. Drugs outside the list return an explicit `unchecked` flag. Staff can still prescribe. Unchecked does not require an override.

## Goal

Allergy and interaction checks cover common clinic drugs, and "not checked" is visible. Lab/imaging and referrals have a real status lifecycle. Named specialties have structured templates. Chart versions can be compared. Certificates show an electronic signature.

## Tasks

### Backend

- [x] Expand curated drug reference + `unchecked` flags
- [x] Lab/imaging order lifecycle (`clinical_orders`)
- [x] Referral recipient/status/outcome on generated documents
- [x] OB-GYN, psychiatry, dermatology templates
- [x] E-sign line on certificate/referral PDFs

### Frontend

- [x] Unchecked drugs shown separately from allergy/interaction
- [x] SOAP version diff
- [x] Structured dental/pediatric/OB/psych/derm widgets
- [x] Orders tab on patient detail
- [x] Referral fields on generate + patient documents

## Exit criteria

- [x] Unchecked drugs are visible in the Rx flow
- [x] Orders and referrals have status, not just a PDF
- [x] Tests + type-check green
