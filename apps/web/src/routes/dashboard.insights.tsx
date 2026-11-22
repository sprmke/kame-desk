import { createFileRoute } from "@tanstack/react-router";
import { SectionHubLayout } from "@/components/layout/SectionHubLayout";
import { insightsHub } from "@/components/layout/nav-config";

export const Route = createFileRoute("/dashboard/insights")({
  component: InsightsLayoutRoute,
});

function InsightsLayoutRoute() {
  return <SectionHubLayout hub={insightsHub} permission="insights:view" />;
}
