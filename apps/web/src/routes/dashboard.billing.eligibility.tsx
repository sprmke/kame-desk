import { createFileRoute } from "@tanstack/react-router";
import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { billingHub } from "@/components/layout/nav-config";
import { EligibilityChecksPage } from "@/features/billing/pages/EligibilityChecksPage";

export const Route = createFileRoute("/dashboard/billing/eligibility")({
  component: EligibilityChecksRoute,
});

function EligibilityChecksRoute() {
  return (
    <SectionHubShell hub={billingHub}>
      <EligibilityChecksPage />
    </SectionHubShell>
  );
}
