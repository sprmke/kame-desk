import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/reports")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/insights/reports" });
  },
});
