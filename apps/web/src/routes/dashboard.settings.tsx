import { createFileRoute } from "@tanstack/react-router";
import { SettingsLayout } from "@/components/layout/SettingsLayout";

export const Route = createFileRoute("/dashboard/settings")({
  component: SettingsLayoutRoute,
});

function SettingsLayoutRoute() {
  return <SettingsLayout />;
}
