import { describe, expect, it } from "vitest";
import { conflictFlagKey } from "./flagKey";

describe("conflictFlagKey", () => {
  it("builds a stable key", () => {
    const key = conflictFlagKey({
      type: "allergy",
      drug_name: "Amoxicillin",
      message: "Allergy",
      related: "Penicillin",
    });
    expect(key).toBe("allergy:Amoxicillin:Allergy:Penicillin");
  });
});
