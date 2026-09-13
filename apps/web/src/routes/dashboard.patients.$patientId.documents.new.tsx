import { createFileRoute } from "@tanstack/react-router";
import { DocumentNewPage } from "@/features/documents/pages/DocumentNewPage";

export const Route = createFileRoute(
  "/dashboard/patients/$patientId/documents/new",
)({
  component: DocumentNewRoute,
});

function DocumentNewRoute() {
  const { patientId } = Route.useParams();
  return <DocumentNewPage patientId={patientId} />;
}
