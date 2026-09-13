import { describe, expect, it } from "vitest";
import {
  findConflictingAppointment,
  manilaSlotToUtc,
  rangesOverlap,
} from "./conflictCheck";
import type { Appointment } from "@/lib/apiClient";

describe("rangesOverlap", () => {
  it("detects overlapping ranges", () => {
    const a0 = new Date("2026-10-06T02:00:00Z");
    const a1 = new Date("2026-10-06T02:30:00Z");
    const b0 = new Date("2026-10-06T02:15:00Z");
    const b1 = new Date("2026-10-06T02:45:00Z");
    expect(rangesOverlap(a0, a1, b0, b1)).toBe(true);
  });

  it("allows back-to-back slots", () => {
    const a0 = new Date("2026-10-06T02:00:00Z");
    const a1 = new Date("2026-10-06T02:30:00Z");
    const b0 = new Date("2026-10-06T02:30:00Z");
    const b1 = new Date("2026-10-06T03:00:00Z");
    expect(rangesOverlap(a0, a1, b0, b1)).toBe(false);
  });
});

describe("findConflictingAppointment", () => {
  const base: Appointment = {
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
  };

  it("flags overlap for same doctor", () => {
    const conflict = findConflictingAppointment(
      [base],
      "d1",
      new Date("2026-10-06T02:10:00Z"),
      new Date("2026-10-06T02:40:00Z"),
    );
    expect(conflict?.id).toBe("a1");
  });

  it("ignores cancelled appointments", () => {
    const conflict = findConflictingAppointment(
      [{ ...base, appointment_status: "Cancelled" }],
      "d1",
      new Date("2026-10-06T02:10:00Z"),
      new Date("2026-10-06T02:40:00Z"),
    );
    expect(conflict).toBeUndefined();
  });
});

describe("manilaSlotToUtc", () => {
  it("converts Manila wall time to UTC", () => {
    const { scheduled_start, scheduled_end } = manilaSlotToUtc(
      "2026-10-06",
      "10:00",
      30,
    );
    expect(scheduled_start).toBe("2026-10-06T02:00:00.000Z");
    expect(scheduled_end).toBe("2026-10-06T02:30:00.000Z");
  });
});
