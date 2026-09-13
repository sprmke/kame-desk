import { describe, expect, it } from "vitest";

export function activityLogQueryKey(
  clinicId: string,
  filters: Record<string, string | number | undefined>,
) {
  return ["activity-log", clinicId, ...Object.values(filters).filter(Boolean)];
}

describe("activityLogQueryKey", () => {
  it("includes clinic and filter values", () => {
    expect(
      activityLogQueryKey("clinic-1", { page: 1, target_type: "patient" }),
    ).toEqual(["activity-log", "clinic-1", 1, "patient"]);
  });
});
