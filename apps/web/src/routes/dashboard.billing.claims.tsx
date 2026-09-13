import { createFileRoute } from "@tanstack/react-router";
import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { billingHub } from "@/components/layout/nav-config";
import { ClaimsListPage } from "@/features/billing/pages/ClaimsPage";

export const Route = createFileRoute("/dashboard/billing/claims")({
  component: ClaimsListRoute,
});

function ClaimsListRoute() {
  return (
    <SectionHubShell hub={billingHub}>
      <ClaimsListPage />
    </SectionHubShell>
  );
}
