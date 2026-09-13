import { createFileRoute } from "@tanstack/react-router";
import { PatientsHubShell } from "@/components/layout/PatientsHubShell";
import { PatientListPage } from "@/features/patients/pages/PatientListPage";

export const Route = createFileRoute("/dashboard/patients/")({
  component: PatientListRoute,
});

function PatientListRoute() {
  return (
    <PatientsHubShell>
      <PatientListPage />
    </PatientsHubShell>
  );
}
