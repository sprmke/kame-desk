import { createFileRoute } from "@tanstack/react-router";
import { InvoiceNewPage } from "@/features/billing/pages/InvoiceNewPage";

type Search = { appointmentId?: string };

export const Route = createFileRoute(
  "/dashboard/patients/$patientId/invoices/new",
)({
  validateSearch: (search: Record<string, unknown>): Search => ({
    appointmentId:
      typeof search.appointmentId === "string"
        ? search.appointmentId
        : undefined,
  }),
  component: InvoiceNewRoute,
});

function InvoiceNewRoute() {
  const { patientId } = Route.useParams();
  const { appointmentId } = Route.useSearch();
  return <InvoiceNewPage patientId={patientId} appointmentId={appointmentId} />;
}
