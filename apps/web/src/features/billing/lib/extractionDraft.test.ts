import { describe, expect, it } from "vitest";
import {
  confidenceClass,
  extractionToLineItem,
  type BillingExtractionDraft,
} from "./extractionDraft";

const draft: BillingExtractionDraft = {
  attempt_id: "a1",
  fields: {
    amount: { value: "1250.00", confidence: "high" },
    date: { value: "2026-09-01", confidence: "high" },
    provider: { value: "St. Luke's", confidence: "high" },
    reference_number: { value: "OR-421", confidence: "low" },
  },
};

describe("extractionDraft", () => {
  it("maps extraction to a line item", () => {
    const line = extractionToLineItem(draft);
    expect(line.unit_price).toBe("1250.00");
    expect(line.description).toContain("St. Luke's");
    expect(line.description).toContain("OR-421");
  });

  it("styles confidence levels", () => {
    expect(confidenceClass("high")).toContain("success");
    expect(confidenceClass("low")).toContain("warning");
    expect(confidenceClass("missing")).toContain("border");
  });
});
