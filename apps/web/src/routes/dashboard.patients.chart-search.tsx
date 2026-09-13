import { createFileRoute } from "@tanstack/react-router";
import { PatientsHubShell } from "@/components/layout/PatientsHubShell";
import { RequirePermission } from "@/components/layout/RequirePermission";
import { ChartSearchPage } from "@/features/chart-search/pages/ChartSearchPage";

export const Route = createFileRoute("/dashboard/patients/chart-search")({
  component: PatientChartSearchRoute,
});

function PatientChartSearchRoute() {
  return (
    <RequirePermission permission="patients:chart_search">
      <PatientsHubShell>
        <ChartSearchPage />
      </PatientsHubShell>
    </RequirePermission>
  );
}
