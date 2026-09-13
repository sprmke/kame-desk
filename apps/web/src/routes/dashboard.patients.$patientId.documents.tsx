import { createFileRoute } from "@tanstack/react-router";
import { PatientDetailPage } from "@/features/patients/pages/PatientDetailPage";

export const Route = createFileRoute(
  "/dashboard/patients/$patientId/documents",
)({
  component: RouteComponent,
});

function RouteComponent() {
  const { patientId } = Route.useParams();
  return <PatientDetailPage patientId={patientId} section="documents" />;
}
