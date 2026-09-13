import { describe, expect, it } from "vitest";
import { sanitize_grounding_facts } from "./groundingFacts";

describe("groundingFacts", () => {
  it("strips patient fields", () => {
    const facts = sanitize_grounding_facts({
      clinic_name: "Demo Clinic",
      patient_name: "Maria Santos",
      nested: { contact_number: "0917", ok: true },
    });
    expect(facts).toEqual({
      clinic_name: "Demo Clinic",
      nested: { ok: true },
    });
  });
});
