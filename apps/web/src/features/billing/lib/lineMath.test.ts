import { describe, expect, it } from "vitest";
import { lineAmount, sumLines } from "./lineMath";

describe("lineMath", () => {
  it("multiplies quantity and unit price", () => {
    expect(lineAmount("2", "150.50")).toBe("301.00");
  });

  it("sums line rows", () => {
    expect(
      sumLines([
        { quantity: "1", unit_price: "500" },
        { quantity: "2", unit_price: "100.25" },
      ]),
    ).toBe("700.50");
  });
});
