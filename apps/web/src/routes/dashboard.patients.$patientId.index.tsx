import { createFileRoute } from "@tanstack/react-router";
import { PatientDetailPage } from "@/features/patients/pages/PatientDetailPage";

export const Route = createFileRoute("/dashboard/patients/$patientId/")({
  component: PatientDetailRoute,
});

function PatientDetailRoute() {
  const { patientId } = Route.useParams();
  return <PatientDetailPage patientId={patientId} />;
}
