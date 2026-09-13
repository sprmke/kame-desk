import { createFileRoute } from "@tanstack/react-router";
import { AppointmentNewPage } from "@/features/appointments/pages/AppointmentNewPage";

type Search = { patientId?: string };

export const Route = createFileRoute("/dashboard/appointments/new")({
  validateSearch: (search: Record<string, unknown>): Search => ({
    patientId:
      typeof search.patientId === "string" ? search.patientId : undefined,
  }),
  component: AppointmentNewRoute,
});

function AppointmentNewRoute() {
  const { patientId } = Route.useSearch();
  return <AppointmentNewPage prefillPatientId={patientId} />;
}
