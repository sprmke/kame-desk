import { describe, expect, it } from "vitest";
import { rruleFromPreset } from "./rrulePresets";

describe("rrulePresets", () => {
  it("builds weekly preset", () => {
    expect(rruleFromPreset("weekly", 4)).toBe("FREQ=WEEKLY;COUNT=4");
  });

  it("builds biweekly preset", () => {
    expect(rruleFromPreset("biweekly", 6)).toBe(
      "FREQ=WEEKLY;INTERVAL=2;COUNT=6",
    );
  });
});
