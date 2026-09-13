import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/recalls")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/outreach/recalls" });
  },
});
