import { createFileRoute } from "@tanstack/react-router";
import { PublicReminderPage } from "@/features/reminders/pages/PublicReminderPage";

export const Route = createFileRoute("/reminders/$token")({
  component: ReminderRoute,
});

function ReminderRoute() {
  const { token } = Route.useParams();
  return <PublicReminderPage token={token} />;
}
