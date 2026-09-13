import { describe, expect, it } from "vitest";
import { clinicProfileSchema } from "@/features/onboarding/lib/schemas";
import { resumeOnboardingStep } from "@/features/onboarding/lib/resumeStep";

describe("onboarding schemas", () => {
  it("validates clinic profile", () => {
    const result = clinicProfileSchema.safeParse({
      address: "123 St",
      contact_phone: "123",
      contact_email: "a@b.com",
      license_info: "LIC",
    });
    expect(result.success).toBe(true);
  });
});

describe("onboarding resume", () => {
  it("returns server current step when present", () => {
    expect(
      resumeOnboardingStep({
        all_complete: false,
        current_step: "hours",
        steps: [],
      }),
    ).toBe("hours");
  });

  it("defaults to clinic when status missing", () => {
    expect(resumeOnboardingStep(undefined)).toBe("clinic");
  });
});
