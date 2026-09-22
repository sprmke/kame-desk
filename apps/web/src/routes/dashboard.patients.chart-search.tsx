import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/patients/chart-search")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/patients" });
  },
});
