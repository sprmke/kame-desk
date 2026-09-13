import { createFileRoute } from "@tanstack/react-router";
import { ServicesSettingsPage } from "@/features/settings/services/pages/ServicesSettingsPage";

export const Route = createFileRoute("/dashboard/settings/services")({
  component: ServicesSettingsPage,
});
