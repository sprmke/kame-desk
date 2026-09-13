import { describe, expect, it } from "vitest";
import {
  applyOptimisticMove,
  appointmentToEvent,
  rollbackOptimisticMove,
} from "./calendarEvents";
import type { Appointment } from "@/lib/apiClient";

const sample: Appointment = {
  id: "a1",
  clinic_id: "c1",
  patient_id: "p1",
  doctor_id: "d1",
  room_id: null,
  scheduled_start: "2026-10-06T02:00:00.000Z",
  scheduled_end: "2026-10-06T02:30:00.000Z",
  reason_for_visit: null,
  notes: null,
  appointment_status: "Scheduled",
  patient_name: "Maria",
  doctor_name: "Dr Lee",
};

describe("calendarEvents", () => {
  it("maps appointment to event", () => {
    const ev = appointmentToEvent(sample);
    expect(ev.title).toContain("Maria");
    expect(ev.start).toBe(sample.scheduled_start);
  });

  it("optimistic move and rollback", () => {
    const events = [appointmentToEvent(sample)];
    const prior = { start: events[0].start, end: events[0].end };
    const moved = applyOptimisticMove(
      events,
      "a1",
      new Date("2026-10-06T03:00:00.000Z"),
      new Date("2026-10-06T03:30:00.000Z"),
    );
    expect(moved[0].start).toBe("2026-10-06T03:00:00.000Z");
    const rolled = rollbackOptimisticMove(moved, "a1", prior);
    expect(rolled[0].start).toBe(prior.start);
  });
});
