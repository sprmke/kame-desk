import { describe, expect, it } from "vitest";
import { hasConflicts, mergeConflictFlags } from "./conflictCheck";

describe("conflictCheck", () => {
  it("detects conflicts", () => {
    expect(hasConflicts([])).toBe(false);
    expect(
      hasConflicts([
        { type: "allergy", drug_name: "Amoxicillin", message: "Allergy" },
      ]),
    ).toBe(true);
  });

  it("merges without duplicates", () => {
    const merged = mergeConflictFlags(
      [{ type: "allergy", drug_name: "A", message: "m1" }],
      [{ type: "allergy", drug_name: "A", message: "m1" }],
    );
    expect(merged).toHaveLength(1);
  });
});
