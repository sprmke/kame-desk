import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/settings/membership-plans")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/settings/services" });
  },
});
