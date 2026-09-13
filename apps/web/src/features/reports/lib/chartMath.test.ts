import { describe, expect, it } from "vitest";

export function maxSeriesValue(
  series: Array<Record<string, string | number | null>>,
  key: string,
): number {
  if (!series.length) return 0;
  return Math.max(...series.map((row) => Number(row[key] ?? 0)));
}

describe("maxSeriesValue", () => {
  it("returns zero for empty series", () => {
    expect(maxSeriesValue([], "booked")).toBe(0);
  });

  it("returns the largest numeric value", () => {
    expect(
      maxSeriesValue([{ booked: 2 }, { booked: 5 }, { booked: 1 }], "booked"),
    ).toBe(5);
  });
});
