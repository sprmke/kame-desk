import { createFileRoute } from "@tanstack/react-router";
import { AccountSettingsPage } from "@/features/settings/account/pages/AccountSettingsPage";

export const Route = createFileRoute("/dashboard/settings/account")({
  component: AccountSettingsPage,
});
