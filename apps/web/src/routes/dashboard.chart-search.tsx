import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/chart-search")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/patients/chart-search" });
  },
});
