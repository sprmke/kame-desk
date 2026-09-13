import { describe, expect, it } from "vitest";
import { listItemDelay } from "./motion";

describe("listItemDelay", () => {
  it("returns 0 when reduced motion is on", () => {
    expect(listItemDelay(5, true)).toBe(0);
  });

  it("caps delay after 12 items", () => {
    expect(listItemDelay(20, false)).toBe(listItemDelay(12, false));
  });

  it("staggers by index", () => {
    expect(listItemDelay(2, false)).toBeGreaterThan(listItemDelay(1, false));
  });
});
