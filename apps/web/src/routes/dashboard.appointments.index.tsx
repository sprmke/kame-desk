import { createFileRoute } from "@tanstack/react-router";
import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { scheduleHub } from "@/components/layout/nav-config";
import { AppointmentListPage } from "@/features/appointments/pages/AppointmentListPage";

export const Route = createFileRoute("/dashboard/appointments/")({
  component: AppointmentListRoute,
});

function AppointmentListRoute() {
  return (
    <SectionHubShell hub={scheduleHub}>
      <AppointmentListPage />
    </SectionHubShell>
  );
}
