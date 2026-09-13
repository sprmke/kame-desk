import { createFileRoute } from "@tanstack/react-router";
import { SectionHubLayout } from "@/components/layout/SectionHubLayout";
import { insightsHub } from "@/components/layout/nav-config";
import { RequirePermission } from "@/components/layout/RequirePermission";

export const Route = createFileRoute("/dashboard/insights")({
  component: InsightsLayoutRoute,
});

function InsightsLayoutRoute() {
  return (
    <RequirePermission permission="insights:view">
      <SectionHubLayout hub={insightsHub} />
    </RequirePermission>
  );
}
