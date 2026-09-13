# Phase 24: Scheduling & booking that scales past one doctor

**Status:** Done
**Depends on:** Phase 23
**Unlocks:** Phase 25

**Plan reference:** `docs/workflow/planned/ground-up-app-redesign-and-platform-admin.md` §4 Phase 24

## Goal

A 3-doctor, 2-room clinic can run the day from the calendar without UUID confusion. Public requests sit in a review queue. Staff can waitlist a patient for an earlier slot and filter the appointment list.

## Tasks

### Backend

- [x] `service_fees.duration_minutes` and `appointments.service_fee_id`
- [x] Rooms CRUD
- [x] Appointment list filters: date range, status, doctor, room, search, booking source
- [x] Public-request queue (public booking, still `Scheduled`)
- [x] Cancellation waitlist

### Frontend

- [x] Doctor selectors show `full_name`
- [x] Appointment type (service) sets duration
- [x] Room on book + calendar
- [x] Multi-doctor day columns
- [x] List filters + public request badge/queue
- [x] Waitlist UI

## Exit criteria

- [x] Doctor names, never UUIDs, in booking and calendar
- [x] Public requests are reviewable before they mix into confirmed work
- [x] Scheduling tests + web type-check green
