import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/settings/clinic/")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/settings/clinic/details" });
  },
});
