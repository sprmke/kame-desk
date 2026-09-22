import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/settings/organization")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/settings/plan" });
  },
});
