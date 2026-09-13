import { createFileRoute } from "@tanstack/react-router";
import { SoapNotePage } from "@/features/soap/pages/SoapNotePage";

export const Route = createFileRoute(
  "/dashboard/appointments/$appointmentId/soap",
)({
  component: SoapRoute,
});

function SoapRoute() {
  const { appointmentId } = Route.useParams();
  return <SoapNotePage appointmentId={appointmentId} />;
}
