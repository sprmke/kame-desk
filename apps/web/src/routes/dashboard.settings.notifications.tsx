import { createFileRoute } from "@tanstack/react-router";
import { NotificationsSettingsPage } from "@/features/settings/notifications/pages/NotificationsSettingsPage";

export const Route = createFileRoute("/dashboard/settings/notifications")({
  component: NotificationsSettingsPage,
});
