import { createFileRoute } from "@tanstack/react-router";
import { RequirePermission } from "@/components/layout/RequirePermission";
import { ReportsPage } from "@/features/reports/pages/ReportsPage";

export const Route = createFileRoute("/dashboard/insights/reports")({
  component: InsightsReportsRoute,
});

function InsightsReportsRoute() {
  return (
    <RequirePermission permission="reports:view">
      <ReportsPage />
    </RequirePermission>
  );
}
