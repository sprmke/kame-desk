import { describe, expect, it } from "vitest";
import {
  computeWaitStats,
  doctorsFromQueue,
  filterByDoctor,
  sortArrivedByLongestWait,
} from "./waitTime";
import type { WaitingRoomItem } from "./waitingRoom";

function item(
  overrides: Partial<WaitingRoomItem> & Pick<WaitingRoomItem, "id">,
): WaitingRoomItem {
  return {
    patient_id: "p1",
    doctor_id: "d1",
    doctor_name: "Dr. Santos",
    scheduled_start: "2026-09-13T01:00:00.000Z",
    scheduled_end: "2026-09-13T01:30:00.000Z",
    appointment_status: "Confirmed",
    current_visit_status: "Arrived",
    ...overrides,
  };
}

describe("computeWaitStats", () => {
  it("formats elapsed wait under an hour", () => {
    const now = new Date("2026-09-13T01:14:00.000Z");
    const stats = computeWaitStats("2026-09-13T01:00:00.000Z", now);
    expect(stats.formatted).toBe("14m wait");
    expect(stats.urgency).toBe("normal");
    expect(stats.isEarly).toBe(false);
  });

  it("marks delayed and overdue thresholds", () => {
    const delayed = computeWaitStats(
      "2026-09-13T01:00:00.000Z",
      new Date("2026-09-13T01:20:00.000Z"),
    );
    expect(delayed.urgency).toBe("delayed");

    const overdue = computeWaitStats(
      "2026-09-13T01:00:00.000Z",
      new Date("2026-09-13T01:35:00.000Z"),
    );
    expect(overdue.urgency).toBe("overdue");
    expect(overdue.formatted).toBe("35m wait");
  });

  it("formats early arrivals", () => {
    const stats = computeWaitStats(
      "2026-09-13T01:30:00.000Z",
      new Date("2026-09-13T01:20:00.000Z"),
    );
    expect(stats.formatted).toBe("10m early");
    expect(stats.isEarly).toBe(true);
    expect(stats.urgency).toBe("normal");
  });
});

describe("sortArrivedByLongestWait", () => {
  it("puts longest wait first", () => {
    const now = new Date("2026-09-13T02:00:00.000Z");
    const sorted = sortArrivedByLongestWait(
      [
        item({ id: "a", scheduled_start: "2026-09-13T01:45:00.000Z" }),
        item({ id: "b", scheduled_start: "2026-09-13T01:00:00.000Z" }),
      ],
      now,
    );
    expect(sorted.map((row) => row.id)).toEqual(["b", "a"]);
  });
});

describe("doctor filter helpers", () => {
  it("aggregates doctors with counts", () => {
    const doctors = doctorsFromQueue([
      item({ id: "1", doctor_id: "d1", doctor_name: "Dr. Santos" }),
      item({ id: "2", doctor_id: "d2", doctor_name: "Dr. Cruz" }),
      item({ id: "3", doctor_id: "d1", doctor_name: "Dr. Santos" }),
    ]);
    expect(doctors).toEqual([
      { id: "d2", name: "Dr. Cruz", count: 1 },
      { id: "d1", name: "Dr. Santos", count: 2 },
    ]);
  });

  it("filters by doctor id", () => {
    const rows = [
      item({ id: "1", doctor_id: "d1" }),
      item({ id: "2", doctor_id: "d2" }),
    ];
    expect(filterByDoctor(rows, "all")).toHaveLength(2);
    expect(filterByDoctor(rows, "d2").map((r) => r.id)).toEqual(["2"]);
  });
});
