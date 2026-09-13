import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/documents/")({
  beforeLoad: () => {
    throw redirect({ to: "/dashboard/documents/generate" });
  },
});
