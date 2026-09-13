import { describe, expect, it } from "vitest";
import { patientFormSchema } from "./schemas";

describe("patientFormSchema", () => {
  it("requires full name", () => {
    const result = patientFormSchema.safeParse({ full_name: "" });
    expect(result.success).toBe(false);
  });

  it("requires data processing consent", () => {
    const result = patientFormSchema.safeParse({ full_name: "Maria Santos" });
    expect(result.success).toBe(false);
  });

  it("accepts minimal valid patient", () => {
    const result = patientFormSchema.safeParse({
      full_name: "Maria Santos",
      data_processing_consent: true,
    });
    expect(result.success).toBe(true);
  });
});
