import { createFileRoute } from "@tanstack/react-router";
import { ReminderDashboardPage } from "@/features/reminders/pages/ReminderDashboardPage";

export const Route = createFileRoute("/dashboard/outreach/reminders")({
  component: ReminderDashboardPage,
});
