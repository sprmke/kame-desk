import { describe, expect, it } from "vitest";
import { filterIcd10, soapFormSchema } from "./schemas";

describe("soapFormSchema", () => {
  it("accepts minimal SOAP payload", () => {
    const parsed = soapFormSchema.parse({
      subjective: "Headache",
      specialty_template_key: "general",
    });
    expect(parsed.subjective).toBe("Headache");
  });
});

describe("filterIcd10", () => {
  it("matches code prefix", () => {
    const hits = filterIcd10("J06");
    expect(hits.some((h) => h.code === "J06.9")).toBe(true);
  });

  it("matches label text", () => {
    const hits = filterIcd10("asthma");
    expect(hits.some((h) => h.code === "J45.909")).toBe(true);
  });
});
