import { createFileRoute } from "@tanstack/react-router";
import { SettingsLayout } from "@/components/layout/SettingsLayout";
import { RequirePermission } from "@/components/layout/RequirePermission";

export const Route = createFileRoute("/dashboard/settings")({
  component: SettingsLayoutRoute,
});

function SettingsLayoutRoute() {
  return (
    <RequirePermission
      permission={[
        "settings:account",
        "settings:doctor",
        "settings:clinic",
        "settings:team",
        "settings:services",
        "settings:notifications",
        "settings:assistant",
        "settings:templates",
        "settings:plan",
      ]}
    >
      <SettingsLayout />
    </RequirePermission>
  );
}
