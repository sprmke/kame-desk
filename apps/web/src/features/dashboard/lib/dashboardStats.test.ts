import { describe, expect, it } from "vitest";
import type { Appointment, WaitingRoomItem } from "@/lib/apiClient";
import {
  addDaysIso,
  dashboardAppointmentWindow,
  firstIsoDayOfMonth,
  lastIsoDayOfMonth,
  manilaDateFromTimestamp,
} from "./dashboardRange";
import {
  activeAppointmentCount,
  appointmentsOnDate,
  completedVisitCount,
  groupUpcomingByDay,
  nextAppointmentId,
  notOnFloor,
  onFloor,
  scheduledWaitingCount,
  waitingNowCount,
} from "./dashboardStats";

function appt(
  overrides: Partial<Appointment> & Pick<Appointment, "id" | "scheduled_start">,
): Appointment {
  return {
    clinic_id: "c1",
    patient_id: "p1",
    doctor_id: "d1",
    room_id: null,
    scheduled_end: overrides.scheduled_start,
    reason_for_visit: null,
    notes: null,
    appointment_status: "Scheduled",
    patient_name: "Ana",
    ...overrides,
  };
}

function wait(
  overrides: Partial<WaitingRoomItem> & Pick<WaitingRoomItem, "id">,
): WaitingRoomItem {
  return {
    patient_id: "p1",
    doctor_id: "d1",
    scheduled_start: "2026-09-12T01:00:00.000Z",
    scheduled_end: "2026-09-12T01:30:00.000Z",
    appointment_status: "Confirmed",
    current_visit_status: null,
    ...overrides,
  };
}

describe("dashboardRange", () => {
  it("computes month bounds from a mid-month date", () => {
    expect(firstIsoDayOfMonth("2026-09-12")).toBe("2026-09-01");
    expect(lastIsoDayOfMonth("2026-09-12")).toBe("2026-09-30");
    expect(addDaysIso("2026-09-12", 1)).toBe("2026-09-13");
  });

  it("extends the window into the next month near month-end", () => {
    const window = dashboardAppointmentWindow("2026-09-28");
    expect(window.from_date).toBe("2026-09-01");
    expect(window.to_date).toBe("2026-10-04");
  });

  it("maps a UTC timestamp to a Manila calendar date", () => {
    expect(manilaDateFromTimestamp("2026-09-11T16:30:00.000Z")).toBe(
      "2026-09-12",
    );
  });
});

describe("dashboardStats", () => {
  const todayItems = [
    appt({
      id: "a1",
      scheduled_start: "2026-09-12T01:00:00.000Z",
      appointment_status: "Confirmed",
    }),
    appt({
      id: "a2",
      scheduled_start: "2026-09-12T03:00:00.000Z",
      appointment_status: "Cancelled",
    }),
    appt({
      id: "a3",
      scheduled_start: "2026-09-13T02:00:00.000Z",
    }),
  ];

  it("counts active appointments on a Manila date", () => {
    const today = appointmentsOnDate(todayItems, "2026-09-12");
    expect(today).toHaveLength(2);
    expect(activeAppointmentCount(today)).toBe(1);
  });

  it("counts waiting-room columns", () => {
    const items = [
      wait({ id: "w1", current_visit_status: null }),
      wait({ id: "w2", current_visit_status: "Arrived" }),
      wait({ id: "w3", current_visit_status: "In Consultation" }),
      wait({ id: "w4", current_visit_status: "Completed" }),
    ];
    expect(waitingNowCount(items)).toBe(2);
    expect(scheduledWaitingCount(items)).toBe(1);
    expect(completedVisitCount(items)).toBe(1);
  });

  it("picks the next uncompleted appointment at or after now", () => {
    const items = appointmentsOnDate(todayItems, "2026-09-12");
    expect(nextAppointmentId(items, new Date("2026-09-12T02:00:00.000Z"))).toBe(
      "a1",
    );
  });

  it("treats only arrived and in-consult as on the floor", () => {
    expect(onFloor(wait({ id: "w1", current_visit_status: null }))).toBe(false);
    expect(onFloor(wait({ id: "w2", current_visit_status: "Arrived" }))).toBe(
      true,
    );
  });

  it("excludes floor visits from the Today schedule list", () => {
    const items = [
      appt({
        id: "a1",
        scheduled_start: "2026-09-12T01:00:00.000Z",
        current_visit_status: "Arrived",
      }),
      appt({
        id: "a2",
        scheduled_start: "2026-09-12T03:00:00.000Z",
        current_visit_status: null,
      }),
    ];
    expect(items.filter(notOnFloor).map((item) => item.id)).toEqual(["a2"]);
  });

  it("groups upcoming days after today", () => {
    const groups = groupUpcomingByDay(todayItems, "2026-09-12", "2026-09-18");
    expect(groups).toHaveLength(1);
    expect(groups[0]?.date).toBe("2026-09-13");
    expect(groups[0]?.items).toHaveLength(1);
  });
});
