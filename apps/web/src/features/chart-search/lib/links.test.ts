import { describe, expect, it } from "vitest";

function chartSearchLink(appointmentId: string, version: number) {
  return `/dashboard/appointments/${appointmentId}/soap?v=${version}`;
}

describe("chartSearchLink", () => {
  it("points at the real SOAP route", () => {
    expect(chartSearchLink("appt-1", 2)).toBe(
      "/dashboard/appointments/appt-1/soap?v=2",
    );
  });
});
