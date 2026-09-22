import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/dashboard/settings/organization/clinics/new",
)({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/settings/plan" });
  },
});
