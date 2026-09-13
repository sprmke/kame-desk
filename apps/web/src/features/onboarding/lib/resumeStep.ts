import type { OnboardingStatus } from "@/lib/apiClient";

export function resumeOnboardingStep(
  status: OnboardingStatus | undefined,
): string {
  return status?.current_step ?? "clinic";
}
