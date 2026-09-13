import { createFileRoute } from "@tanstack/react-router";
import { DoctorProfilePage } from "@/features/settings/doctor/pages/DoctorProfilePage";

export const Route = createFileRoute("/dashboard/settings/doctor")({
  component: DoctorProfilePage,
});
