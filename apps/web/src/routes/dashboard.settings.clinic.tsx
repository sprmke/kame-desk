import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/settings/clinic")({
  component: ClinicSettingsLayout,
});

function ClinicSettingsLayout() {
  return <Outlet />;
}
