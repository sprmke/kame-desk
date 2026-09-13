import { createFileRoute } from "@tanstack/react-router";
import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { billingHub } from "@/components/layout/nav-config";
import { LoaRequestsPage } from "@/features/billing/pages/LoaRequestsPage";

export const Route = createFileRoute("/dashboard/billing/loa")({
  component: LoaRequestsRoute,
});

function LoaRequestsRoute() {
  return (
    <SectionHubShell hub={billingHub}>
      <LoaRequestsPage />
    </SectionHubShell>
  );
}
