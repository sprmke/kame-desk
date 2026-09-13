import { createFileRoute } from "@tanstack/react-router";
import { SectionHubShell } from "@/components/layout/SectionHubShell";
import { scheduleHub } from "@/components/layout/nav-config";
import { AppointmentCalendarPage } from "@/features/appointments/calendar/pages/AppointmentCalendarPage";

export const Route = createFileRoute("/dashboard/appointments/calendar")({
  component: AppointmentCalendarRoute,
});

function AppointmentCalendarRoute() {
  return (
    <SectionHubShell hub={scheduleHub}>
      <AppointmentCalendarPage />
    </SectionHubShell>
  );
}
