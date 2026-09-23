import { describe, expect, it } from "vitest";
import {
  soapTemplateForSpecialtyKey,
  specialtyKeyFromLegacyLabel,
} from "./doctorSpecialties";

describe("doctorSpecialties", () => {
  it("maps dentist to the dental SOAP template", () => {
    expect(soapTemplateForSpecialtyKey("dentist")).toBe("dental");
  });

  it("falls back to general", () => {
    expect(soapTemplateForSpecialtyKey("cardiologist")).toBe("general");
    expect(soapTemplateForSpecialtyKey(null)).toBe("general");
  });

  it("maps display labels back to keys", () => {
    expect(specialtyKeyFromLegacyLabel("OB-GYN")).toBe("obgyn");
    expect(specialtyKeyFromLegacyLabel("Unknown clinic")).toBe("other");
  });
});
