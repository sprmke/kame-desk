import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/outreach/recalls")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/outreach/reminders" });
  },
});
