import { createFileRoute } from "@tanstack/react-router";
import { PayersSettingsPage } from "@/features/settings/payers/pages/PayersSettingsPage";

export const Route = createFileRoute("/dashboard/settings/payers")({
  component: PayersSettingsPage,
});
