import { createFileRoute } from "@tanstack/react-router";
import { AlertsPage } from "@/features/notifications/pages/AlertsPage";

export const Route = createFileRoute("/dashboard/notifications")({
  component: AlertsPage,
});
