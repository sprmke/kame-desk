import { createFileRoute } from "@tanstack/react-router";
import { InvoiceDetailPage } from "@/features/billing/pages/InvoiceDetailPage";

export const Route = createFileRoute(
  "/dashboard/patients/$patientId/invoices/$invoiceId",
)({
  component: InvoiceDetailRoute,
});

function InvoiceDetailRoute() {
  const { patientId, invoiceId } = Route.useParams();
  return <InvoiceDetailPage patientId={patientId} invoiceId={invoiceId} />;
}
