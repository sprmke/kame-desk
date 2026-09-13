import { createFileRoute } from "@tanstack/react-router";
import { TeamSettingsPage } from "@/features/settings/team/pages/TeamSettingsPage";

export const Route = createFileRoute("/dashboard/settings/team")({
  component: TeamSettingsPage,
});
