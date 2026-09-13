import { createFileRoute } from "@tanstack/react-router";
import { PrescriptionNewPage } from "@/features/prescriptions/pages/PrescriptionNewPage";

type Search = { template?: string };

export const Route = createFileRoute(
  "/dashboard/patients/$patientId/prescriptions/new",
)({
  validateSearch: (search: Record<string, unknown>): Search => ({
    template: typeof search.template === "string" ? search.template : undefined,
  }),
  component: PrescriptionNewRoute,
});

function PrescriptionNewRoute() {
  const { patientId } = Route.useParams();
  const { template } = Route.useSearch();
  let templateItems;
  if (template) {
    try {
      templateItems = JSON.parse(template) as unknown;
    } catch {
      templateItems = undefined;
    }
  }
  return (
    <PrescriptionNewPage
      patientId={patientId}
      templateItems={Array.isArray(templateItems) ? templateItems : undefined}
    />
  );
}
