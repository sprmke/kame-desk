import { createFileRoute } from "@tanstack/react-router";
import { RequirePermission } from "@/components/layout/RequirePermission";
import { ClinicSettingsPage } from "@/features/settings/clinic/pages/ClinicSettingsPage";

export const Route = createFileRoute("/dashboard/settings/clinic/details")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <RequirePermission permission="settings:clinic">
      <ClinicSettingsPage view="details" />
    </RequirePermission>
  );
}
