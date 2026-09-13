import { createFileRoute } from "@tanstack/react-router";
import { OrganizationSettingsPage } from "@/features/settings/organization/pages/OrganizationSettingsPage";

export const Route = createFileRoute("/dashboard/settings/organization")({
  component: OrganizationSettingsPage,
});
