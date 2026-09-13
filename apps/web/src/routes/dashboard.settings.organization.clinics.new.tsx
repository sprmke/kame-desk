import { createFileRoute } from "@tanstack/react-router";
import { CreateClinicPage } from "@/features/settings/organization/pages/CreateClinicPage";

export const Route = createFileRoute(
  "/dashboard/settings/organization/clinics/new",
)({
  component: CreateClinicPage,
});
