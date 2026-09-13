import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/audit-log")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/insights/audit-log" });
  },
});
