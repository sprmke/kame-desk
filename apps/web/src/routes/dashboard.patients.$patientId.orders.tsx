import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/patients/$patientId/orders")({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: "/dashboard/patients/$patientId/records",
      params,
    });
  },
});
